#!/usr/bin/env python3
"""
Complete test suite for CRM Analytics Pipeline
Run with: python -m pytest tests/ -v
Or: python tests/run_all_tests.py
"""

import sys
import os
import subprocess
import unittest
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_pytest():
    """Run pytest with coverage"""
    print("=" * 80)
    print("RUNNING CRM ANALYTICS TESTS")
    print("=" * 80)
    print(f"Started at: {datetime.now()}")
    print()
    
    # Run pytest with coverage
    result = subprocess.run([
        "pytest", "tests/",
        "-v",
        "--tb=short",
        "--strict-markers",
        "--disable-warnings",
        "--cov=scripts",
        "--cov-report=term",
        "--cov-report=html",
        "--cov-report=xml"
    ])
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_pytest())