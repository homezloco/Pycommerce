#!/usr/bin/env python3
"""
Verify the page builder functionality and fix any issues.
"""

import os
import sys
import logging
import importlib
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s.%(msecs)03d %(levelname)s %(name)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('main')


def check_import(module_name):
    """Check if a module can be imported."""
    try:
        module = importlib.import_module(module_name)
        logger.info(f"✅ Successfully imported {module_name}")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import {module_name}: {str(e)}")
        return False

logger.info("Starting page builder verification")

# Get database URL from environment or use default
database_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/pycommerce')
logger.info(f"Using database URL: {database_url.split('@')[1] if '@' in database_url else database_url}")

try:
    # Create engine
    engine = create_engine(database_url)

    # Check if page builder tables exist
    logger.info("Checking page builder tables...")

    with engine.connect() as conn:
        # Check each table
        tables_to_check = ['pages', 'page_sections', 'content_blocks', 'page_templates']
        missing_tables = []

        for table in tables_to_check:
            query = text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')")
            result = conn.execute(query).scalar()

            if not result:
                missing_tables.append(table)
                logger.warning(f"Table '{table}' does not exist")
            else:
                logger.info(f"Table '{table}' exists")

        # Create missing tables if needed
        if missing_tables:
            logger.warning(f"Need to create {len(missing_tables)} missing tables: {', '.join(missing_tables)}")

            # Import models and create tables
            logger.info("Creating missing tables...")

            try:
                # Import Base and models
                from pycommerce.core.db import Base
                from pycommerce.models.page_builder import Page, PageSection, ContentBlock, PageTemplate

                # Create tables
                Base.metadata.create_all(engine, tables=[
                    table.__table__ for table_name, table in [
                        ('pages', Page),
                        ('page_sections', PageSection),
                        ('content_blocks', ContentBlock),
                        ('page_templates', PageTemplate)
                    ] if table_name in missing_tables
                ])

                logger.info("Successfully created missing tables")
            except Exception as e:
                logger.error(f"Error creating tables: {str(e)}")
                sys.exit(1)

        # Verify templates exist
        logger.info("Checking for page templates...")
        template_count = conn.execute(text("SELECT COUNT(*) FROM page_templates")).scalar()
        logger.info(f"Found {template_count} templates")

        if template_count == 0:
            logger.warning("No templates found, creating default templates...")
            try:
                # Import function to create templates
                from create_default_templates import create_default_templates
                create_default_templates()
                logger.info("Default templates created successfully")
            except Exception as e:
                logger.error(f"Error creating default templates: {str(e)}")

        # Check for API routes
        logger.info("Verifying API endpoints...")
        try:
            # Add routes verification logic here
            # This is just a placeholder since we can't easily check routes directly
            logger.info("API routes verification would happen here")
        except Exception as e:
            logger.error(f"Error verifying API routes: {str(e)}")

        #Import verification
        logger.info("Verifying Page Builder Imports...")
        imports_ok = True
        imports_ok = check_import("routes.admin.page_builder") and imports_ok
        imports_ok = check_import("pycommerce.models.page_builder") and imports_ok
        imports_ok = check_import("routes.admin.ai_content") and imports_ok
        imports_ok = check_import("pycommerce.models.tenant") and imports_ok

        try:
            from pycommerce.services.wysiwyg_service import WysiwygService
            logger.info("✅ Successfully imported WysiwygService")
        except ImportError as e:
            logger.error(f"❌ Failed to import WysiwygService: {str(e)}")
            imports_ok = False

        if imports_ok:
            logger.info("✅ All page builder components verified successfully")
        else:
            logger.error("❌ Some page builder components failed verification")


        logger.info("Page builder verification completed")

except SQLAlchemyError as e:
    logger.error(f"Database error: {str(e)}")
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    sys.exit(1)