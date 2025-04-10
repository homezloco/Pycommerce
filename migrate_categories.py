"""
Migration script to transfer existing categories from JSON field to proper category relationships.

This script will:
1. Create Category records for all unique category names in products
2. Create ProductCategory associations between products and their categories
3. Preserve the existing JSON categories field for backward compatibility
"""
import logging
import os
import sys
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('category_migration')

# Add the current directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the app and models
from app import app, db
from models import Product, Tenant, Category, ProductCategory
from pycommerce.models.category import CategoryManager

def migrate_tenant_categories(tenant_slug):
    """
    Migrate categories from JSON to proper relationships for a specific tenant.
    
    Args:
        tenant_slug: The slug of the tenant to migrate
    
    Returns:
        True if successful, False otherwise
    """
    start_time = datetime.now()
    logger.info(f"Starting category migration for tenant {tenant_slug} at {start_time}")
    
    # Create a category manager
    try:
        category_manager = CategoryManager()
    except Exception as e:
        logger.error(f"Error creating CategoryManager: {e}")
        return False
    
    # Find the tenant
    tenant = Tenant.query.filter_by(slug=tenant_slug).first()
    if not tenant:
        logger.error(f"Tenant with slug '{tenant_slug}' not found")
        return False
    
    logger.info(f"Processing tenant: {tenant.name} ({tenant.id})")
    
    try:
        # Migrate categories for this tenant
        stats = category_manager.migrate_from_json_categories(tenant.id)
        
        logger.info(f"Tenant {tenant.name}: {stats['products_processed']} products processed, "
                    f"{stats['categories_created']} categories created, "
                    f"{stats['associations_created']} associations created, "
                    f"{stats['errors']} errors")
    except Exception as e:
        logger.error(f"Error processing tenant {tenant.name}: {e}")
        return False
    
    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"Category migration for tenant {tenant_slug} completed in {duration}")
    
    return True

def migrate_categories():
    """
    Migrate categories from JSON to proper relationships for all tenants.
    """
    start_time = datetime.now()
    logger.info(f"Starting category migration at {start_time}")
    
    # Create a category manager
    try:
        category_manager = CategoryManager()
    except Exception as e:
        logger.error(f"Error creating CategoryManager: {e}")
        return False
    
    # Get all tenants
    tenants = Tenant.query.all()
    logger.info(f"Found {len(tenants)} tenants")
    
    total_stats = {
        "tenants_processed": 0,
        "products_processed": 0,
        "categories_created": 0,
        "associations_created": 0,
        "errors": 0
    }
    
    # Process each tenant
    for tenant in tenants:
        logger.info(f"Processing tenant: {tenant.name} ({tenant.id})")
        
        try:
            # Migrate categories for this tenant
            stats = category_manager.migrate_from_json_categories(tenant.id)
            
            # Update total stats
            total_stats["tenants_processed"] += 1
            total_stats["products_processed"] += stats["products_processed"]
            total_stats["categories_created"] += stats["categories_created"]
            total_stats["associations_created"] += stats["associations_created"]
            total_stats["errors"] += stats["errors"]
            
            logger.info(f"Tenant {tenant.name}: {stats['products_processed']} products processed, "
                        f"{stats['categories_created']} categories created, "
                        f"{stats['associations_created']} associations created, "
                        f"{stats['errors']} errors")
        except Exception as e:
            logger.error(f"Error processing tenant {tenant.name}: {e}")
            total_stats["errors"] += 1
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info(f"Category migration completed in {duration}")
    logger.info(f"Final stats: {total_stats}")
    
    return True

if __name__ == "__main__":
    with app.app_context():
        logger.info("Running category migration")
        success = migrate_categories()
        if success:
            logger.info("Migration completed successfully")
        else:
            logger.error("Migration failed")