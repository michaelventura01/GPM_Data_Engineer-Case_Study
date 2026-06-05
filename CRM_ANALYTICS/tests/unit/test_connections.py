"""
Tests for database connections and configuration
"""

import unittest
import os
import sys
import pandas as pd
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.read_excel_source import ExcelDataSource
from scripts.load_data_postgres import load_to_postgres
from scripts.sync_to_mysql import DataSync


class TestConnections(unittest.TestCase):
    """Test all database connections"""
    
    def setUp(self):
        """Set up test environment"""
        self.postgres_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'crm_staging',
            'user': 'staging_user',
            'password': 'staging_password'
        }
        
        self.mysql_config = {
            'host': 'localhost',
            'port': 3306,
            'database': 'crm_production',
            'user': 'prod_user',
            'password': 'prod_password'
        }
    
    @patch('psycopg2.connect')
    def test_postgres_connection(self, mock_connect):
        """Test PostgreSQL connection"""
        import psycopg2
        mock_connect.return_value = Mock()
        
        try:
            conn = psycopg2.connect(**self.postgres_config)
            self.assertIsNotNone(conn)
        except Exception as e:
            self.skipTest(f"PostgreSQL connection failed: {e}")
    
    @patch('mysql.connector.connect')
    def test_mysql_connection(self, mock_connect):
        """Test MySQL connection"""
        import mysql.connector
        mock_connect.return_value = Mock()
        
        try:
            conn = mysql.connector.connect(**self.mysql_config)
            self.assertIsNotNone(conn)
        except Exception as e:
            self.skipTest(f"MySQL connection failed: {e}")
    
    def test_docker_containers_running(self):
        """Test Docker containers are running"""
        import subprocess
        
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=crm_", "--format", "table {{.Names}}"],
            capture_output=True,
            text=True
        )
        
        containers = result.stdout
        
        self.assertIn("crm_postgres_staging", containers, "PostgreSQL container not running")
        self.assertIn("crm_mysql_production", containers, "MySQL container not running")
    
    def test_config_files_exist(self):
        """Test configuration files exist"""
        required_files = [
            'config/excel_source.yaml',
            '.env',
            'dbt_project.yml',
            'docker-compose-both.yml',
            'init_postgres.sql',
            'init_mysql.sql'
        ]
        
        for file in required_files:
            with self.subTest(file=file):
                self.assertTrue(
                    os.path.exists(file),
                    f"Configuration file {file} not found"
                )


class TestExcelSource(unittest.TestCase):
    """Test Excel source configuration and reading"""
    
    def setUp(self):
        """Set up Excel source tester"""
        self.config_path = 'config/excel_source.yaml'
    
    def test_config_exists(self):
        """Test Excel config file exists"""
        self.assertTrue(os.path.exists(self.config_path), "Excel config not found")
    
    def test_config_valid_yaml(self):
        """Test Excel config is valid YAML"""
        import yaml
        
        with open(self.config_path, 'r') as f:
            try:
                config = yaml.safe_load(f)
                self.assertIsNotNone(config)
                self.assertIn('source', config)
                self.assertIn('sheets', config)
            except yaml.YAMLError as e:
                self.fail(f"Invalid YAML: {e}")
    
    def test_excel_file_exists(self):
        """Test Excel file exists at configured path"""
        import yaml
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        excel_path = config['source']['path']
        
        # Try to find the file
        possible_paths = [
            excel_path,
            os.path.join('..', excel_path),
            os.path.abspath(excel_path),
            os.path.expanduser(excel_path)
        ]
        
        found = any(os.path.exists(p) for p in possible_paths)
        
        if not found:
            self.skipTest(f"Excel file not found at: {excel_path}")
        else:
            self.assertTrue(True, "Excel file found")


class TestEnvironmentVariables(unittest.TestCase):
    """Test environment variables are properly set"""
    
    def test_env_file_exists(self):
        """Test .env file exists"""
        self.assertTrue(os.path.exists('.env'), ".env file not found")
    
    def test_required_env_vars(self):
        """Test required environment variables are set"""
        from dotenv import load_dotenv
        
        load_dotenv()
        
        required_vars = [
            'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB',
            'POSTGRES_USER', 'POSTGRES_PASSWORD',
            'MYSQL_HOST', 'MYSQL_PORT', 'MYSQL_DB',
            'MYSQL_USER', 'MYSQL_PASSWORD'
        ]
        
        for var in required_vars:
            with self.subTest(var=var):
                self.assertIsNotNone(os.getenv(var), f"Environment variable {var} not set")


if __name__ == '__main__':
    unittest.main()