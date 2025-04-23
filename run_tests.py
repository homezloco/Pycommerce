#!/usr/bin/env python3
"""
Test runner for PyCommerce.

This script discovers and runs all tests in the project.
"""

import unittest
import sys
import os

def run_tests():
    """Discover and run all tests."""
    # Get the directory containing the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add the current directory to the path
    sys.path.insert(0, script_dir)
    
    # Discover all tests
    loader = unittest.TestLoader()
    suite = loader.discover(script_dir, pattern='test_*.py')
    
    # Create a test runner and run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return 0 if all tests passed, 1 otherwise
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())