#!/usr/bin/env python3
import pandas as pd
from sqlalchemy import create_engine

# Test PostgreSQL connection
pg_engine = create_engine('postgresql://staging_user:staging_password@localhost:5432/crm_staging')

print("Testing PostgreSQL connection...")
try:
    # List tables
    tables = pd.read_sql("SELECT tablename FROM pg_tables WHERE schemaname = 'staging'", pg_engine)
    print(f"Tables in staging schema: {tables['tablename'].tolist()}")
    
    # Check deals table
    df = pd.read_sql("SELECT * FROM staging.deals_raw LIMIT 5", pg_engine)
    print(f"\nDeals table columns: {list(df.columns)}")
    print(f"Sample data:\n{df}")
    
    print(f"\nTotal deals: {len(pd.read_sql('SELECT * FROM staging.deals_raw', pg_engine))}")
    
except Exception as e:
    print(f"Error: {e}")

# Test MySQL connection
from sqlalchemy import create_engine
mysql_engine = create_engine('mysql+mysqlconnector://prod_user:prod_password@localhost:3306/crm_production')

print("\nTesting MySQL connection...")
try:
    tables = pd.read_sql("SHOW TABLES", mysql_engine)
    print(f"Tables in MySQL: {tables.values.flatten().tolist()}")
except Exception as e:
    print(f"Error: {e}")

print("\n >>>> Connection test complete")