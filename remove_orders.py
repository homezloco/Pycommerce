#!/usr/bin/env python
"""
Script to remove all orders from a tenant.

This script removes all orders and related data (order items, notes, shipments)
for a specified tenant. It's useful for testing and development purposes.
"""

import logging
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def remove_orders_for_tenant(tenant_slug="tech"):
    """
    Remove all orders and related data for the specified tenant.
    
    Args:
        tenant_slug: The slug of the tenant to remove orders for
        
    Returns:
        Tuple of (success, count of orders removed)
    """
    from app import app, db
    
    with app.app_context():
        # Get tenant ID
        tenant_result = db.session.execute(
            text("SELECT id FROM tenants WHERE slug = :slug"),
            {"slug": tenant_slug}
        ).fetchone()
        
        if not tenant_result:
            logger.error(f"Tenant not found with slug: {tenant_slug}")
            return False, 0
        
        tenant_id = tenant_result[0]
        logger.info(f"Found tenant {tenant_slug} with ID: {tenant_id}")
        
        # Get order IDs for this tenant
        order_ids_result = db.session.execute(
            text("SELECT id FROM orders WHERE tenant_id = :tenant_id"),
            {"tenant_id": tenant_id}
        ).fetchall()
        
        if not order_ids_result:
            logger.info(f"No orders found for tenant: {tenant_slug}")
            return True, 0
        
        order_ids = [row[0] for row in order_ids_result]
        logger.info(f"Found {len(order_ids)} orders to remove")
        
        # Remove order-related data first (due to foreign key constraints)
        try:
            # Remove order notes
            notes_deleted = db.session.execute(
                text("DELETE FROM order_notes WHERE order_id IN :order_ids"),
                {"order_ids": tuple(order_ids)}
            ).rowcount
            logger.info(f"Deleted {notes_deleted} order notes")
            
            # Remove shipments
            shipments_deleted = db.session.execute(
                text("DELETE FROM shipments WHERE order_id IN :order_ids"),
                {"order_ids": tuple(order_ids)}
            ).rowcount
            logger.info(f"Deleted {shipments_deleted} shipments")
            
            # Remove order items
            items_deleted = db.session.execute(
                text("DELETE FROM order_items WHERE order_id IN :order_ids"),
                {"order_ids": tuple(order_ids)}
            ).rowcount
            logger.info(f"Deleted {items_deleted} order items")
            
            # Finally, remove orders
            orders_deleted = db.session.execute(
                text("DELETE FROM orders WHERE id IN :order_ids"),
                {"order_ids": tuple(order_ids)}
            ).rowcount
            logger.info(f"Deleted {orders_deleted} orders")
            
            # Commit changes
            db.session.commit()
            logger.info("Successfully removed all orders and related data")
            
            return True, orders_deleted
            
        except Exception as e:
            logger.error(f"Error removing orders: {str(e)}")
            db.session.rollback()
            return False, 0

if __name__ == "__main__":
    try:
        logger.info("Starting order removal")
        success, count = remove_orders_for_tenant()
        if success:
            logger.info(f"Successfully removed {count} orders")
        else:
            logger.error("Failed to remove orders")
    except Exception as e:
        logger.error(f"Error: {str(e)}")