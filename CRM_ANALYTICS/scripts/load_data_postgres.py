import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import os
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_data():

    logger.info("Loading data to PostgreSQL...")

    # PostgreSQL connection
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="crm_staging",
        user="staging_user",
        password="staging_password"
    )

    cur = conn.cursor()

    # CSV -> PostgreSQL tables
    tables = {
        'deals': 'deals_raw',
        'activities': 'activities_raw',
        'stages': 'stages_raw',
        'pipeline': 'pipeline_raw',
        'organizations': 'organizations_raw'
    }

    # Extraction metadata
    metadata_path = 'data/extraction_metadata.json'

    metadata = {}

    if os.path.exists(metadata_path):

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        logger.info(
            f"Loading data extracted at: {metadata.get('extracted_at')}"
        )

        logger.info(
            f"Source: {metadata.get('source_file')}"
        )

    total_rows = 0

    # Process each CSV
    for key, table in tables.items():

        file_path = f'data/{key}.csv'

        if not os.path.exists(file_path):

            logger.warning(f"File not found: {file_path}")

            continue

        logger.info(
            f"  Loading {file_path} -> staging.{table}"
        )

        # Read CSV
        df = pd.read_csv(file_path)

        # Normalize column names
        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace(' ', '_', regex=False)
            .str.replace('(', '', regex=False)
            .str.replace(')', '', regex=False)
            .str.replace('/', '_', regex=False)
            .str.replace('-', '_', regex=False)
        )

        # Auto detect datetime columns
        for col in df.columns:

            if 'date' in col.lower() or 'time' in col.lower():

                df[col] = pd.to_datetime(
                    df[col],
                    errors='coerce'
                )

        # Replace NaN / NaT with None
        df = df.astype(object).where(pd.notnull(df), None)

        # Add ingestion metadata
        df['ingested_at'] = datetime.now()

        # Clear table
        cur.execute(f"TRUNCATE TABLE staging.{table}")

        # Prepare insert
        tuples = [tuple(x) for x in df.to_numpy()]

        cols = ','.join(df.columns)

        query = f"""
            INSERT INTO staging.{table} ({cols})
            VALUES %s
        """

        # Bulk insert
        execute_values(cur, query, tuples)

        conn.commit()

        logger.info(f">> Loaded {len(df)} rows")

        total_rows += len(df)

    # Create monitoring table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS monitoring.load_history (
            id SERIAL PRIMARY KEY,
            load_time TIMESTAMP,
            source_file VARCHAR(500),
            total_rows INTEGER,
            tables_loaded JSON
        )
    """)

    # Insert load history
    cur.execute("""
        INSERT INTO monitoring.load_history (
            load_time,
            source_file,
            total_rows,
            tables_loaded
        )
        VALUES (%s, %s, %s, %s)
    """, (
        datetime.now(),
        metadata.get('source_file', 'Unknown'),
        total_rows,
        json.dumps(tables)
    ))

    conn.commit()

    cur.close()
    conn.close()

    logger.info(
        f">>>> Data loading complete! Total rows: {total_rows}"
    )

if __name__ == "__main__":
    load_data()