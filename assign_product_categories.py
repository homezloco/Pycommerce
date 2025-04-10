#!/usr/bin/env python
"""
Script to assign products to categories.

This script helps fix category assignment for existing products in the database.
It will ensure all products are properly assigned to categories so they display
correctly in the market analysis dashboard.
"""

import logging
import sys
from typing import List, Dict, Optional, Set

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import the models and managers
try:
    from app import app, db
    from pycommerce.models.product import Product, ProductManager
    from pycommerce.models.tenant import TenantManager
    from pycommerce.models.category import CategoryManager, Category
    from managers import TenantManager as AppTenantManager
    from managers import ProductManager as AppProductManager
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

def get_all_products(product_manager: AppProductManager, tenant_id: Optional[str] = None) -> List[Product]:
    """
    Get all products in the system, optionally filtered by tenant.
    
    Args:
        product_manager: The product manager instance
        tenant_id: Optional tenant ID to filter by
        
    Returns:
        List of products
    """
    try:
        if tenant_id:
            products = product_manager.get_products_by_tenant(tenant_id)
        else:
            products = product_manager.get_all_products()
        return products
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        return []

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
    
    categories = []
    
    # Simple keyword matching for different categories
    if any(keyword in name or keyword in description for keyword in ["laptop", "notebook", "macbook"]):
        categories.append("Laptops")
    
    if any(keyword in name or keyword in description for keyword in ["phone", "iphone", "android", "mobile", "smartphone"]):
        categories.append("Phones")
    
    if any(keyword in name or keyword in description for keyword in ["earbuds", "headphones", "speaker", "audio", "sound"]):
        categories.append("Audio")
    
    if any(keyword in name or keyword in description for keyword in ["watch", "band", "fitness tracker", "wearable"]):
        categories.append("Wearables")
    
    if any(keyword in name or keyword in description for keyword in ["camera", "gopro", "dslr", "photography"]):
        categories.append("Electronics")
    
    if any(keyword in name or keyword in description for keyword in ["charger", "case", "cover", "stand", "holder", "dock", "cable"]):
        categories.append("Accessories")
    
    if any(keyword in name or keyword in description for keyword in ["smart home", "alexa", "echo", "nest", "smart bulb", "hue"]):
        categories.append("Smart Home")
    
    # Default to Electronics if no specific category is found
    if not categories:
        categories.append("Electronics")
    
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
    required_categories = [
        "Laptops", "Phones", "Audio", "Wearables", "Electronics", 
        "Accessories", "Smart Home"
    ]
    
    category_map = {}
    
    # Get existing categories
    existing_categories = category_manager.get_for_tenant(tenant_id)
    existing_names = {cat.name: cat.id for cat in existing_categories}
    
    # Make sure all required categories exist
    for category_name in required_categories:
        if category_name in existing_names:
            category_map[category_name] = existing_names[category_name]
            logger.info(f"Category exists: {category_name} (ID: {existing_names[category_name]})")
        else:
            # Create the category
            with app.app_context():
                new_category = Category(
                    name=category_name,
                    tenant_id=tenant_id,
                    description=f"{category_name} products"
                )
                db.session.add(new_category)
                db.session.commit()
                category_id = new_category.id
                category_map[category_name] = category_id
                logger.info(f"Created category: {category_name} (ID: {category_id})")
    
    return category_map

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
    # Get all tenants
    tenants = tenant_manager.list()
    assignment_count = 0
    
    for tenant in tenants:
        tenant_id = tenant.id
        logger.info(f"Processing tenant: {tenant.name} (ID: {tenant_id})")
        
        # Ensure all categories exist
        category_map = ensure_categories_exist(category_manager, tenant_id)
        
        # Get all products for the tenant
        products = get_all_products(product_manager, tenant_id)
        logger.info(f"Found {len(products)} products for tenant {tenant.name}")
        
        # Assign categories to products
        for product in products:
            # Get current categories for the product
            current_categories = set()
            try:
                with app.app_context():
                    product_categories = category_manager.get_product_categories(product.id)
                    current_categories = {cat.name for cat in product_categories}
            except Exception as e:
                logger.warning(f"Error getting categories for product {product.id}: {e}")
            
            # Suggest categories based on product attributes
            suggested_categories = suggest_category_for_product(product)
            
            # Only add new categories if the product doesn't have any
            categories_to_add = []
            if not current_categories:
                categories_to_add = suggested_categories
                logger.info(f"Product has no categories, adding: {', '.join(categories_to_add)}")
            else:
                logger.info(f"Product already has categories: {', '.join(current_categories)}")
            
            # Assign categories to the product
            for category_name in categories_to_add:
                if category_name in category_map:
                    category_id = category_map[category_name]
                    try:
                        with app.app_context():
                            # Add the category to the product
                            category_manager.add_product_to_category(product.id, category_id)
                            logger.info(f"Added product {product.name} to category {category_name}")
                            assignment_count += 1
                    except Exception as e:
                        logger.error(f"Error assigning product {product.id} to category {category_id}: {e}")
    
    return assignment_count

def main():
    """Main function to assign products to categories."""
    logger.info("Starting to assign products to categories")
    
    # Let's use a direct approach with SQL to fix the issue
    from models import db, Product, Category, product_categories
    from sqlalchemy import text, insert
    
    # Get the tech tenant
    tech_tenant_id = None
    try:
        # Get tenant directly from the database
        tenant_result = db.session.execute(text("SELECT id, name FROM tenants WHERE slug = 'tech'")).fetchone()
        if tenant_result:
            tech_tenant_id = tenant_result[0]
            logger.info(f"Found Tech tenant with ID: {tech_tenant_id}")
        else:
            logger.error("Tech tenant not found")
            return
    except Exception as e:
        logger.error(f"Error finding tech tenant: {e}")
        return
    
    # Ensure categories exist
    categories = {
        "Laptops": None,
        "Phones": None,
        "Audio": None,
        "Wearables": None,
        "Electronics": None,
        "Accessories": None,
        "Smart Home": None
    }
    
    for category_name in categories.keys():
        # Check if category exists
        try:
            category = db.session.execute(
                text(f"SELECT id FROM categories WHERE name = :name AND tenant_id = :tenant_id"),
                {"name": category_name, "tenant_id": tech_tenant_id}
            ).fetchone()
            
            if category:
                categories[category_name] = category[0]
                logger.info(f"Found existing category: {category_name} (ID: {category[0]})")
            else:
                # Create the category
                new_category = Category(
                    name=category_name,
                    tenant_id=tech_tenant_id,
                    description=f"{category_name} products"
                )
                db.session.add(new_category)
                db.session.commit()
                categories[category_name] = new_category.id
                logger.info(f"Created new category: {category_name} (ID: {new_category.id})")
        except Exception as e:
            logger.error(f"Error with category {category_name}: {e}")
    
    # Get all products for the tech tenant
    try:
        products = db.session.query(Product).filter_by(tenant_id=tech_tenant_id).all()
        logger.info(f"Found {len(products)} products for Tech tenant")
        
        assignment_count = 0
        
        for product in products:
            # Check current categories
            product_cats = db.session.execute(
                text("SELECT category_id FROM product_categories WHERE product_id = :product_id"),
                {"product_id": product.id}
            ).fetchall()
            
            if product_cats:
                logger.info(f"Product {product.name} already has {len(product_cats)} categories")
                continue
            
            # Assign categories based on product name/description
            name = product.name.lower() if product.name else ""
            description = product.description.lower() if product.description else ""
            
            assigned_categories = []
            
            # Simple keyword matching
            if any(keyword in name or keyword in description for keyword in ["laptop", "notebook", "macbook", "ultrabook"]):
                assigned_categories.append("Laptops")
            
            if any(keyword in name or keyword in description for keyword in ["phone", "iphone", "android", "mobile", "smartphone"]):
                assigned_categories.append("Phones")
            
            if any(keyword in name or keyword in description for keyword in ["earbuds", "headphones", "speaker", "audio", "sound"]):
                assigned_categories.append("Audio")
            
            if any(keyword in name or keyword in description for keyword in ["watch", "band", "fitness tracker", "wearable"]):
                assigned_categories.append("Wearables")
            
            if any(keyword in name or keyword in description for keyword in ["camera", "gopro", "dslr", "photography"]):
                assigned_categories.append("Electronics")
            
            if any(keyword in name or keyword in description for keyword in ["charger", "case", "cover", "stand", "holder", "dock", "cable"]):
                assigned_categories.append("Accessories")
            
            if any(keyword in name or keyword in description for keyword in ["smart home", "alexa", "echo", "nest", "smart bulb", "hue"]):
                assigned_categories.append("Smart Home")
                
            # Default to Electronics if no specific category is found
            if not assigned_categories:
                assigned_categories.append("Electronics")
            
            logger.info(f"Assigning product '{product.name}' to categories: {', '.join(assigned_categories)}")
            
            # Add to product_categories table
            for category_name in assigned_categories:
                category_id = categories.get(category_name)
                if category_id:
                    try:
                        # Insert directly into the table
                        db.session.execute(
                            insert(product_categories).values(
                                product_id=product.id,
                                category_id=category_id
                            )
                        )
                        assignment_count += 1
                        logger.info(f"Assigned '{product.name}' to '{category_name}'")
                    except Exception as e:
                        logger.error(f"Error assigning {product.name} to {category_name}: {e}")
            
        # Commit all changes
        db.session.commit()
        logger.info(f"Completed with {assignment_count} product-category assignments")
        
    except Exception as e:
        logger.error(f"Error processing products: {e}")
        db.session.rollback()

if __name__ == "__main__":
    # Run with Flask app context
    with app.app_context():
        main()