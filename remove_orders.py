#!/usr/bin/env python
"""
Script to remove all existing orders from the database.

This script will delete all orders for a specified tenant,
making it possible to recreate them with proper product categories.
"""
import logging
import sys
from typing import Optional
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import the models and managers
try:
    from pycommerce.models.order import OrderManager
    from pycommerce.models.tenant import TenantManager
    from models import db, Order, OrderItem
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

def remove_orders_for_tenant(tenant_slug: str) -> int:
    """
    Remove all orders for a specific tenant.
    
    Args:
        tenant_slug: The slug of the tenant to remove orders for
        
    Returns:
        Number of orders removed
    """
    tenant_manager = TenantManager()
    order_manager = OrderManager()
    
    # Get tenant by slug
    tenant = tenant_manager.get_tenant_by_slug(tenant_slug)
    if not tenant:
        logger.error(f"Tenant with slug '{tenant_slug}' not found")
        return 0
        
    logger.info(f"Found tenant: {tenant.name} (ID: {tenant.id})")
    
    # Get all orders for this tenant
    orders = order_manager.get_for_tenant(tenant.id)
    if not orders:
        logger.info(f"No orders found for tenant {tenant.name}")
        return 0
        
    logger.info(f"Found {len(orders)} orders for tenant {tenant.name}")
    
    # Delete each order
    removed_count = 0
    for order in orders:
        try:
            # First, check if there are related order_notes
            try:
                # Try direct SQL access to delete order notes
                db.session.execute(text(f"DELETE FROM order_notes WHERE order_id = '{order.id}'"))
            except Exception as note_error:
                logger.warning(f"Could not delete order notes for {order.id}: {note_error}")
            
            # Check if there are related shipments
            try:
                # Delete shipments if they exist (direct SQL)
                db.session.execute(text(f"DELETE FROM shipments WHERE order_id = '{order.id}'"))
            except Exception as ship_error:
                logger.warning(f"Could not delete shipments for {order.id}: {ship_error}")
            
            # Delete order items
            OrderItem.query.filter_by(order_id=order.id).delete()
            
            # Then delete the order itself
            Order.query.filter_by(id=order.id).delete()
            
            # Commit the transaction
            db.session.commit()
            removed_count += 1
            logger.info(f"Removed order {order.id}")
        except Exception as e:
            logger.error(f"Error removing order {order.id}: {e}")
            db.session.rollback()
    
    logger.info(f"Successfully removed {removed_count} orders for tenant {tenant.name}")
    return removed_count

def main():
    """Main function to remove orders."""
    # Default tenant to "tech"
    tenant_slug = "tech"
    
    try:
        # Remove orders for the tenant
        count = remove_orders_for_tenant(tenant_slug)
        logger.info(f"Removed {count} orders for tenant {tenant_slug}")
    except Exception as e:
        logger.error(f"Error removing orders: {e}")

if __name__ == "__main__":
    import os
    # Flask app context - ensure we have a database session
    from app import app
    with app.app_context():
        main()