#!/usr/bin/env python3
"""
Complete pipeline: Excel → PostgreSQL (Staging) → dbt Transform → MySQL (Production)
"""

import subprocess
import sys
import time
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(cmd, description):
    """Run shell command and log output"""
    logger.info(f" {description}...")
    start = time.time()
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    elapsed = time.time() - start
    
    if result.returncode != 0:
        logger.error(f" Failed: {description}")
        logger.error(f"Error: {result.stderr}")
        return False
    else:
        logger.info(f">>>> {description} completed in {elapsed:.2f}s")
        if result.stdout:
            logger.debug(result.stdout[:500])  # Log first 500 chars
        return True

def check_excel_source():
    """Verify Excel source file exists"""
    excel_path = "../Source/CRM Data Set - Case Study.xlsx"
    
    if os.path.exists(excel_path):
        file_size = os.path.getsize(excel_path) / (1024 * 1024)  # MB
        logger.info(f">> Excel source found: {excel_path} ({file_size:.2f} MB)")
        return True
    else:
        logger.error(f" Excel source not found: {excel_path}")
        logger.info("Please update the path in config/excel_source.yaml")
        return False

def get_excel_metadata():
    """Get metadata from Excel file"""
    excel_path = "../Source/CRM Data Set - Case Study.xlsx"
    if os.path.exists(excel_path):
        mod_time = os.path.getmtime(excel_path)
        mod_date = datetime.fromtimestamp(mod_time)
        logger.info(f"  Last modified: {mod_date}")
        return mod_date
    return None

def main():
    start_time = time.time()
    
    logger.info("=" * 70)
    logger.info("CRM ANALYTICS PIPELINE - Excel Source")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    # Step 0: Check Excel source
    logger.info("\n STEP 0: Validating Excel Source")
    if not check_excel_source():
        sys.exit(1)
    
    excel_modified = get_excel_metadata()
    
    # Step 1: Extract from Excel and convert to CSV
    logger.info("\n STEP 1: Extracting Data from Excel")
    if not run_command("python scripts/read_excel_source.py", "Excel extraction"):
        sys.exit(1)
    
    # Step 2: Load to PostgreSQL staging
    logger.info("\n STEP 2: Loading to PostgreSQL Staging")
    if not run_command("python scripts/load_data_postgres.py", "PostgreSQL load"):
        sys.exit(1)
    
    # Step 3: Run dbt transformations
    logger.info("\n STEP 3: Running dbt Transformations")
    if not run_command("cd dbt && dbt run", "dbt run"):
        sys.exit(1)
    
    # Step 4: Run dbt tests
    logger.info("\n STEP 4: Running Data Tests")
    run_command("cd dbt && dbt test", "dbt tests")  # Don't exit on test failure
    
    # Step 5: Sync to MySQL
    logger.info("\n STEP 5: Syncing to MySQL Production")
    if not run_command("python scripts/sync_to_mysql.py", "MySQL sync"):
        sys.exit(1)
    
    # Step 6: Generate documentation
    logger.info("\n STEP 6: Generating Documentation")
    run_command("cd dbt && dbt docs generate", "Documentation")
    
    # Step 7: Show summary
    elapsed = time.time() - start_time
    
    logger.info("\n" + "=" * 70)
    logger.info(">>>> PIPELINE COMPLETE!")
    logger.info(f"Time taken: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")
    logger.info("=" * 70)
    
    # Show summary statistics
    logger.info("\n QUICK STATISTICS:")
    
    # Get counts from PostgreSQL
    result = subprocess.run(
        """docker exec crm_postgres_staging psql -U staging_user -d crm_staging -t -c "
            SELECT 'Deals: ' || COUNT(*) FROM staging.deals_raw
            UNION ALL
            SELECT 'Activities: ' || COUNT(*) FROM staging.activities_raw
            UNION ALL
            SELECT 'Organizations: ' || COUNT(*) FROM staging.organizations_raw
        "\n""",
        shell=True, capture_output=True, text=True
    )
    if result.stdout:
        logger.info("\n" + result.stdout.strip())
    
    # Get counts from MySQL
    result = subprocess.run(
        """docker exec crm_mysql_production mysql -uprod_user -pprod_password -e "
            SELECT 'MySQL Deals: ' || COUNT(*) FROM crm_production.fact_deals
        "\n""",
        shell=True, capture_output=True, text=True
    )
    if result.stdout:
        logger.info(result.stdout.strip())
    
    # Check if Excel was modified during run
    new_modified = get_excel_metadata()
    if excel_modified and new_modified and new_modified > excel_modified:
        logger.warning("Excel file was modified during pipeline execution!")
    
    logger.info("\n🔗 Useful URLs:")
    logger.info("  - Adminer (DB Management): http://localhost:8080")
    logger.info("  - PostgreSQL: localhost:5432 (staging_user/staging_password)")
    logger.info("  - MySQL: localhost:3306 (prod_user/prod_password)")
    logger.info("  - dbt Docs: cd dbt && dbt docs serve")

if __name__ == "__main__":
    main()