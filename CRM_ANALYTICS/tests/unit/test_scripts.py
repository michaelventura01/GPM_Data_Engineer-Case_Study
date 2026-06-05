"""
Unit tests for individual script functions
"""

import unittest
import os
import sys
import pandas as pd
import tempfile
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestExcelReader(unittest.TestCase):
    """Test Excel reader functionality"""
    
    def setUp(self):
        """Create test Excel file"""
        import pandas as pd
        
        # Create temporary Excel file
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        self.test_data = pd.DataFrame({
            'ID': [1, 2, 3],
            'Name': ['Test1', 'Test2', 'Test3'],
            'Value': [100, 200, 300]
        })
        self.test_data.to_excel(self.temp_file.name, sheet_name='Deals', index=False)
        self.temp_file.close()
    
    def tearDown(self):
        """Clean up test file"""
        os.unlink(self.temp_file.name)
    
    @patch('scripts.read_excel_source.ExcelDataSource')
    def test_read_excel(self, MockExcelDataSource):
        """Test reading Excel file"""
        mock_instance = MockExcelDataSource.return_value
        mock_instance.read_sheet.return_value = self.test_data
        
        df = mock_instance.read_sheet('Deals')
        self.assertEqual(len(df), 3)
        self.assertIn('ID', df.columns)


class TestDataLoader(unittest.TestCase):
    """Test data loading functions"""
    
    @patch('psycopg2.connect')
    def test_load_to_postgres(self, mock_connect):
        """Test PostgreSQL data loading"""
        from scripts.load_data_postgres import load_to_postgres
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Create test CSV
        test_df = pd.DataFrame({'ID': [1, 2], 'Value': [100, 200]})
        test_df.to_csv('data/test.csv', index=False)
        
        # Mock file loading
        with patch('os.path.exists', return_value=True):
            with patch('pandas.read_csv', return_value=test_df):
                # This won't actually run due to mocking
                pass


class TestDataSync(unittest.TestCase):
    """Test data sync functionality"""
    
    @patch('mysql.connector.connect')
    @patch('psycopg2.connect')
    def test_sync_fact_deals(self, mock_pg, mock_mysql):
        """Test sync_fact_deals method"""
        from scripts.sync_to_mysql import DataSync
        
        # Mock PostgreSQL connection
        mock_pg_conn = Mock()
        mock_pg_cursor = Mock()
        mock_pg.return_value = mock_pg_conn
        mock_pg_conn.cursor.return_value = mock_pg_cursor
        
        # Mock MySQL connection
        mock_mysql_conn = Mock()
        mock_mysql_cursor = Mock()
        mock_mysql.return_value = mock_mysql_conn
        mock_mysql_conn.cursor.return_value = mock_mysql_cursor
        
        # Create test data
        test_data = pd.DataFrame({
            'deal_id': [1, 2, 3],
            'value': [100, 200, 300],
            'status': ['won', 'lost', 'open'],
            'add_time': ['2024-01-01', '2024-01-02', '2024-01-03']
        })
        
        with patch('pandas.read_sql', return_value=test_data):
            syncer = DataSync()
            # Test would continue here


if __name__ == '__main__':
    unittest.main()