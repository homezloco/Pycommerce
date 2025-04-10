#!/usr/bin/env python
"""
Script to fix product categories in the database.

This script adds categories to products by directly manipulating the database tables,
allowing the market analysis dashboard to properly display category metrics.
"""

import logging
import os
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_product_categories():
    """Fix product categories by adding direct database entries."""
    from app import app, db
    
    with app.app_context():
        # Get tenant ID for Tech Gadgets
        tenant_result = db.session.execute(
            text("SELECT id FROM tenants WHERE slug = 'tech'")
        ).fetchone()
        
        if not tenant_result:
            logger.error("Tech tenant not found")
            return False
        
        tenant_id = tenant_result[0]
        logger.info(f"Found Tech tenant with ID: {tenant_id}")
        
        # Create necessary categories
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
            cat_result = db.session.execute(
                text("SELECT id FROM categories WHERE name = :name AND tenant_id = :tenant_id"),
                {"name": category_name, "tenant_id": tenant_id}
            ).fetchone()
            
            if cat_result:
                categories[category_name] = cat_result[0]
                logger.info(f"Found existing category: {category_name} (ID: {cat_result[0]})")
            else:
                # Create new category
                cat_id = os.urandom(16).hex()
                db.session.execute(
                    text("""
                        INSERT INTO categories (id, name, tenant_id, description, created_at, updated_at)
                        VALUES (:id, :name, :tenant_id, :description, current_timestamp, current_timestamp)
                    """),
                    {
                        "id": cat_id,
                        "name": category_name,
                        "tenant_id": tenant_id,
                        "description": f"{category_name} products"
                    }
                )
                categories[category_name] = cat_id
                logger.info(f"Created new category: {category_name} (ID: {cat_id})")
        
        # Get all products for this tenant
        products = db.session.execute(
            text("SELECT id, name, description FROM products WHERE tenant_id = :tenant_id"),
            {"tenant_id": tenant_id}
        ).fetchall()
        
        logger.info(f"Found {len(products)} products for Tech tenant")
        
        assignment_count = 0
        
        # Clear existing product-category associations
        db.session.execute(
            text("""
                DELETE FROM product_categories 
                WHERE product_id IN (
                    SELECT id FROM products WHERE tenant_id = :tenant_id
                )
            """),
            {"tenant_id": tenant_id}
        )
        logger.info("Cleared existing product-category associations")
        
        # Assign product categories
        for product in products:
            product_id = product[0]
            product_name = product[1]
            product_description = product[2] or ""
            
            # Make lowercase for easier matching
            name_lower = product_name.lower()
            desc_lower = product_description.lower()
            
            # Determine categories based on keywords
            product_categories = []
            
            # Simple keyword matching
            if any(keyword in name_lower or keyword in desc_lower for keyword in ["laptop", "notebook", "macbook", "ultrabook"]):
                product_categories.append("Laptops")
            
            if any(keyword in name_lower or keyword in desc_lower for keyword in ["phone", "iphone", "android", "mobile", "smartphone"]):
                product_categories.append("Phones")
            
            if any(keyword in name_lower or keyword in desc_lower for keyword in ["earbuds", "headphones", "speaker", "audio", "sound"]):
                product_categories.append("Audio")
            
            if any(keyword in name_lower or keyword in desc_lower for keyword in ["watch", "band", "fitness tracker", "wearable"]):
                product_categories.append("Wearables")
            
            if any(keyword in name_lower or keyword in desc_lower for keyword in ["camera", "gopro", "dslr", "photography"]):
                product_categories.append("Electronics")
            
            if any(keyword in name_lower or keyword in desc_lower for keyword in ["charger", "case", "cover", "stand", "holder", "dock", "cable"]):
                product_categories.append("Accessories")
            
            if any(keyword in name_lower or keyword in desc_lower for keyword in ["smart home", "alexa", "echo", "nest", "smart bulb", "hue"]):
                product_categories.append("Smart Home")
            
            # Default to Electronics if no match
            if not product_categories:
                product_categories.append("Electronics")
            
            logger.info(f"Product '{product_name}' will be assigned to: {', '.join(product_categories)}")
            
            # Insert category associations
            for category_name in product_categories:
                category_id = categories.get(category_name)
                if category_id:
                    db.session.execute(
                        text("""
                            INSERT INTO product_categories (product_id, category_id)
                            VALUES (:product_id, :category_id)
                        """),
                        {"product_id": product_id, "category_id": category_id}
                    )
                    assignment_count += 1
                    logger.info(f"Assigned product '{product_name}' to category '{category_name}'")
        
        # Commit all changes
        db.session.commit()
        logger.info(f"Successfully assigned {assignment_count} product-category associations")
        return True

if __name__ == "__main__":
    try:
        logger.info("Starting product category fix")
        success = fix_product_categories()
        if success:
            logger.info("Product categories fixed successfully")
        else:
            logger.error("Failed to fix product categories")
    except Exception as e:
        logger.error(f"Error fixing product categories: {str(e)}")