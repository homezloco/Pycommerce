#!/usr/bin/env python3
"""
Debug script for market analysis issues.

This script analyzes problems with the market analysis dashboard,
particularly focusing on the Top Products section.
"""

import logging
import os
import sys
import json
from sqlalchemy import text
from datetime import datetime, timedelta

from app import app, db
from pycommerce.services.market_analysis import MarketAnalysisService
from pycommerce.models.tenant import TenantManager

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_market_analysis_service():
    """Test the market analysis service with direct debugging."""
    with app.app_context():
        try:
            # Initialize the service
            market_service = MarketAnalysisService()
            
            # Get all tenants for testing
            tenant_manager = TenantManager()
            tenants = tenant_manager.list()
            
            logger.info(f"Found {len(tenants)} tenants")
            
            for tenant in tenants:
                tenant_id = str(tenant.id)
                tenant_name = tenant.name
                logger.info(f"\nTesting tenant: {tenant_name} (ID: {tenant_id})")
                
                # Default to last 30 days
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                formatted_start = start_date.strftime("%Y-%m-%d")
                formatted_end = end_date.strftime("%Y-%m-%d")
                
                # Test sales trends retrieval
                logger.info(f"Testing sales trends for period: {formatted_start} to {formatted_end}")
                sales_trends = market_service.get_sales_trends(
                    tenant_id=tenant_id,
                    start_date=formatted_start,
                    end_date=formatted_end
                )
                
                # Check if we have top products data
                has_top_products = "top_products" in sales_trends.get("data", {}) and sales_trends["data"]["top_products"]
                if has_top_products:
                    top_products = sales_trends["data"]["top_products"]
                    logger.info(f"Found {len(top_products)} top products for tenant: {tenant_name}")
                    for product in top_products:
                        logger.info(f"  - {product.get('name')} (ID: {product.get('id')})")
                        logger.info(f"    Quantity: {product.get('quantity')}, Revenue: ${product.get('revenue')}")
                else:
                    logger.warning(f"No top products found for tenant: {tenant_name}")

                # Check orders in database directly
                order_count = db.session.execute(
                    text("SELECT COUNT(*) FROM orders WHERE tenant_id = :tenant_id"),
                    {"tenant_id": tenant_id}
                ).scalar()
                
                logger.info(f"Direct database check - Orders for tenant {tenant_name}: {order_count}")
                
                # Check order items with product IDs
                order_items = db.session.execute(
                    text("""
                        SELECT oi.product_id, COUNT(oi.id) AS order_count, 
                               SUM(oi.quantity) AS total_quantity, 
                               SUM(oi.price * oi.quantity) AS total_revenue
                        FROM order_items oi
                        JOIN orders o ON oi.order_id = o.id
                        WHERE o.tenant_id = :tenant_id
                        GROUP BY oi.product_id
                        ORDER BY total_quantity DESC
                        LIMIT 10
                    """),
                    {"tenant_id": tenant_id}
                ).fetchall()
                
                logger.info(f"Direct database check - Top products from order_items:")
                for item in order_items:
                    product_id = item.product_id
                    total_quantity = item.total_quantity
                    total_revenue = item.total_revenue
                    
                    # Try to get product name from products table
                    product_name = db.session.execute(
                        text("SELECT name FROM products WHERE id = :product_id"),
                        {"product_id": product_id}
                    ).scalar()
                    
                    if product_name:
                        logger.info(f"  - {product_name} (ID: {product_id})")
                    else:
                        logger.info(f"  - Unknown Product (ID: {product_id}) - Not found in products table")
                    
                    logger.info(f"    Quantity: {total_quantity}, Revenue: ${total_revenue:.2f}")
                
                # Check if there's a mismatch between order items and products
                if not has_top_products and order_items:
                    logger.error(f"MISMATCH DETECTED for tenant {tenant_name}: Orders exist but no top products returned")
                    
                    # Check the product-category mappings for this tenant
                    product_categories = db.session.execute(
                        text("""
                            SELECT pc.product_id, c.name as category_name
                            FROM product_categories pc
                            JOIN categories c ON pc.category_id = c.id
                            JOIN products p ON pc.product_id = p.id
                            WHERE p.tenant_id = :tenant_id
                        """),
                        {"tenant_id": tenant_id}
                    ).fetchall()
                    
                    logger.info(f"Product-category mappings for tenant {tenant_name}: {len(product_categories)}")
                    
                    # Get the product IDs with no categories
                    product_ids_in_orders = [item.product_id for item in order_items]
                    product_ids_with_categories = [item.product_id for item in product_categories]
                    
                    missing_categories = [pid for pid in product_ids_in_orders if pid not in product_ids_with_categories]
                    if missing_categories:
                        logger.warning(f"Products without categories: {len(missing_categories)}")
                        for pid in missing_categories:
                            product_name = db.session.execute(
                                text("SELECT name FROM products WHERE id = :product_id"),
                                {"product_id": pid}
                            ).scalar() or f"Unknown Product (ID: {pid[-6:]})"
                            
                            logger.warning(f"  - {product_name} (ID: {pid}) has no category assigned")
        
        except Exception as e:
            logger.error(f"Error testing market analysis service: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting market analysis debug script")
    test_market_analysis_service()
    logger.info("Market analysis debug script completed")