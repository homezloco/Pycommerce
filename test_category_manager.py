"""
Test script for CategoryManager.

This script tests the CategoryManager class and its ability to handle database operations
with or without a Flask application context.
"""
import logging
import os
import sys
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('category_test')

# Add the current directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the app and models
from app import app, db
from models import Product, Tenant, Category, ProductCategory
from pycommerce.models.category import CategoryManager

def test_category_manager_for_tenant(tenant_slug):
    """
    Test the CategoryManager for a specific tenant.
    
    Args:
        tenant_slug: The slug of the tenant to test
    """
    start_time = datetime.now()
    logger.info(f"Starting category manager test for tenant {tenant_slug} at {start_time}")
    
    # Create a category manager
    try:
        category_manager = CategoryManager()
        logger.info("CategoryManager created successfully")
    except Exception as e:
        logger.error(f"Error creating CategoryManager: {e}")
        return False
    
    # Find the tenant by slug
    tenant = Tenant.query.filter_by(slug=tenant_slug).first()
    if not tenant:
        logger.error(f"Tenant with slug '{tenant_slug}' not found")
        return False
    
    logger.info(f"Testing with tenant: {tenant.name} ({tenant.id})")
    
    # Get all categories for the tenant
    categories = category_manager.get_all_categories(tenant.id)
    logger.info(f"Found {len(categories)} categories for tenant {tenant.name}")
    
    # List a few categories
    if categories:
        logger.info("Sample categories:")
        for category in categories[:5]:
            logger.info(f"- {category.name} (id: {category.id})")
    
    # Test category tree
    category_tree = category_manager.get_category_tree(tenant.id)
    logger.info(f"Category tree has {len(category_tree)} root categories")
    
    # Sample a product that should have categories
    product = Product.query.filter_by(tenant_id=tenant.id).first()
    if product:
        logger.info(f"Sample product: {product.name} (id: {product.id})")
        if hasattr(product, 'categories') and product.categories:
            logger.info(f"Product has {len(product.categories)} categories (JSON field): {product.categories}")
    
    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"Category manager test completed in {duration}")
    
    return True

if __name__ == "__main__":
    with app.app_context():
        # Test with a known tenant (tech store from the sample data)
        logger.info("Running category manager test")
        success = test_category_manager_for_tenant('tech')
        if success:
            logger.info("Test completed successfully")
        else:
            logger.error("Test failed")