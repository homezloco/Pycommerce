"""
Script to assign products to categories.

This script helps fix category assignment for existing products in the database.
It will ensure all products are properly assigned to categories so they display
correctly in the market analysis dashboard.
"""

import logging
import sys
from uuid import uuid4
from typing import Dict, List, Optional, Tuple

# Initialize logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set up path for imports
sys.path.append('.')

# Import app context and database
from app import app, db
from models import Tenant, Product
from pycommerce.core.db import init_db
from managers import ProductManager as AppProductManager
from managers import TenantManager as AppTenantManager
from pycommerce.models.category import CategoryManager
from pycommerce.models.order import OrderManager as PyOrderManager
from pycommerce.models.product import Product


def get_all_products(product_manager: AppProductManager, tenant_id: Optional[str] = None) -> List[Product]:
    """
    Get all products in the system, optionally filtered by tenant.
    
    Args:
        product_manager: The product manager instance
        tenant_id: Optional tenant ID to filter by
        
    Returns:
        List of products
    """
    if tenant_id:
        return product_manager.get_products_by_tenant(tenant_id)
    
    # Get all tenants
    with app.app_context():
        products = []
        tenants = AppTenantManager().get_all_tenants()
        
        for tenant in tenants:
            tenant_products = product_manager.get_products_by_tenant(tenant.id)
            products.extend(tenant_products)
            
        return products


def suggest_category_for_product(product: Product) -> List[str]:
    """
    Suggest appropriate categories for a product based on its attributes.
    
    Args:
        product: The product to suggest categories for
        
    Returns:
        List of suggested category names
    """
    name = product.name.lower() if product.name else ""
    description = product.description.lower() if product.description else ""
    
    # Default to electronics if nothing else matches
    categories = ["Electronics"]
    
    # Check name and description for keywords
    if any(keyword in name or keyword in description for keyword in ["laptop", "macbook", "notebook", "chromebook"]):
        categories = ["Laptops"]
    elif any(keyword in name or keyword in description for keyword in ["phone", "iphone", "android", "smartphone"]):
        categories = ["Phones"]
    elif any(keyword in name or keyword in description for keyword in ["headphone", "speaker", "earbud", "airpod", "audio"]):
        categories = ["Audio"]
    elif any(keyword in name or keyword in description for keyword in ["case", "charger", "cable", "keyboard", "mouse"]):
        categories = ["Accessories"]
    elif any(keyword in name or keyword in description for keyword in ["alexa", "echo", "home pod", "smart home", "smart light"]):
        categories = ["Smart Home"]
    
    # Use product ID suffix as a fallback for some known products
    if product.id:
        id_suffix = product.id[-6:]
        if id_suffix in ['036ef6', '0a00a4']:
            categories = ["Laptops"]
        elif id_suffix in ['60a6eb', '44f144']:
            categories = ["Audio"]
        elif id_suffix in ['174922', 'fa4014']:
            categories = ["Phones"]
        elif id_suffix in ['e69e99', '9e0c47']:
            categories = ["Accessories"]
    
    return categories


def ensure_categories_exist(category_manager: CategoryManager, tenant_id: str) -> Dict[str, str]:
    """
    Ensure that all required categories exist for the tenant.
    
    Args:
        category_manager: The category manager instance
        tenant_id: The tenant ID
        
    Returns:
        Dictionary mapping category names to their IDs
    """
    primary_categories = {
        "Electronics": None,
        "Laptops": None,
        "Phones": None,
        "Audio": None,
        "Accessories": None,
        "Smart Home": None
    }
    
    # Check existing categories
    existing_categories = category_manager.get_all_categories(tenant_id)
    for category in existing_categories:
        if category.name in primary_categories:
            primary_categories[category.name] = category.id
    
    # Create any missing categories
    for category_name, category_id in primary_categories.items():
        if category_id is None:
            try:
                category = category_manager.create_category(
                    tenant_id=tenant_id,
                    name=category_name,
                    slug=category_name.lower().replace(' ', '-')
                )
                primary_categories[category_name] = category.id
                logger.info(f"Created category {category_name}")
            except Exception as e:
                logger.error(f"Error creating category {category_name}: {e}")
    
    return {name: id for name, id in primary_categories.items() if id is not None}


def assign_products_to_categories(
    product_manager: AppProductManager,
    category_manager: CategoryManager,
    tenant_manager: AppTenantManager
) -> int:
    """
    Assign products to appropriate categories.
    
    Args:
        product_manager: The product manager instance
        category_manager: The category manager instance
        tenant_manager: The tenant manager instance
        
    Returns:
        Number of product-category assignments made
    """
    assignment_count = 0
    
    # Get all tenants
    tenants = tenant_manager.get_all_tenants()
    
    for tenant in tenants:
        tenant_id = tenant.id
        logger.info(f"Processing tenant: {tenant.name} ({tenant.slug})")
        
        # Get category mapping for this tenant
        category_map = ensure_categories_exist(category_manager, tenant_id)
        
        # Get all products for this tenant
        products = product_manager.get_products_by_tenant(tenant_id)
        logger.info(f"Found {len(products)} products for tenant {tenant.slug}")
        
        # Process each product
        for product in products:
            # Check existing categories
            existing_categories = category_manager.get_product_categories(product.id)
            existing_category_ids = [cat.id for cat in existing_categories]
            
            if existing_categories:
                logger.info(f"Product {product.name} already has {len(existing_categories)} categories")
            else:
                # Suggest categories for the product
                suggested_categories = suggest_category_for_product(product)
                category_ids = [category_map[cat] for cat in suggested_categories if cat in category_map]
                
                # Assign categories
                for category_id in category_ids:
                    if category_id not in existing_category_ids:
                        try:
                            category_manager.assign_product_to_category(product.id, category_id)
                            assignment_count += 1
                            logger.info(f"Assigned product {product.name} to category {category_id}")
                        except Exception as e:
                            logger.error(f"Error assigning product {product.id} to category {category_id}: {e}")
    
    return assignment_count


def main():
    """Main function to assign products to categories."""
    try:
        # Initialize database
        init_db()
        
        # Use Flask app context
        with app.app_context():
            # Initialize managers
            product_manager = AppProductManager()
            category_manager = CategoryManager()
            tenant_manager = AppTenantManager()
            
            # Assign products to categories
            assignment_count = assign_products_to_categories(
                product_manager, 
                category_manager,
                tenant_manager
            )
            
            logger.info(f"Made {assignment_count} product-category assignments successfully!")
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()