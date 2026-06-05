"""
Data quality tests for the pipeline
"""

import unittest
import pandas as pd
import psycopg2
import mysql.connector
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestDataQuality(unittest.TestCase):
    """Test data quality in both databases"""
    
    @classmethod
    def setUpClass(cls):
        """Set up database connections"""
        try:
            # PostgreSQL connection
            cls.pg_conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="crm_staging",
                user="staging_user",
                password="staging_password"
            )
            cls.pg_cursor = cls.pg_conn.cursor()
            
            # MySQL connection
            cls.mysql_conn = mysql.connector.connect(
                host="localhost",
                port=3306,
                database="crm_production",
                user="prod_user",
                password="prod_password"
            )
            cls.mysql_cursor = cls.mysql_conn.cursor()
            
        except Exception as e:
            cls.skipTest(f"Database connection failed: {e}")
    
    @classmethod
    def tearDownClass(cls):
        """Close database connections"""
        if hasattr(cls, 'pg_cursor'):
            cls.pg_cursor.close()
            cls.pg_conn.close()
        if hasattr(cls, 'mysql_cursor'):
            cls.mysql_cursor.close()
            cls.mysql_conn.close()
    
    def test_postgres_has_data(self):
        """Test PostgreSQL staging has data"""
        self.pg_cursor.execute("SELECT COUNT(*) FROM staging.deals_raw")
        count = self.pg_cursor.fetchone()[0]
        
        self.assertGreater(count, 0, "No data in PostgreSQL staging")
        print(f"  PostgreSQL has {count} deals")
    
    def test_mysql_has_data(self):
        """Test MySQL production has data"""
        self.mysql_cursor.execute("SELECT COUNT(*) FROM fact_deals")
        count = self.mysql_cursor.fetchone()[0]
        
        self.assertGreater(count, 0, "No data in MySQL production")
        print(f"  MySQL has {count} deals")
    
    def test_no_null_deal_ids(self):
        """Test no NULL deal IDs in MySQL"""
        self.mysql_cursor.execute("SELECT COUNT(*) FROM fact_deals WHERE deal_id IS NULL")
        count = self.mysql_cursor.fetchone()[0]
        
        self.assertEqual(count, 0, f"Found {count} rows with NULL deal_id")
    
    def test_valid_status_values(self):
        """Test only valid status values"""
        valid_statuses = ['won', 'lost', 'open']
        
        self.mysql_cursor.execute(
            "SELECT DISTINCT status FROM fact_deals WHERE status NOT IN (%s, %s, %s)",
            valid_statuses
        )
        invalid = self.mysql_cursor.fetchall()
        
        self.assertEqual(len(invalid), 0, f"Found invalid statuses: {invalid}")
    
    def test_positive_values_only(self):
        """Test no negative values (excluding 0 which is valid for leads)"""
        self.mysql_cursor.execute("SELECT COUNT(*) FROM fact_deals WHERE value < 0")
        count = self.mysql_cursor.fetchone()[0]
        
        self.assertEqual(count, 0, f"Found {count} deals with negative values")
    
    def test_days_to_close_positive_or_null(self):
        """Test days_to_close is positive or NULL"""
        self.mysql_cursor.execute(
            "SELECT COUNT(*) FROM fact_deals WHERE days_to_close IS NOT NULL AND days_to_close < 0"
        )
        count = self.mysql_cursor.fetchone()[0]
        
        self.assertEqual(count, 0, f"Found {count} deals with negative days_to_close")
    
    def test_activity_count_not_negative(self):
        """Test activity count is not negative"""
        self.mysql_cursor.execute("SELECT COUNT(*) FROM fact_deals WHERE total_activities < 0")
        count = self.mysql_cursor.fetchone()[0]
        
        self.assertEqual(count, 0, f"Found {count} deals with negative activity count")
    
    def test_win_rate_logic(self):
        """Test win rate logic (is_won and status consistent)"""
        self.mysql_cursor.execute(
            "SELECT COUNT(*) FROM fact_deals WHERE (status='won' AND is_won=0) OR (status='lost' AND is_won=1)"
        )
        count = self.mysql_cursor.fetchone()[0]
        
        self.assertEqual(count, 0, f"Found {count} deals with inconsistent win status")


class TestDataConsistency(unittest.TestCase):
    """Test data consistency between PostgreSQL and MySQL"""
    
    @classmethod
    def setUpClass(cls):
        """Set up database connections"""
        try:
            cls.pg_conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="crm_staging",
                user="staging_user",
                password="staging_password"
            )
            cls.pg_cursor = cls.pg_conn.cursor()
            
            cls.mysql_conn = mysql.connector.connect(
                host="localhost",
                port=3306,
                database="crm_production",
                user="prod_user",
                password="prod_password"
            )
            cls.mysql_cursor = cls.mysql_conn.cursor()
            
        except Exception as e:
            cls.skipTest(f"Database connection failed: {e}")
    
    @classmethod
    def tearDownClass(cls):
        """Close database connections"""
        cls.pg_cursor.close()
        cls.pg_conn.close()
        cls.mysql_cursor.close()
        cls.mysql_conn.close()
    
    def test_row_count_match(self):
        """Test row counts match between source and destination"""
        self.pg_cursor.execute("SELECT COUNT(*) FROM staging.deals_raw WHERE Is_deleted = FALSE")
        pg_count = self.pg_cursor.fetchone()[0]
        
        self.mysql_cursor.execute("SELECT COUNT(*) FROM fact_deals")
        mysql_count = self.mysql_cursor.fetchone()[0]
        
        # Allow some difference due to transformation rules
        difference = abs(pg_count - mysql_count)
        self.assertLessEqual(difference, pg_count * 0.05, 
                            f"Row count mismatch: PG={pg_count}, MySQL={mysql_count}")
    
    def test_value_distribution(self):
        """Test value distribution is reasonable"""
        self.mysql_cursor.execute("""
            SELECT 
                MIN(value) as min_val,
                MAX(value) as max_val,
                AVG(value) as avg_val,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY value) as median_val
            FROM fact_deals
        """)
        
        result = self.mysql_cursor.fetchone()
        min_val, max_val, avg_val, median_val = result
        
        self.assertGreaterEqual(min_val, 0, "Minimum value should be >= 0")
        self.assertGreater(avg_val, 0, "Average value should be > 0")
        print(f"  Value stats: min=${min_val:,.2f}, max=${max_val:,.2f}, avg=${avg_val:,.2f}")


if __name__ == '__main__':
    unittest.main()