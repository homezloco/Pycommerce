#!/usr/bin/env python3
"""
Script to ensure products are properly assigned to categories.

This script checks if all products have at least one category assigned,
and assigns them to appropriate categories if needed.
"""

import logging
import json
import os
import datetime
from typing import Dict, List, Set, Tuple, Optional, Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app import app, db

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_products_without_categories() -> List[Tuple[str, str, str]]:
    """
    Find products that don't have any categories assigned.
    
    Returns:
        List of tuples (product_id, product_name, tenant_id) for products without categories
    """
    logger.info("Checking for products without categories")
    
    with app.app_context():
        # Get all products that don't have categories assigned
        result = db.session.execute(
            text("""
                SELECT p.id, p.name, p.tenant_id
                FROM products p
                LEFT JOIN product_categories pc ON p.id = pc.product_id
                WHERE pc.category_id IS NULL
            """)
        ).fetchall()
        
        products_without_categories = [(str(row[0]), row[1], str(row[2])) for row in result]
        logger.info(f"Found {len(products_without_categories)} products without categories")
        
        return products_without_categories

def get_categories_for_tenant(tenant_id: str) -> List[Tuple[str, str]]:
    """
    Get all categories for a tenant.
    
    Args:
        tenant_id: The tenant ID
        
    Returns:
        List of tuples (category_id, category_name) for categories belonging to the tenant
    """
    with app.app_context():
        result = db.session.execute(
            text("""
                SELECT id, name
                FROM categories
                WHERE tenant_id = :tenant_id
            """),
            {"tenant_id": tenant_id}
        ).fetchall()
        
        categories = [(str(row[0]), row[1]) for row in result]
        
        if not categories:
            logger.warning(f"No categories found for tenant {tenant_id}")
            
        return categories

def assign_product_to_category(product_id: str, category_id: str) -> bool:
    """
    Assign a product to a category.
    
    Args:
        product_id: The product ID
        category_id: The category ID
        
    Returns:
        True if the assignment was successful, False otherwise
    """
    try:
        with app.app_context():
            # Check if the relationship already exists
            existing = db.session.execute(
                text("""
                    SELECT 1
                    FROM product_categories
                    WHERE product_id = :product_id AND category_id = :category_id
                """),
                {"product_id": product_id, "category_id": category_id}
            ).fetchone()
            
            if existing:
                logger.debug(f"Product {product_id} is already assigned to category {category_id}")
                return True
            
            # Insert the relationship
            db.session.execute(
                text("""
                    INSERT INTO product_categories (product_id, category_id)
                    VALUES (:product_id, :category_id)
                """),
                {"product_id": product_id, "category_id": category_id}
            )
            
            # Commit the transaction
            db.session.commit()
            
            return True
    except Exception as e:
        logger.error(f"Error assigning product {product_id} to category {category_id}: {str(e)}")
        return False

def find_best_category_match(product_name: str, categories: List[Tuple[str, str]]) -> Optional[Tuple[str, str]]:
    """
    Find the best category match for a product based on its name.
    
    Args:
        product_name: The product name
        categories: List of tuples (category_id, category_name) to match against
        
    Returns:
        Tuple (category_id, category_name) of the best matching category, or None if no match
    """
    product_name_lower = product_name.lower()
    
    # First try exact word matches
    for category_id, category_name in categories:
        category_name_lower = category_name.lower()
        if category_name_lower in product_name_lower.split():
            return (category_id, category_name)
    
    # Then try substring matches
    for category_id, category_name in categories:
        category_name_lower = category_name.lower()
        if category_name_lower in product_name_lower:
            return (category_id, category_name)
    
    # Look for specific keywords that might indicate categories
    keywords = {
        "laptop": "Laptops",
        "computer": "Laptops",
        "phone": "Phones",
        "smartphone": "Phones",
        "earbuds": "Audio",
        "headphones": "Audio",
        "speaker": "Audio",
        "charger": "Accessories",
        "cable": "Accessories",
        "case": "Accessories",
        "watch": "Wearables",
        "band": "Wearables",
        "tracker": "Wearables",
        "camera": "Electronics",
        "tv": "Electronics",
        "device": "Electronics",
        "hub": "Smart Home",
        "thermostat": "Smart Home",
        "assistant": "Smart Home"
    }
    
    for keyword, category_type in keywords.items():
        if keyword in product_name_lower:
            # Find the category that matches this type
            for category_id, category_name in categories:
                if category_name.lower() == category_type.lower():
                    return (category_id, category_name)
    
    # If no match, return the first category as default (if available)
    return categories[0] if categories else None

def main():
    """Main function."""
    logger.info("Starting fix_product_category_mapping.py")
    
    # Find products without categories
    products_without_categories = find_products_without_categories()
    
    assigned_count = 0
    
    for product_id, product_name, tenant_id in products_without_categories:
        # Get categories for this tenant
        categories = get_categories_for_tenant(tenant_id)
        
        if not categories:
            logger.warning(f"No categories available for product {product_id} (tenant {tenant_id})")
            continue
        
        # Find the best category match
        category_match = find_best_category_match(product_name, categories)
        
        if category_match:
            category_id, category_name = category_match
            
            # Assign the product to the category
            if assign_product_to_category(product_id, category_id):
                logger.info(f"Assigned product '{product_name}' to category '{category_name}'")
                assigned_count += 1
    
    logger.info(f"Assigned {assigned_count} products to categories")
    
    # Now check all product-category mappings for the market analysis dashboard
    check_market_analysis_categories()
    
    return assigned_count

def check_market_analysis_categories():
    """
    Check all product category mappings for the market analysis dashboard.
    
    This function checks if any categories have single-letter names (which causes
    issues in the market analysis dashboard) and logs them for further investigation.
    """
    logger.info("Checking product category mappings for market analysis dashboard")
    
    with app.app_context():
        # Get all categories
        categories_result = db.session.execute(
            text("""
                SELECT id, name, tenant_id
                FROM categories
            """)
        ).fetchall()
        
        categories = [(str(row[0]), row[1], str(row[2])) for row in categories_result]
        
        # Check for single-letter category names
        short_categories = [(cid, name, tid) for cid, name, tid in categories if len(name) <= 1]
        
        if short_categories:
            logger.warning(f"Found {len(short_categories)} categories with short names:")
            
            for category_id, name, tenant_id in short_categories:
                logger.warning(f"  Category ID {category_id}: '{name}' (tenant {tenant_id})")
        
        # Get product-category mappings for orders
        query = """
            SELECT DISTINCT p.id, p.name, c.id, c.name 
            FROM products p
            JOIN product_categories pc ON p.id = pc.product_id
            JOIN categories c ON pc.category_id = c.id
            JOIN order_items oi ON p.id = oi.product_id
        """
        
        product_categories = db.session.execute(text(query)).fetchall()
        
        if product_categories:
            logger.info(f"Found {len(product_categories)} product-category mappings for ordered products")
        else:
            logger.warning("No product-category mappings found for ordered products")

if __name__ == "__main__":
    main()