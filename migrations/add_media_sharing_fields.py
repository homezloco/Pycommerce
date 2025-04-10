#!/usr/bin/env python3
"""
Migration script to add media sharing fields to the media_files table.

This script adds the following columns to the media_files table:
- meta_data (JSONB): To store arbitrary metadata including sharing_level
- is_public (Boolean): Flag to indicate if the media is publicly accessible
- is_ai_generated (Boolean): Flag to indicate if the media was AI-generated
"""

import os
import sys
import logging

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import Table, Column, MetaData, Boolean, Text
from sqlalchemy.dialects.postgresql import JSONB
from pycommerce.core.db import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upgrade():
    """
    Add new columns to the media_files table.
    """
    meta = MetaData()
    meta.reflect(bind=engine)
    
    # Get the media_files table
    if 'media_files' not in meta.tables:
        logger.error("Table media_files not found in database")
        return False
    
    table = meta.tables['media_files']
    
    # Check if columns already exist
    existing_columns = [c.name for c in table.columns]
    
    # Create a connection and begin a transaction
    with engine.begin() as conn:
        # Add meta_data column
        if 'meta_data' not in existing_columns:
            logger.info("Adding meta_data column to media_files table")
            conn.execute(f"ALTER TABLE media_files ADD COLUMN meta_data JSONB")
        else:
            logger.info("meta_data column already exists")
        
        # Add is_public column
        if 'is_public' not in existing_columns:
            logger.info("Adding is_public column to media_files table")
            conn.execute(f"ALTER TABLE media_files ADD COLUMN is_public BOOLEAN DEFAULT FALSE")
        else:
            logger.info("is_public column already exists")
        
        # Add is_ai_generated column
        if 'is_ai_generated' not in existing_columns:
            logger.info("Adding is_ai_generated column to media_files table")
            conn.execute(f"ALTER TABLE media_files ADD COLUMN is_ai_generated BOOLEAN DEFAULT FALSE")
        else:
            logger.info("is_ai_generated column already exists")
        
        # Add url column (derived from file_path)
        if 'url' not in existing_columns:
            logger.info("Adding url column to media_files table")
            conn.execute(f"ALTER TABLE media_files ADD COLUMN url TEXT")
        else:
            logger.info("url column already exists")
        
        # Add thumbnail_url column
        if 'thumbnail_url' not in existing_columns:
            logger.info("Adding thumbnail_url column to media_files table")
            conn.execute(f"ALTER TABLE media_files ADD COLUMN thumbnail_url TEXT")
        else:
            logger.info("thumbnail_url column already exists")
        
        # Add alt_text column
        if 'alt_text' not in existing_columns:
            logger.info("Adding alt_text column to media_files table")
            conn.execute(f"ALTER TABLE media_files ADD COLUMN alt_text TEXT")
        else:
            logger.info("alt_text column already exists")
        
    logger.info("Migration completed successfully")
    return True

def downgrade():
    """
    Remove the columns added in the upgrade.
    """
    meta = MetaData()
    meta.reflect(bind=engine)
    
    # Get the media_files table
    if 'media_files' not in meta.tables:
        logger.error("Table media_files not found in database")
        return False
    
    table = meta.tables['media_files']
    
    # Check if columns exist
    existing_columns = [c.name for c in table.columns]
    
    # Create a connection and begin a transaction
    with engine.begin() as conn:
        # Remove meta_data column
        if 'meta_data' in existing_columns:
            logger.info("Removing meta_data column from media_files table")
            conn.execute(f"ALTER TABLE media_files DROP COLUMN meta_data")
        
        # Remove is_public column
        if 'is_public' in existing_columns:
            logger.info("Removing is_public column from media_files table")
            conn.execute(f"ALTER TABLE media_files DROP COLUMN is_public")
        
        # Remove is_ai_generated column
        if 'is_ai_generated' in existing_columns:
            logger.info("Removing is_ai_generated column from media_files table")
            conn.execute(f"ALTER TABLE media_files DROP COLUMN is_ai_generated")
        
        # Remove url column
        if 'url' in existing_columns:
            logger.info("Removing url column from media_files table")
            conn.execute(f"ALTER TABLE media_files DROP COLUMN url")
        
        # Remove thumbnail_url column
        if 'thumbnail_url' in existing_columns:
            logger.info("Removing thumbnail_url column from media_files table")
            conn.execute(f"ALTER TABLE media_files DROP COLUMN thumbnail_url")
        
        # Remove alt_text column
        if 'alt_text' in existing_columns:
            logger.info("Removing alt_text column from media_files table")
            conn.execute(f"ALTER TABLE media_files DROP COLUMN alt_text")
    
    logger.info("Downgrade completed successfully")
    return True

if __name__ == '__main__':
    # Run the migration
    if len(sys.argv) > 1 and sys.argv[1] == 'downgrade':
        logger.info("Running downgrade...")
        downgrade()
    else:
        logger.info("Running upgrade...")
        upgrade()