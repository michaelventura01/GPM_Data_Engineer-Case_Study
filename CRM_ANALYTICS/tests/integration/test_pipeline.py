"""
End-to-end pipeline tests
"""

import unittest
import subprocess
import os
import sys
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestPipelineSteps(unittest.TestCase):
    """Test each step of the pipeline"""
    
    def test_excel_extraction(self):
        """Test Excel extraction step"""
        result = subprocess.run(
            ["python", "scripts/read_excel_source.py"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )
        
        # Check if CSV files were created
        csv_files = ['deals.csv', 'activities.csv', 'stages.csv']
        csv_created = all(os.path.exists(f'data/{f}') for f in csv_files)
        
        self.assertTrue(csv_created, "CSV files not created from Excel")
        self.assertEqual(result.returncode, 0, f"Extraction failed: {result.stderr}")
    
    def test_postgres_loading(self):
        """Test PostgreSQL loading step"""
        result = subprocess.run(
            ["python", "scripts/load_data_postgres.py"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )
        
        self.assertEqual(result.returncode, 0, f"PostgreSQL loading failed: {result.stderr}")
    
    def test_dbt_run(self):
        """Test dbt transformations"""
        result = subprocess.run(
            ["dbt", "run"],
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'dbt')
        )
        
        self.assertEqual(result.returncode, 0, f"dbt run failed: {result.stderr}")
    
    def test_mysql_sync(self):
        """Test MySQL sync step"""
        result = subprocess.run(
            ["python", "scripts/sync_to_mysql.py"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )
        
        self.assertEqual(result.returncode, 0, f"MySQL sync failed: {result.stderr}")
    
    def test_complete_pipeline(self):
        """Test complete pipeline run"""
        result = subprocess.run(
            ["python", "run_pipeline.py"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )
        
        self.assertEqual(result.returncode, 0, f"Pipeline failed: {result.stderr}")
        self.assertIn("Pipeline completed successfully", result.stdout)


class TestPerformance(unittest.TestCase):
    """Test pipeline performance"""
    
    def test_pipeline_completion_time(self):
        """Test pipeline completes within reasonable time"""
        import time
        
        start = time.time()
        
        result = subprocess.run(
            ["python", "run_pipeline.py"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )
        
        duration = time.time() - start
        
        # Pipeline should complete within 5 minutes (300 seconds)
        self.assertLess(duration, 300, f"Pipeline took {duration:.2f} seconds (>300)")
        print(f"  Pipeline completed in {duration:.2f} seconds")
    
    def test_dbt_run_time(self):
        """Test dbt transformations within reasonable time"""
        import time
        
        start = time.time()
        
        result = subprocess.run(
            ["dbt", "run"],
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'dbt')
        )
        
        duration = time.time() - start
        
        # dbt should complete within 2 minutes
        self.assertLess(duration, 120, f"dbt run took {duration:.2f} seconds (>120)")
        print(f"  dbt run completed in {duration:.2f} seconds")


if __name__ == '__main__':
    unittest.main()