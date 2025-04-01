"""
Pre-start script for PyCommerce platform.

This script is executed before the application server starts to initialize
the database and create a default tenant if needed.
"""

import os
import logging
import uuid
from pycommerce.core.db import init_db, db_session, Tenant
from pycommerce.core.migrations import init_migrations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prestart")

def setup_database():
    """Initialize the database and migrations."""
    try:
        # Initialize database schema
        init_db()
        logger.info("Database initialized")
        
        # Initialize migrations
        try:
            init_migrations()
            logger.info("Migrations initialized")
        except Exception as e:
            logger.warning(f"Error initializing migrations: {str(e)}")
        
        # Create a default tenant if none exists
        try:
            # Check if any tenants exist
            tenant_count = db_session.query(Tenant).count()
            
            if tenant_count == 0:
                logger.info("No tenants found, creating default tenant")
                
                # Create default tenant
                default_tenant = Tenant(
                    id=uuid.uuid4(),
                    name="Default Store",
                    slug="default",
                    domain=os.environ.get("PRIMARY_DOMAIN", "pycommerce.replit.app"),
                    active=True
                )
                
                db_session.add(default_tenant)
                db_session.commit()
                
                logger.info(f"Created default tenant: {default_tenant.name} ({default_tenant.slug})")
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error creating default tenant: {str(e)}")
        
        return True
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Running pre-start initialization")
    
    # Setup database
    if not setup_database():
        logger.error("Failed to set up database")
        exit(1)
    
    logger.info("Pre-start initialization complete")