#!/usr/bin/env python3
"""
Synchronize data from PostgreSQL staging to MySQL production
Using SQLAlchemy for better compatibility
"""

import mysql.connector
import psycopg2
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataSync:
    def __init__(self):
        # Create SQLAlchemy engines for better compatibility
        self.pg_engine = create_engine(
            'postgresql://staging_user:staging_password@localhost:5432/crm_staging'
        )
        
        self.mysql_engine = create_engine(
            'mysql+mysqlconnector://prod_user:prod_password@localhost:3306/crm_production'
        )
        
        # Also keep direct connections for specific operations
        self.mysql_conn = mysql.connector.connect(
            host="localhost",
            port=3306,
            database="crm_production",
            user="prod_user",
            password="prod_password"
        )
        self.mysql_cursor = self.mysql_conn.cursor()
    
    def sync_fact_deals(self):
        """Sync fact_deals table"""
        logger.info("Syncing fact_deals...")
        
        # Query from PostgreSQL using SQLAlchemy
        query = """
        SELECT 
            d.ID as deal_id,
            d.Org_ID as org_id,
            d.Pipeline_ID as pipeline_id,
            d.Stage_ID as stage_id,
            d.Title,
            d.Value,
            d.Currency,
            d.Status,
            d.Lost_reason,
            d.Close_time,
            d.Add_time,
            d.Won_time,
            d.Lost_time,
            EXTRACT(DAY FROM (d.Close_time - d.Add_time)) as days_to_close,
            CASE WHEN d.Status = 'won' THEN d.Value ELSE 0 END as won_value,
            CASE WHEN d.Status = 'won' THEN 1 ELSE 0 END as is_won,
            CASE WHEN d.Status = 'lost' THEN 1 ELSE 0 END as is_lost,
            CASE WHEN d.Status = 'open' THEN 1 ELSE 0 END as is_open,
            COALESCE(a.activity_count, 0) as total_activities
        FROM staging.deals_raw d
        LEFT JOIN (
            SELECT Deal_ID, COUNT(*) as activity_count
            FROM staging.activities_raw
            GROUP BY Deal_ID
        ) a ON d.ID = a.Deal_ID
        WHERE d.Is_deleted = FALSE OR d.Is_deleted IS NULL
        """
        
        # Use pandas with SQLAlchemy engine
        df = pd.read_sql(query, self.pg_engine)
        logger.info(f"  Retrieved {len(df)} rows from PostgreSQL")
        
        if len(df) == 0:
            logger.warning("  No data to sync!")
            return 0
        
        # Show column names for debugging
        logger.info(f"  Columns: {list(df.columns)}")
        
        # Clear existing data in MySQL
        self.mysql_cursor.execute("TRUNCATE TABLE fact_deals")
        
        # Insert new data using batch insert for better performance
        inserted = 0
        batch_size = 500
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            for _, row in batch.iterrows():
                try:
                    sql = """
                    INSERT INTO fact_deals (
                        deal_id, org_id, pipeline_id, stage_id, title, value, currency,
                        status, lost_reason, close_time, add_time, won_time, lost_time,
                        days_to_close, won_value, is_won, is_lost, is_open, total_activities
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    # Convert NaN to None for MySQL
                    values = (
                        int(row['deal_id']) if pd.notna(row['deal_id']) else None,
                        int(row['org_id']) if pd.notna(row['org_id']) else None,
                        int(row['pipeline_id']) if pd.notna(row['pipeline_id']) else None,
                        int(row['stage_id']) if pd.notna(row['stage_id']) else None,
                        str(row['title']) if pd.notna(row['title']) else None,
                        float(row['value']) if pd.notna(row['value']) else 0,
                        str(row['currency']) if pd.notna(row['currency']) else 'USD',
                        str(row['status']) if pd.notna(row['status']) else None,
                        str(row['lost_reason']) if pd.notna(row['lost_reason']) else None,
                        row['close_time'] if pd.notna(row['close_time']) else None,
                        row['add_time'] if pd.notna(row['add_time']) else None,
                        row['won_time'] if pd.notna(row['won_time']) else None,
                        row['lost_time'] if pd.notna(row['lost_time']) else None,
                        int(row['days_to_close']) if pd.notna(row['days_to_close']) else None,
                        float(row['won_value']) if pd.notna(row['won_value']) else 0,
                        int(row['is_won']) if pd.notna(row['is_won']) else 0,
                        int(row['is_lost']) if pd.notna(row['is_lost']) else 0,
                        int(row['is_open']) if pd.notna(row['is_open']) else 0,
                        int(row['total_activities']) if pd.notna(row['total_activities']) else 0
                    )
                    
                    self.mysql_cursor.execute(sql, values)
                    inserted += 1
                    
                except Exception as e:
                    logger.warning(f"  Error inserting row {row['deal_id']}: {e}")
                    continue
            
            self.mysql_conn.commit()
            logger.info(f"  Inserted {inserted}/{len(df)} rows...")
        
        self.mysql_conn.commit()
        logger.info(f"\t >> Synced {inserted} rows to MySQL fact_deals")
        return inserted
    
    def sync_dimensions(self):
        """Sync dimension tables"""
        logger.info("Syncing dimension tables...")
        
        try:
            # Sync organizations
            org_df = pd.read_sql("SELECT * FROM staging.organizations_raw", self.pg_engine)
            if len(org_df) > 0:
                # Check column names (might be ID or id)
                id_col = 'ID' if 'ID' in org_df.columns else 'id'
                name_col = 'Name' if 'Name' in org_df.columns else 'name'
                
                self.mysql_cursor.execute("TRUNCATE TABLE dim_organization")
                for _, row in org_df.iterrows():
                    self.mysql_cursor.execute(
                        "INSERT INTO dim_organization (org_id, org_name) VALUES (%s, %s)",
                        (row[id_col], row[name_col])
                    )
                logger.info(f"\t >> Synced {len(org_df)} organizations")
            else:
                logger.warning("  No organizations found")
            
            # Sync stages
            stages_df = pd.read_sql("SELECT * FROM staging.stages_raw", self.pg_engine)
            if len(stages_df) > 0:
                id_col = 'ID' if 'ID' in stages_df.columns else 'id'
                name_col = 'Name' if 'Name' in stages_df.columns else 'name'
                order_col = 'Order nr' if 'Order nr' in stages_df.columns else 'order_nr'
                pipeline_col = 'Pipeline ID' if 'Pipeline ID' in stages_df.columns else 'pipeline_id'
                prob_col = 'Deal probability' if 'Deal probability' in stages_df.columns else 'deal_probability'
                days_col = 'Days to rotten' if 'Days to rotten' in stages_df.columns else 'days_to_rotten'
                
                self.mysql_cursor.execute("TRUNCATE TABLE dim_stage")
                for _, row in stages_df.iterrows():
                    self.mysql_cursor.execute("""
                        INSERT INTO dim_stage (stage_id, stage_name, order_nr, pipeline_id, deal_probability, days_to_rotten)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        row[id_col], row[name_col], 
                        row[order_col] if pd.notna(row[order_col]) else 0,
                        row[pipeline_col] if pd.notna(row[pipeline_col]) else 0,
                        row[prob_col] if pd.notna(row[prob_col]) else 0,
                        row[days_col] if pd.notna(row[days_col]) else None
                    ))
                logger.info(f"\t >> Synced {len(stages_df)} stages")
            else:
                logger.warning("  No stages found")
            
            # Sync pipeline
            pipeline_df = pd.read_sql("SELECT * FROM staging.pipeline_raw", self.pg_engine)
            if len(pipeline_df) > 0:
                id_col = 'ID' if 'ID' in pipeline_df.columns else 'id'
                name_col = 'Name' if 'Name' in pipeline_df.columns else 'name'
                
                self.mysql_cursor.execute("TRUNCATE TABLE dim_pipeline")
                for _, row in pipeline_df.iterrows():
                    self.mysql_cursor.execute(
                        "INSERT INTO dim_pipeline (pipeline_id, pipeline_name) VALUES (%s, %s)",
                        (row[id_col], row[name_col])
                    )
                logger.info(f"\t >> Synced {len(pipeline_df)} pipelines")
            else:
                logger.warning("  No pipelines found")
            
            self.mysql_conn.commit()
            
        except Exception as e:
            logger.error(f"Error syncing dimensions: {e}")
            logger.info("  Continuing with fact table sync...")
    
    def generate_kpi_summary(self):
        """Generate KPI summary tables in MySQL"""
        logger.info("Generating KPI summary...")
        
        try:
            self.mysql_cursor.execute("""
                INSERT INTO kpi_daily_summary (summary_date, total_deals, won_deals, lost_deals, revenue_won, win_rate)
                SELECT 
                    DATE(add_time) as summary_date,
                    COUNT(*) as total_deals,
                    SUM(is_won) as won_deals,
                    SUM(is_lost) as lost_deals,
                    SUM(won_value) as revenue_won,
                    ROUND(100.0 * SUM(is_won) / NULLIF(SUM(is_won + is_lost), 0), 2) as win_rate
                FROM fact_deals
                WHERE add_time >= DATE_SUB(NOW(), INTERVAL 90 DAY)
                GROUP BY DATE(add_time)
                ON DUPLICATE KEY UPDATE
                    total_deals = VALUES(total_deals),
                    won_deals = VALUES(won_deals),
                    lost_deals = VALUES(lost_deals),
                    revenue_won = VALUES(revenue_won),
                    win_rate = VALUES(win_rate),
                    updated_at = CURRENT_TIMESTAMP
            """)
            
            self.mysql_conn.commit()
            logger.info("\t >> KPI summary generated")
        except Exception as e:
            logger.warning(f"  KPI summary generation skipped: {e}")
    
    def verify_sync(self):
        """Verify sync was successful"""
        logger.info("\nVerifying sync...")
        
        # Check counts in MySQL
        self.mysql_cursor.execute("SELECT COUNT(*) FROM fact_deals")
        mysql_count = self.mysql_cursor.fetchone()[0]
        
        # Check counts in PostgreSQL
        pg_count = pd.read_sql("SELECT COUNT(*) as count FROM staging.deals_raw WHERE Is_deleted = FALSE", self.pg_engine)
        pg_count = pg_count['count'].iloc[0]
        
        logger.info(f"  PostgreSQL deals: {pg_count}")
        logger.info(f"  MySQL deals: {mysql_count}")
        
        if pg_count == mysql_count:
            logger.info("\t >>>> Sync verified - counts match!")
        else:
            logger.warning(f"\t Count mismatch: PG={pg_count}, MySQL={mysql_count}")
        
        # Show sample data
        self.mysql_cursor.execute("""
            SELECT status, COUNT(*) as count, ROUND(AVG(value), 2) as avg_value
            FROM fact_deals 
            GROUP BY status
        """)
        
        logger.info("\n  Deal status breakdown:")
        for row in self.mysql_cursor.fetchall():
            logger.info(f"    {row[0]}: {row[1]} deals, avg value: ${row[2]:,.2f}")
    
    def run_full_sync(self):
        """Run complete synchronization"""
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info("Starting PostgreSQL to MySQL Sync")
        logger.info(f"Started at: {start_time}")
        logger.info("=" * 60)
        
        try:
            # Sync all tables
            self.sync_dimensions()
            rows_synced = self.sync_fact_deals()
            
            if rows_synced > 0:
                self.generate_kpi_summary()
                self.verify_sync()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("=" * 60)
            logger.info(f">>>> Sync completed in {duration:.2f} seconds")
            logger.info(f"   Rows synced: {rows_synced}")
            logger.info("=" * 60)
            
            return rows_synced > 0
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            import traceback
            traceback.print_exc()
            self.mysql_conn.rollback()
            return False
    
    def close(self):
        """Close database connections"""
        self.mysql_cursor.close()
        self.mysql_conn.close()
        self.pg_engine.dispose()
        self.mysql_engine.dispose()

def main():
    syncer = DataSync()
    try:
        success = syncer.run_full_sync()
        exit(0 if success else 1)
    finally:
        syncer.close()

if __name__ == "__main__":
    main()