"""
Utility script to create missing products from order data.

This script checks all orders in the system, identifies product IDs that don't 
have corresponding products in the database, and creates those products to ensure
proper rendering of the market analysis dashboard.
"""

import logging
import os
import sys
import uuid
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import Flask app context
from app import app, db
from models import Tenant, Product

# Import from pycommerce
from pycommerce.models.category import CategoryManager, Category
from pycommerce.models.order import Order, OrderItem
from pycommerce.core.db import init_db

# Import managers but with alternative names to avoid conflicts
from managers import ProductManager as AppProductManager
from managers import TenantManager as AppTenantManager
from pycommerce.models.order import OrderManager as PyOrderManager


def extract_missing_product_ids(product_manager: AppProductManager, order_manager: PyOrderManager) -> Dict[str, List[OrderItem]]:
    """
    Extract product IDs from orders that don't exist in the product manager.
    
    Args:
        product_manager: The product manager instance
        order_manager: The order manager instance
        
    Returns:
        Dictionary mapping missing product IDs to their order items for reference
    """
    missing_products: Dict[str, List[OrderItem]] = {}
    
    # Get all orders (using the get_for_tenant method with no tenant_id to get all)
    orders = order_manager.get_for_tenant()
    logger.info(f"Found {len(orders)} orders in the system")
    
    # Get all unique product IDs from orders
    order_product_ids = set()
    for order in orders:
        for item in order.items:
            if hasattr(item, 'product_id') and item.product_id:
                order_product_ids.add(str(item.product_id))
            
    logger.info(f"Found {len(order_product_ids)} unique product IDs referenced in orders")
    
    # Check each product ID both through the manager and directly in the database
    for product_id in order_product_ids:
        # First check through the manager
        product_exists = False
        
        # Check the manager
        try:
            product = product_manager.get_product_by_id(product_id)
            if product:
                product_exists = True
        except Exception:
            # Product not found through manager, continue to database check
            pass
            
        # If not found through manager, check directly in database
        if not product_exists:
            try:
                # Direct database query
                product_record = db.session.query(Product).filter(Product.id == product_id).first()
                if product_record:
                    product_exists = True
                    logger.info(f"Product {product_id} exists in database but not found through manager")
            except Exception as e:
                logger.warning(f"Error checking product {product_id} in database: {e}")
                
        # If still not found, add to missing products
        if not product_exists:
            logger.info(f"Product {product_id} is missing from the database")
            # Find the order items for this product
            missing_products[product_id] = []
            for order in orders:
                for item in order.items:
                    if str(item.product_id) == product_id:
                        missing_products[product_id].append(item)
    
    logger.info(f"Found {len(missing_products)} unique missing products")
    return missing_products


def infer_product_details(product_id: str, items: List[OrderItem]) -> Tuple[str, float, str, List[str]]:
    """
    Infer product details from order items.
    
    Args:
        product_id: The product ID
        items: List of order items for this product ID
        
    Returns:
        Tuple of (name, price, description, categories)
    """
    # Default values
    name = f"Product {product_id[-6:]}"  # Use last 6 chars of ID for readability
    price = 0.0
    description = f"Auto-created product for ID {product_id}"
    categories = []
    
    # Try to get better information from the order items
    if items:
        # Use the most recent order's price
        price = items[-1].price if hasattr(items[-1], 'price') else 0.0
        
        # If any item has a name attribute, use it
        for item in items:
            if hasattr(item, 'name') and item.name:
                name = item.name
                break
                
        # If any item has a description attribute, use it
        for item in items:
            if hasattr(item, 'description') and item.description:
                description = item.description
                break
    
    # Infer categories based on the product ID
    id_suffix = product_id[-6:]
    if id_suffix in ['036ef6', '0a00a4']:
        categories = ["Laptops"]
    elif id_suffix in ['60a6eb', '44f144']:
        categories = ["Audio"]
    elif id_suffix in ['174922', 'fa4014']:
        categories = ["Phones"]
    elif id_suffix in ['e69e99', '9e0c47']:
        categories = ["Accessories"]
    else:
        # Default to Electronics if we can't determine a more specific category
        categories = ["Electronics"]
    
    return name, price, description, categories


def create_missing_products(
    product_manager: AppProductManager, 
    category_manager: CategoryManager,
    tenant_manager: AppTenantManager,
    missing_products: Dict[str, List[OrderItem]]
) -> int:
    """
    Create missing products with appropriate categories.
    
    Args:
        product_manager: The product manager instance
        category_manager: The category manager instance
        tenant_manager: The tenant manager instance
        missing_products: Dictionary of missing product IDs to their order items
        
    Returns:
        Number of products created
    """
    created_count = 0
    
    # Get default tenant for product creation
    default_tenant = tenant_manager.get_tenant_by_slug("tech")
    if not default_tenant:
        default_tenant = tenant_manager.get_all_tenants()[0] if tenant_manager.get_all_tenants() else None
    
    if not default_tenant:
        logger.error("No tenants found in the system, cannot create products")
        return 0
        
    tenant_id = default_tenant.id
    
    # Ensure categories exist for our product categorization
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
                if category and hasattr(category, 'id'):
                    primary_categories[category_name] = category.id
                    logger.info(f"Created category {category_name} with ID {category.id}")
                else:
                    logger.warning(f"Created category {category_name} but no ID was returned")
            except Exception as e:
                logger.error(f"Error creating category {category_name}: {e}")
    
    # Create each missing product
    for product_id, items in missing_products.items():
        name, price, description, categories = infer_product_details(product_id, items)
        
        # Create the product
        try:
            # Convert category names to IDs
            category_ids = [primary_categories[cat] for cat in categories if cat in primary_categories]
            
            # Create product with a specific ID (matching the ID used in orders)
            # First, check if we can create directly with the specific ID
            try:
                # Try to create directly in the database with the specific product_id
                with db.session.begin():
                    product = Product(
                        id=product_id,
                        tenant_id=tenant_id,
                        name=name,
                        price=price,
                        description=description,
                        sku=f"SKU-{product_id[-6:]}",
                        stock=10,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.session.add(product)
                logger.info(f"Created product directly in database with ID {product_id}")
            except Exception as e:
                logger.warning(f"Could not create product directly with ID {product_id}: {e}")
                # Fall back to standard creation if direct creation fails
                product = product_manager.create_product(
                    tenant_id=tenant_id,
                    name=name,
                    price=price,
                    description=description,
                    sku=f"SKU-{product_id[-6:]}",
                    stock=10
                )
                logger.warning(f"Created product with new ID {product.id} instead of {product_id}")
                # Map the old product ID to the new one for category assignment
                product_id = product.id
            
            # Assign categories
            for category_id in category_ids:
                if category_id:
                    try:
                        # Use the correct product ID for category assignment
                        category_manager.assign_product_to_category(product.id, category_id)
                    except Exception as e:
                        logger.error(f"Error assigning product {product.id} to category: {e}")
                        # Try direct database assignment if the category manager fails
                        try:
                            with db.session.begin():
                                # Create direct association in the product_categories table
                                db.session.execute(
                                    f"INSERT INTO product_categories (product_id, category_id) VALUES ('{product.id}', '{category_id}')"
                                )
                            logger.info(f"Assigned product {product.id} to category {category_id} directly in database")
                        except Exception as inner_e:
                            logger.error(f"Direct category assignment also failed: {inner_e}")
            
            created_count += 1
            logger.info(f"Created product {name} (ID: {product_id}) with categories: {', '.join(categories)}")
            
        except Exception as e:
            logger.error(f"Error creating product {product_id}: {e}")
    
    return created_count


def main():
    """Main function to create missing products."""
    try:
        # Initialize database
        init_db()
        
        # Use Flask app context
        with app.app_context():
            # Initialize managers
            product_manager = AppProductManager()
            order_manager = PyOrderManager()
            category_manager = CategoryManager()
            tenant_manager = AppTenantManager()
            
            # Find missing products
            missing_products = extract_missing_product_ids(product_manager, order_manager)
            
            if not missing_products:
                logger.info("No missing products found!")
                return
                
            # Create missing products
            created_count = create_missing_products(
                product_manager, 
                category_manager,
                tenant_manager,
                missing_products
            )
            
            logger.info(f"Created {created_count} missing products successfully!")
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()