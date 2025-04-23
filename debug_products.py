#!/usr/bin/env python3
"""
Debug script to check products in the database.
"""
import sys
import logging
import os
from typing import List, Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_products():
    """Debug products in the database."""
    try:
        # Import product manager
        from pycommerce.models.product import ProductManager
        from pycommerce.models.tenant import TenantManager

        # Create instances
        product_manager = ProductManager()
        tenant_manager = TenantManager()

        # Get all tenants
        tenants = tenant_manager.list()
        logger.info(f"Found {len(tenants)} tenants")

        # For each tenant, get products
        for tenant in tenants:
            logger.info(f"Tenant: {tenant.name} (ID: {tenant.id})")
            try:
                # Get products by tenant
                products = product_manager.get_by_tenant(str(tenant.id))
                logger.info(f"  Found {len(products)} products")
                
                # Print first 3 products
                for i, product in enumerate(products[:3]):
                    logger.info(f"  Product {i+1}: ID={product.id}, Name={product.name}, Tenant ID in metadata={product.metadata.get('tenant_id') if hasattr(product, 'metadata') and product.metadata else 'Not found'}")
            except Exception as e:
                logger.error(f"  Error getting products for tenant {tenant.name}: {str(e)}")

        # Try getting all products directly
        try:
            all_products = product_manager.list()
            logger.info(f"Direct product_manager.list() returned {len(all_products)} products")
            
            # Print first 3 products
            for i, product in enumerate(all_products[:3]):
                logger.info(f"  Product {i+1}: ID={product.id}, Name={product.name}")
        except Exception as e:
            logger.error(f"Error listing all products: {str(e)}")

        # Try accessing a specific product ID that's failing
        problem_id = "63d63aca-5b6b-4672-a72b-b1483f036ef6"
        logger.info(f"Attempting to access problem product ID: {problem_id}")
        try:
            product = product_manager.get(problem_id)
            if product:
                logger.info(f"Found product: ID={product.id}, Name={product.name}")
            else:
                logger.warning(f"Product ID {problem_id} returned None")
        except Exception as e:
            logger.error(f"Error getting problem product: {str(e)}")

    except Exception as e:
        logger.error(f"Error during debugging: {str(e)}")

if __name__ == "__main__":
    debug_products()