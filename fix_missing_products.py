#!/usr/bin/env python3
"""
Script to fix missing products in the database that appear in orders.

This script identifies product IDs referenced in orders but missing in the product database,
and creates those missing products with data inferred from the orders.
"""

import logging
import json
import os
import datetime
from typing import Dict, List, Set, Tuple, Optional, Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app import app, db
from pycommerce.models.order import OrderItem

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_missing_product_ids() -> List[str]:
    """
    Find product IDs in orders that don't exist in the products table.
    
    Returns:
        List of product IDs that are missing from the products table
    """
    logger.info("Checking for missing products in the database")
    
    with app.app_context():
        # Get all product IDs from orders
        order_product_ids_result = db.session.execute(
            text("""
                SELECT DISTINCT product_id 
                FROM order_items
            """)
        ).fetchall()
        
        order_product_ids = {str(row[0]) for row in order_product_ids_result}
        logger.info(f"Found {len(order_product_ids)} unique product IDs in orders")
        
        # Get all product IDs from products table
        existing_product_ids_result = db.session.execute(
            text("""
                SELECT id 
                FROM products
            """)
        ).fetchall()
        
        existing_product_ids = {str(row[0]) for row in existing_product_ids_result}
        logger.info(f"Found {len(existing_product_ids)} existing products in database")
        
        # Find missing product IDs
        missing_product_ids = order_product_ids - existing_product_ids
        logger.info(f"Found {len(missing_product_ids)} missing products that need to be created")
        
        return list(missing_product_ids)

def get_order_item_data(product_id: str) -> Dict[str, Any]:
    """
    Retrieve order item data for a specific product ID.
    
    Args:
        product_id: The product ID to look up
        
    Returns:
        Dictionary with order item data
    """
    with app.app_context():
        # Get all order items for this product
        order_items_result = db.session.execute(
            text("""
                SELECT oi.product_id, oi.name, oi.price, oi.quantity, o.tenant_id, o.created_at
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE oi.product_id = :product_id
                ORDER BY o.created_at DESC
            """),
            {"product_id": product_id}
        ).fetchall()
        
        if not order_items_result:
            logger.warning(f"No order items found for product ID {product_id}")
            return {}
        
        # Use the most recent order item as reference
        item = order_items_result[0]
        
        return {
            "product_id": str(item[0]),
            "name": item[1],
            "price": float(item[2]),
            "tenant_id": str(item[4]),
            "quantity": int(item[3]),
            "order_count": len(order_items_result)
        }

def create_missing_product(product_id: str, item_data: Dict[str, Any]) -> bool:
    """
    Create a missing product in the database.
    
    Args:
        product_id: The product ID to create
        item_data: Dictionary with product data from order items
        
    Returns:
        True if product was created successfully, False otherwise
    """
    try:
        with app.app_context():
            # Generate a description based on the product name
            description = f"Product automatically created from order data. Original product ID: {product_id}"
            
            # Calculate stock based on order history (add some buffer)
            stock = max(item_data["quantity"] * 2, 10)
            
            # Generate a SKU based on product ID
            sku = f"SKU-{product_id[-8:]}"
            
            # Insert the product
            db.session.execute(
                text("""
                    INSERT INTO products (id, name, price, description, sku, stock, tenant_id, created_at, updated_at)
                    VALUES (:id, :name, :price, :description, :sku, :stock, :tenant_id, :created_at, :updated_at)
                """),
                {
                    "id": product_id,
                    "name": item_data["name"],
                    "price": item_data["price"],
                    "description": description,
                    "sku": sku,
                    "stock": stock,
                    "tenant_id": item_data["tenant_id"],
                    "created_at": datetime.datetime.now(),
                    "updated_at": datetime.datetime.now()
                }
            )
            
            # Commit the transaction
            db.session.commit()
            
            logger.info(f"Created missing product: {item_data['name']} (ID: {product_id})")
            return True
    except Exception as e:
        logger.error(f"Error creating product {product_id}: {str(e)}")
        return False

def assign_product_to_categories(product_id: str, tenant_id: str) -> None:
    """
    Assign the product to appropriate categories.
    
    Args:
        product_id: The product ID to assign categories to
        tenant_id: The tenant ID that owns the product
    """
    try:
        with app.app_context():
            # Get available categories for the tenant
            categories_result = db.session.execute(
                text("""
                    SELECT id, name 
                    FROM categories
                    WHERE tenant_id = :tenant_id
                """),
                {"tenant_id": tenant_id}
            ).fetchall()
            
            if not categories_result:
                logger.warning(f"No categories found for tenant {tenant_id}")
                return
            
            # Choose a category based on the product name
            product_result = db.session.execute(
                text("""
                    SELECT name
                    FROM products
                    WHERE id = :product_id
                """),
                {"product_id": product_id}
            ).fetchone()
            
            if not product_result:
                logger.warning(f"Product {product_id} not found in database")
                return
            
            product_name = product_result[0].lower()
            
            # Try to find a matching category
            matched_category = None
            for category in categories_result:
                category_name = category[1].lower()
                if category_name in product_name:
                    matched_category = category
                    break
            
            # If no match, use the first category
            if not matched_category and categories_result:
                matched_category = categories_result[0]
            
            if matched_category:
                # Check if the relationship already exists
                existing = db.session.execute(
                    text("""
                        SELECT 1
                        FROM product_categories
                        WHERE product_id = :product_id AND category_id = :category_id
                    """),
                    {"product_id": product_id, "category_id": matched_category[0]}
                ).fetchone()
                
                if not existing:
                    # Insert the relationship
                    db.session.execute(
                        text("""
                            INSERT INTO product_categories (product_id, category_id)
                            VALUES (:product_id, :category_id)
                        """),
                        {"product_id": product_id, "category_id": matched_category[0]}
                    )
                    
                    # Commit the transaction
                    db.session.commit()
                    
                    logger.info(f"Assigned product {product_id} to category '{matched_category[1]}'")
    except Exception as e:
        logger.error(f"Error assigning product {product_id} to categories: {str(e)}")

def main():
    """Main function."""
    logger.info("Starting fix_missing_products.py")
    
    # Find missing product IDs
    missing_product_ids = find_missing_product_ids()
    
    created_count = 0
    
    # Create missing products
    for product_id in missing_product_ids:
        # Get order item data for this product
        item_data = get_order_item_data(product_id)
        
        if item_data:
            # Create the product
            if create_missing_product(product_id, item_data):
                created_count += 1
                
                # Assign to categories
                assign_product_to_categories(product_id, item_data["tenant_id"])
    
    logger.info(f"Created {created_count} missing products")
    
    return created_count

if __name__ == "__main__":
    main()