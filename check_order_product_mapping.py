#!/usr/bin/env python3
"""
Script to check order item to product mapping.

This script identifies potential issues with product IDs in order items
that don't match product IDs in the database.
"""

import logging
import os
import sys
from sqlalchemy import inspect, text

from app import app, db

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_product_mapping():
    """Check mapping between order items and products."""
    with app.app_context():
        try:
            # First, let's check the structure of the order_items table
            inspector = inspect(db.engine)
            order_items_columns = inspector.get_columns("order_items")
            logger.info("Order Items table columns:")
            for col in order_items_columns:
                logger.info(f"  - {col['name']}: {col['type']}")
            logger.info("")
            
            # Count tables
            product_count = db.session.execute(text("SELECT COUNT(*) FROM products")).scalar()
            order_count = db.session.execute(text("SELECT COUNT(*) FROM orders")).scalar()
            order_item_count = db.session.execute(text("SELECT COUNT(*) FROM order_items")).scalar()
            
            logger.info(f"Database contains:")
            logger.info(f"  - {product_count} products")
            logger.info(f"  - {order_count} orders")
            logger.info(f"  - {order_item_count} order items")
            logger.info("")
            
            # Check order items to products mapping
            order_items = db.session.execute(
                text("""
                    SELECT oi.id, oi.order_id, oi.product_id, 
                           p.id AS product_db_id, p.name AS product_name
                    FROM order_items oi
                    LEFT JOIN products p ON oi.product_id = p.id
                    ORDER BY oi.id
                """)
            ).fetchall()
            
            if not order_items:
                logger.info("No order items found in the database")
                return
            
            missing_products = []
            matched_products = []
            
            for item in order_items:
                if item.product_db_id is None:
                    missing_products.append(item)
                else:
                    matched_products.append(item)
            
            logger.info(f"Found {len(matched_products)} order items with matching products")
            logger.info(f"Found {len(missing_products)} order items with missing products")
            
            if missing_products:
                logger.info("\nMissing product mappings:")
                for item in missing_products:
                    logger.info(f"Order item (ID: {item.id})")
                    logger.info(f"  - Order ID: {item.order_id}")
                    logger.info(f"  - Product ID: {item.product_id} (not in products table)")
                    logger.info("")
                
                # Check if there are any similar product IDs
                for item in missing_products:
                    similar_products = db.session.execute(
                        text("""
                            SELECT id, name, tenant_id
                            FROM products
                            WHERE id LIKE :pattern
                            LIMIT 5
                        """),
                        {"pattern": f"%{item.product_id[-6:]}%"}
                    ).fetchall()
                    
                    if similar_products:
                        logger.info(f"Similar products for {item.product_id}:")
                        for prod in similar_products:
                            logger.info(f"  - {prod.name} (ID: {prod.id})")
                        logger.info("")
            
            # Check top products by quantity
            logger.info("\nTop products by quantity sold:")
            top_products = db.session.execute(
                text("""
                    SELECT oi.product_id, SUM(oi.quantity) AS total_quantity, 
                           oi.name AS item_name,
                           p.id AS product_db_id, p.name AS product_name
                    FROM order_items oi
                    LEFT JOIN products p ON oi.product_id = p.id
                    GROUP BY oi.product_id, oi.name, p.id, p.name
                    ORDER BY total_quantity DESC
                    LIMIT 10
                """)
            ).fetchall()
            
            for item in top_products:
                product_status = "✓ FOUND IN DB" if item.product_db_id else "✗ MISSING FROM DB"
                product_name = item.product_name if item.product_name else item.item_name
                
                logger.info(f"{product_name} - {item.total_quantity} units - {product_status}")
                logger.info(f"  - Order Item Product ID: {item.product_id}")
                if item.product_db_id:
                    logger.info(f"  - Database Product ID: {item.product_db_id}")
                logger.info("")
                
        except Exception as e:
            logger.error(f"Error checking product mapping: {str(e)}")

if __name__ == "__main__":
    check_product_mapping()