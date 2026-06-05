#!/usr/bin/env python3
"""
Read data from external Excel file and prepare for loading
"""

import pandas as pd
import yaml
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExcelDataSource:
    def __init__(self, config_path='config/excel_source.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.excel_path = self.config['source']['path']
        self.sheets = self.config['sheets']
        
        # Expand user path if needed
        self.excel_path = os.path.expanduser(self.excel_path)
        
    def validate_excel_file(self):
        """Check if Excel file exists and is accessible"""
        if not os.path.exists(self.excel_path):
            raise FileNotFoundError(f"Excel file not found: {self.excel_path}")
        
        logger.info(f">> Excel file found: {self.excel_path}")
        return True
    
    def read_sheet(self, sheet_name):
        """Read a specific sheet from Excel"""
        try:
            df = pd.read_excel(self.excel_path, sheet_name=sheet_name)
            logger.info(f"  Read {len(df)} rows from sheet '{sheet_name}'")
            return df
        except Exception as e:
            logger.error(f"Error reading sheet '{sheet_name}': {e}")
            return None
    
    def read_all_sheets(self):
        """Read all configured sheets"""
        logger.info(f"Reading data from: {self.excel_path}")
        
        data = {}
        for key, sheet_name in self.sheets.items():
            logger.info(f"Loading sheet: {sheet_name}")
            df = self.read_sheet(sheet_name)
            if df is not None:
                data[key] = df
            else:
                logger.warning(f"Sheet '{sheet_name}' not found, trying alternative names...")
                # Try alternative naming conventions
                alternatives = [sheet_name.lower(), sheet_name.upper(), sheet_name.capitalize()]
                for alt in alternatives:
                    try:
                        df = self.read_sheet(alt)
                        if df is not None:
                            data[key] = df
                            break
                    except:
                        continue
        
        return data
    
    def validate_schema(self, df, expected_columns):
        """Validate that DataFrame has expected columns"""
        missing_cols = set(expected_columns) - set(df.columns)
        if missing_cols:
            logger.warning(f"Missing columns: {missing_cols}")
            return False
        return True
    
    def clean_data(self, df, sheet_type):
        """Clean data based on sheet type"""
        # Convert column names to standard format
        df.columns = df.columns.str.strip().str.replace(' ', '_')
        
        # Handle nulls based on type
        if sheet_type == 'deals':
            df['Value'] = df['Value'].fillna(0)
            df['Lost_reason'] = df['Lost_reason'].fillna('Unknown')
        elif sheet_type == 'activities':
            df['Deal_ID'] = df['Deal_ID'].fillna(0).astype(int)
        
        return df
    
    def save_to_csv(self, data_dict, output_dir='data'):
        """Save all sheets as CSV for staging"""
        os.makedirs(output_dir, exist_ok=True)
        
        for key, df in data_dict.items():
            # Clean data
            df = self.clean_data(df, key)
            
            # Save to CSV
            output_path = os.path.join(output_dir, f'{key}.csv')
            df.to_csv(output_path, index=False)
            logger.info(f">> Saved {len(df)} rows to {output_path}")
        
        # Also save metadata about the extraction
        metadata = {
            'extracted_at': datetime.now().isoformat(),
            'source_file': self.excel_path,
            'sheets_loaded': list(data_dict.keys()),
            'row_counts': {k: len(v) for k, v in data_dict.items()}
        }
        
        import json
        with open(os.path.join(output_dir, 'extraction_metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return data_dict

def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("Reading CRM Data from External Excel File")
    logger.info("=" * 60)
    
    # Initialize reader
    reader = ExcelDataSource()
    
    # Validate file exists
    reader.validate_excel_file()
    
    # Read all sheets
    data = reader.read_all_sheets()
    
    if not data:
        logger.error("No data was read from Excel file")
        return False
    
    # Save as CSV
    reader.save_to_csv(data)
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("EXTRACTION SUMMARY")
    logger.info("=" * 60)
    for key, df in data.items():
        logger.info(f"  {key}: {len(df)} rows, {len(df.columns)} columns")
    
    logger.info("\n>>>> Data extraction complete! CSV files ready for staging.")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)