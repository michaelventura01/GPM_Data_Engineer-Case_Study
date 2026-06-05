#!/usr/bin/env python3
"""
Discover and display all sheets in the Excel file
"""

import pandas as pd
import os

def discover_sheets():
    excel_path = "../Source/CRM Data Set - Case Study.xlsx"
    
    if not os.path.exists(excel_path):
        print(f"Error: Excel file not found at {excel_path}")
        return
    
    print(f"Analyzing Excel file: {excel_path}")
    print("=" * 60)
    
    # Get all sheet names
    xl = pd.ExcelFile(excel_path)
    sheet_names = xl.sheet_names
    
    print(f"\nFound {len(sheet_names)} sheets:\n")
    
    for sheet in sheet_names:
        # Read first few rows to preview
        df = pd.read_excel(excel_path, sheet_name=sheet, nrows=5)
        print(f" Sheet: '{sheet}'")
        print(f"\t Columns: {list(df.columns)}")
        print(f"\t Shape: {df.shape}")
        print(f"\t Preview:\n{df.head(2).to_string()}\n")
        print("-" * 40)
    
    # Generate config suggestion
    print("\n Suggested config/excel_source.yaml:")
    print("source:")
    print("  type: excel")
    print(f"  path: \"{excel_path}\"")
    print("sheets:")
    for sheet in sheet_names:
        # Guess the key name based on sheet name
        key = sheet.lower().replace(' ', '_')
        print(f"  {key}: \"{sheet}\"")
    
    return sheet_names

if __name__ == "__main__":
    discover_sheets()
