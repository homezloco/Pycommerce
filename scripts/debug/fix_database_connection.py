
#!/usr/bin/env python3
"""
Fix database connection issues for the page builder.
This script properly formats the DATABASE_URL environment variable.
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s.%(msecs)03d %(levelname)s %(name)s - %(message)s',
                   datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('db_connection_fixer')

def fix_database_url():
    """Fix the DATABASE_URL environment variable format."""
    # Get current DATABASE_URL
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        # If DATABASE_URL is not set, try REPLIT_DB_URL
        replit_db_url = os.environ.get('REPLIT_DB_URL')
        
        if replit_db_url and replit_db_url.startswith('https://kv.replit.com'):
            logger.info(f"Found Replit KV URL, but we need a PostgreSQL URL")
            logger.info("Using default PostgreSQL connection string")
            postgres_url = "postgresql://postgres:postgres@localhost:5432/pycommerce"
            os.environ['DATABASE_URL'] = postgres_url
            logger.info(f"Set DATABASE_URL to: {postgres_url}")
            return True
        
        # If no DATABASE_URL is set, use default
        logger.info("No DATABASE_URL found, setting default")
        os.environ['DATABASE_URL'] = "postgresql://postgres:postgres@localhost:5432/pycommerce"
        logger.info(f"Set DATABASE_URL to: {os.environ['DATABASE_URL']}")
        return True
        
    # Check if DATABASE_URL is a https URL (Replit KV format)
    if database_url.startswith('https://'):
        logger.warning(f"Found invalid DATABASE_URL format: {database_url}")
        logger.info("Converting to PostgreSQL format")
        
        # Set a proper PostgreSQL URL
        postgres_url = "postgresql://postgres:postgres@localhost:5432/pycommerce"
        os.environ['DATABASE_URL'] = postgres_url
        logger.info(f"Updated DATABASE_URL to: {postgres_url}")
        return True
    
    logger.info(f"DATABASE_URL is properly formatted: {database_url}")
    return False

if __name__ == "__main__":
    logger.info("Starting database connection fixer")
    
    # Fix the DATABASE_URL
    fixed = fix_database_url()
    
    if fixed:
        logger.info("Database URL has been fixed. You can now run the application.")
    else:
        logger.info("No changes needed to DATABASE_URL.")
    
    # Print current environment variables for debugging
    logger.info(f"Current DATABASE_URL: {os.environ.get('DATABASE_URL')}")
    
    # Run debug_page_builder.py with fixed DATABASE_URL if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--run-debug":
        logger.info("Running page builder debug with fixed DATABASE_URL")
        import debug_page_builder
        debug_page_builder.run_debug()
