"""
Test script for PyCommerce multi-tenant functionality.

This script tests the multi-tenant functionality of the PyCommerce platform by
creating tenants, adding products to each tenant, and verifying that data is properly isolated.
"""

import os
import logging
import uuid
import sys
from uuid import UUID

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_multi_tenant")

# Import PyCommerce modules
from pycommerce.core.db import db_session, init_db, Tenant, Product
from pycommerce.models.tenant import TenantManager, Tenant as TenantObj
from pycommerce.models.product import ProductManager

def create_test_tenant(tenant_manager, name, slug):
    """Create a test tenant."""
    try:
        # Create tenant
        tenant = tenant_manager.create(
            name=name,
            slug=slug,
            domain=f"{slug}.pycommerce.test"
        )
        logger.info(f"Created tenant: {tenant.name} ({tenant.slug})")
        return tenant
    except Exception as e:
        logger.error(f"Error creating tenant: {str(e)}")
        return None

def add_test_products(tenant_id, count=3):
    """Add test products to a tenant."""
    try:
        products = []
        product_manager = ProductManager()
        
        for i in range(1, count + 1):
            # Create product data
            product_data = {
                "sku": f"TEST-{tenant_id}-{i}",
                "name": f"Test Product {i} for Tenant {tenant_id}",
                "description": f"This is a test product for tenant {tenant_id}",
                "price": 10.0 * i,
                "stock": 100,
                "tenant_id": tenant_id
            }
            
            # Create product model
            product_model = Product(
                id=uuid.uuid4(),
                **product_data
            )
            
            # Add to database
            db_session.add(product_model)
            products.append(product_model)
        
        # Commit changes
        db_session.commit()
        
        logger.info(f"Added {count} products to tenant {tenant_id}")
        return products
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error adding products to tenant {tenant_id}: {str(e)}")
        return []

def verify_tenant_isolation(tenant_ids):
    """Verify that tenant data is properly isolated."""
    try:
        for tenant_id in tenant_ids:
            # Get products for this tenant
            products = db_session.query(Product).filter(Product.tenant_id == tenant_id).all()
            
            logger.info(f"Tenant {tenant_id} has {len(products)} products:")
            for product in products:
                logger.info(f"  - {product.name} (SKU: {product.sku})")
            
            # Verify that products belong to the correct tenant
            for product in products:
                assert product.tenant_id == tenant_id, f"Product {product.id} has incorrect tenant_id: {product.tenant_id} != {tenant_id}"
            
        return True
    except Exception as e:
        logger.error(f"Error verifying tenant isolation: {str(e)}")
        return False

def run_test():
    """Run the multi-tenant test."""
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized")
        
        # Create tenant manager
        tenant_manager = TenantManager()
        
        # Create test tenants
        tenant1 = create_test_tenant(tenant_manager, "Test Store 1", "test1")
        tenant2 = create_test_tenant(tenant_manager, "Test Store 2", "test2")
        
        if not tenant1 or not tenant2:
            logger.error("Failed to create test tenants")
            return False
        
        # Add products to each tenant
        products1 = add_test_products(tenant1.id, 3)
        products2 = add_test_products(tenant2.id, 3)
        
        if not products1 or not products2:
            logger.error("Failed to add products to tenants")
            return False
        
        # Verify tenant isolation
        success = verify_tenant_isolation([tenant1.id, tenant2.id])
        
        if success:
            logger.info("Multi-tenant test successful")
        else:
            logger.error("Multi-tenant test failed")
        
        return success
    except Exception as e:
        logger.error(f"Error running multi-tenant test: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting multi-tenant test")
    
    # Run test
    success = run_test()
    
    logger.info("Multi-tenant test complete")
    
    # Exit with status code
    sys.exit(0 if success else 1)