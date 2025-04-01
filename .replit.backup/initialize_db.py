"""
Database initialization script for PyCommerce.

This script creates the database schema and initializes
the migrations system for the PyCommerce platform.
"""

import os
import sys
import logging
import argparse
from pycommerce.core.migrations import init_migrations, upgrade_database
from pycommerce.core.db import init_db, get_db, Tenant, Product
from uuid import uuid4

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pycommerce.initialize_db")


def initialize_database():
    """Initialize the database and migrations."""
    try:
        # Initialize migrations
        init_migrations()
        
        # Initialize database schema
        init_db()
        
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False


def create_sample_tenant(name, slug, domain=None):
    """
    Create a sample tenant with products.
    
    Args:
        name: The tenant name
        slug: The tenant slug
        domain: Optional domain for the tenant
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Create tenant
        tenant = Tenant(
            id=uuid4(),
            name=name,
            slug=slug,
            domain=domain,
            active=True
        )
        db.add(tenant)
        db.commit()
        
        # Create products
        products = [
            {
                "sku": "TSHIRT-RED-M",
                "name": "Red T-Shirt (M)",
                "description": "A comfortable red t-shirt made of 100% cotton.",
                "price": 19.99,
                "stock": 100,
                "categories": "clothing,t-shirts"
            },
            {
                "sku": "TSHIRT-BLUE-M",
                "name": "Blue T-Shirt (M)",
                "description": "A comfortable blue t-shirt made of 100% cotton.",
                "price": 19.99,
                "stock": 80,
                "categories": "clothing,t-shirts"
            },
            {
                "sku": "HOODIE-BLACK-L",
                "name": "Black Hoodie (L)",
                "description": "A warm black hoodie perfect for cold days.",
                "price": 39.99,
                "stock": 50,
                "categories": "clothing,hoodies"
            },
            {
                "sku": "JEANS-BLUE-32",
                "name": "Blue Jeans (32)",
                "description": "Classic blue jeans with a comfortable fit.",
                "price": 49.99,
                "stock": 30,
                "categories": "clothing,jeans"
            },
            {
                "sku": "SNEAKERS-WHITE-9",
                "name": "White Sneakers (Size 9)",
                "description": "Stylish white sneakers for everyday wear.",
                "price": 59.99,
                "stock": 25,
                "categories": "footwear,sneakers"
            }
        ]
        
        for product_data in products:
            product = Product(
                id=uuid4(),
                tenant_id=tenant.id,
                **product_data
            )
            db.add(product)
        
        db.commit()
        
        logger.info(f"Created sample tenant: {name} ({slug})")
        return tenant
    except Exception as e:
        logger.error(f"Error creating sample tenant: {str(e)}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize the PyCommerce database")
    parser.add_argument("--sample", action="store_true", help="Create a sample tenant with products")
    args = parser.parse_args()
    
    # Initialize the database
    if not initialize_database():
        sys.exit(1)
    
    # Create a sample tenant if requested
    if args.sample:
        tenant = create_sample_tenant(
            name="Demo Store",
            slug="demo",
            domain="demo.pycommerce.test"
        )
        
        if not tenant:
            sys.exit(1)
    
    logger.info("Database initialization complete")