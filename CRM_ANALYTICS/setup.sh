#!/bin/bash

echo "========================================="
echo "CRM Analytics Pipeline Setup"
echo "========================================="

# Check if Excel file exists
EXCEL_PATH="../Source/CRM Data Set - Case Study.xlsx"
if [ ! -f "$EXCEL_PATH" ]; then
    echo " Excel file not found at: $EXCEL_PATH"
    echo "Please update the path in config/excel_source.yaml"
    exit 1
fi

echo ">> Excel file found"

# Create virtual environment
echo "📦 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install pandas openpyxl psycopg2-binary mysql-connector-python sqlalchemy pyyaml watchdog

# Create directories
mkdir -p data logs config backups dbt/models

# Discover Excel sheets
echo " Discovering Excel sheets..."
python scripts/discover_excel_sheets.py

# Start Docker containers
echo " Starting Docker containers..."
docker-compose -f docker-compose-both.yml up -d

# Wait for databases
echo " Waiting for databases to be ready..."
sleep 15

# Run initial pipeline
echo " Running initial pipeline..."
python run_pipeline.py

echo ""
echo "========================================="
echo ">>>> Setup complete!"
echo "========================================="
echo ""
echo "To run pipeline manually: python run_pipeline.py"
echo "To watch for Excel changes: python scripts/watch_excel.py"
echo "To access Adminer: http://localhost:8080"
echo ""