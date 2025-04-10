#!/usr/bin/env python3
"""
Debug script to examine database structure.

This script inspects database tables and prints information about tables
and their columns to help diagnose issues.
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

def inspect_table(table_name):
    """Inspect a specific table in the database."""
    with app.app_context():
        inspector = inspect(db.engine)
        
        if table_name not in inspector.get_table_names():
            logger.error(f"Table '{table_name}' does not exist in the database")
            return
        
        columns = inspector.get_columns(table_name)
        logger.info(f"Table: {table_name}")
        logger.info(f"Columns:")
        for column in columns:
            logger.info(f"  - {column['name']}: {column['type']}")
        
        # Get a sample row
        try:
            sample = db.session.execute(
                text(f"SELECT * FROM {table_name} LIMIT 1")
            ).fetchone()
            
            if sample:
                logger.info(f"Sample row:")
                for i, column in enumerate(columns):
                    logger.info(f"  - {column['name']}: {sample[i]}")
            else:
                logger.info(f"No data in table {table_name}")
        except Exception as e:
            logger.error(f"Error getting sample row: {str(e)}")
        
        logger.info("-" * 50)

def count_table_rows(table_name):
    """Count rows in a specific table."""
    with app.app_context():
        try:
            count = db.session.execute(
                text(f"SELECT COUNT(*) FROM {table_name}")
            ).scalar()
            
            logger.info(f"Table {table_name}: {count} rows")
        except Exception as e:
            logger.error(f"Error counting rows in {table_name}: {str(e)}")

def examine_order_items():
    """Examine order items table specifically for product IDs."""
    with app.app_context():
        try:
            # Get order items with product IDs
            order_items = db.session.execute(
                text("""
                    SELECT oi.id, oi.order_id, oi.product_id, oi.name, oi.price, oi.quantity,
                           p.id as p_id, p.name as p_name, p.price as p_price
                    FROM order_items oi
                    LEFT JOIN products p ON oi.product_id = p.id
                    LIMIT 10
                """)
            ).fetchall()
            
            if not order_items:
                logger.info("No order items found in the database")
                return
            
            logger.info(f"Found {len(order_items)} order items:")
            for item in order_items:
                product_match = "MATCH" if item.product_id == item.p_id else "NO MATCH"
                logger.info(f"Item: {item.name} (ID: {item.id})")
                logger.info(f"  - Product ID: {item.product_id}")
                logger.info(f"  - Product in DB: {item.p_name if item.p_name else 'Not found'} ({product_match})")
                logger.info(f"  - Price: {item.price} (Product price: {item.p_price if item.p_price else 'N/A'})")
                logger.info(f"  - Quantity: {item.quantity}")
                logger.info("")
        except Exception as e:
            logger.error(f"Error examining order items: {str(e)}")

def check_top_products():
    """Fetch and display top products by sales."""
    with app.app_context():
        try:
            # Get order items grouped by product ID
            results = db.session.execute(
                text("""
                    SELECT oi.product_id, 
                           SUM(oi.quantity) as total_quantity,
                           SUM(oi.price * oi.quantity) as total_revenue,
                           p.name as product_name,
                           p.id as actual_product_id
                    FROM order_items oi
                    LEFT JOIN products p ON oi.product_id = p.id
                    GROUP BY oi.product_id, p.name, p.id
                    ORDER BY total_quantity DESC
                    LIMIT 10
                """)
            ).fetchall()
            
            if not results:
                logger.info("No product sales data found in the database")
                return
            
            logger.info(f"Top products by sales:")
            for item in results:
                product_name = item.product_name if item.product_name else f"Product {item.product_id[-6:]}"
                product_match = "MATCH" if item.product_id == item.actual_product_id else "NO MATCH"
                logger.info(f"{product_name}")
                logger.info(f"  - Product ID: {item.product_id}")
                logger.info(f"  - Product ID in DB: {item.actual_product_id} ({product_match})")
                logger.info(f"  - Total Quantity: {item.total_quantity}")
                logger.info(f"  - Total Revenue: ${item.total_revenue:.2f}")
                logger.info("")
            
            # Now try to list all products from the database
            logger.info("-" * 50)
            logger.info("All products in database:")
            products = db.session.execute(
                text("""
                    SELECT id, name, price, sku, tenant_id
                    FROM products
                    ORDER BY name
                """)
            ).fetchall()
            
            logger.info(f"Found {len(products)} products in database:")
            for product in products:
                logger.info(f"{product.name}")
                logger.info(f"  - ID: {product.id}")
                logger.info(f"  - Price: ${product.price:.2f}")
                logger.info(f"  - SKU: {product.sku}")
                logger.info(f"  - Tenant ID: {product.tenant_id}")
                logger.info("")
        except Exception as e:
            logger.error(f"Error checking top products: {str(e)}")

def main():
    """Main function to debug database."""
    logger.info("Starting database debug script")
    
    # Inspect main tables
    inspect_table("products")
    inspect_table("categories")
    inspect_table("orders")
    inspect_table("order_items")
    inspect_table("product_categories")
    
    # Count rows in tables
    count_table_rows("products")
    count_table_rows("categories")
    count_table_rows("orders")
    count_table_rows("order_items")
    count_table_rows("product_categories")
    
    # Examine order items
    examine_order_items()
    
    # Check top products
    check_top_products()
    
    logger.info("Database debug script completed")

if __name__ == "__main__":
    main()