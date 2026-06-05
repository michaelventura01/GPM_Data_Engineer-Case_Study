#!/usr/bin/env python3
import psycopg2
import mysql.connector

# Connect to PostgreSQL
pg_conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="crm_staging",
    user="staging_user",
    password="staging_password"
)
pg_cursor = pg_conn.cursor()

# Connect to MySQL
mysql_conn = mysql.connector.connect(
    host="localhost",
    port=3306,
    database="crm_production",
    user="prod_user",
    password="prod_password"
)
mysql_cursor = mysql_conn.cursor()

# Clear MySQL table
mysql_cursor.execute("TRUNCATE TABLE fact_deals")

# Get data from PostgreSQL
pg_cursor.execute("""
    SELECT 
        ID, Org_ID, Pipeline_ID, Stage_ID, Title, Value, Currency,
        Status, Lost_reason, Close_time, Add_time, Won_time, Lost_time
    FROM staging.deals_raw 
    WHERE Is_deleted = FALSE
""")

# Insert into MySQL
inserted = 0
for row in pg_cursor.fetchall():
    mysql_cursor.execute("""
        INSERT INTO fact_deals (
            deal_id, org_id, pipeline_id, stage_id, title, value, currency,
            status, lost_reason, close_time, add_time, won_time, lost_time,
            days_to_close, won_value, is_won, is_lost, is_open, total_activities
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL, 0, 0, 0, 0, 0)
    """, row)
    inserted += 1

mysql_conn.commit()
print(f"Synced {inserted} rows to MySQL")

pg_cursor.close()
pg_conn.close()
mysql_cursor.close()
mysql_conn.close()