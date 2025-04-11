"""
Update existing orders with different statuses.

This script updates existing orders with a variety of statuses
(PENDING, PROCESSING, SHIPPED, DELIVERED, COMPLETED) to test
revenue calculations and ensure proper dashboard calculations.
"""
import logging
import random
from sqlalchemy import text
from app import db, app

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Different statuses to test (including the 3 that affect revenue calculations)
ORDER_STATUSES = ["PENDING", "PROCESSING", "SHIPPED", "DELIVERED", "COMPLETED"]

def update_order_statuses():
    """Update existing orders with different statuses."""
    with app.app_context():
        try:
            # Get all tenants
            tenant_result = db.session.execute(text("SELECT id, name, slug FROM tenants")).fetchall()
            tenants = [{"id": str(row[0]), "name": row[1], "slug": row[2]} for row in tenant_result]
            
            if not tenants:
                logger.error("No tenants found in the database")
                return
                
            logger.info(f"Found {len(tenants)} tenants")
            
            total_orders_updated = 0
            
            # For each tenant, update order statuses
            for tenant in tenants:
                tenant_id = tenant["id"]
                tenant_name = tenant["name"]
                
                # Get orders for this tenant
                order_result = db.session.execute(
                    text("SELECT id, status FROM orders WHERE tenant_id = :tenant_id"),
                    {"tenant_id": tenant_id}
                ).fetchall()
                
                if not order_result:
                    logger.warning(f"No orders found for tenant: {tenant_name}")
                    continue
                
                orders = [{"id": str(row[0]), "status": row[1]} for row in order_result]
                logger.info(f"Found {len(orders)} orders for tenant: {tenant_name}")
                
                # For categories, we want orders with different statuses
                # First, check if we have product categories in the database
                category_result = db.session.execute(
                    text("SELECT DISTINCT c.id, c.name FROM categories c JOIN product_categories pc ON c.id = pc.category_id WHERE c.tenant_id = :tenant_id"),
                    {"tenant_id": tenant_id}
                ).fetchall()
                
                if not category_result:
                    logger.warning(f"No product categories found for tenant: {tenant_name}")
                    # Distribute statuses randomly across all orders
                    orders_updated = update_random_orders(orders, tenant_name)
                    total_orders_updated += orders_updated
                    continue
                
                categories = [{"id": str(row[0]), "name": row[1]} for row in category_result]
                logger.info(f"Found {len(categories)} product categories for tenant: {tenant_name}")
                
                # Try to distribute statuses by product category
                try:
                    orders_by_category = {}
                    
                    for category in categories:
                        category_id = category["id"]
                        category_name = category["name"]
                        
                        # Find orders with products in this category
                        order_ids_result = db.session.execute(
                            text("""
                            SELECT DISTINCT o.id 
                            FROM orders o
                            JOIN order_items oi ON o.id = oi.order_id
                            JOIN product_categories pc ON oi.product_id = pc.product_id
                            WHERE o.tenant_id = :tenant_id
                            AND pc.category_id = :category_id
                            """),
                            {"tenant_id": tenant_id, "category_id": category_id}
                        ).fetchall()
                        
                        if not order_ids_result:
                            logger.warning(f"No orders found for category: {category_name}")
                            continue
                        
                        category_order_ids = [str(row[0]) for row in order_ids_result]
                        orders_by_category[category_name] = category_order_ids
                        
                        logger.info(f"Found {len(category_order_ids)} orders for category: {category_name}")
                    
                    # Update orders by category
                    if orders_by_category:
                        orders_updated = update_orders_by_category(orders_by_category, tenant_name)
                        total_orders_updated += orders_updated
                    else:
                        # Fallback to random distribution if no category mapping found
                        logger.warning(f"No category to order mappings found for tenant: {tenant_name}")
                        orders_updated = update_random_orders(orders, tenant_name)
                        total_orders_updated += orders_updated
                        
                except Exception as e:
                    logger.error(f"Error updating orders by category: {str(e)}")
                    # Fallback to random distribution
                    orders_updated = update_random_orders(orders, tenant_name)
                    total_orders_updated += orders_updated
            
            logger.info(f"Total orders updated: {total_orders_updated}")
            
        except Exception as e:
            logger.error(f"Error updating order statuses: {str(e)}")
            raise

def update_orders_by_category(orders_by_category, tenant_name):
    """
    Update orders with different statuses by category.
    
    For each category, we'll try to have at least one order with each status.
    """
    orders_updated = 0
    
    for category_name, order_ids in orders_by_category.items():
        logger.info(f"Updating {len(order_ids)} orders for category: {category_name}")
        
        # If we have enough orders, assign one to each status
        if len(order_ids) >= len(ORDER_STATUSES):
            # Shuffle the orders to randomize which ones get which status
            random.shuffle(order_ids)
            
            # Assign statuses
            for i, status in enumerate(ORDER_STATUSES):
                order_id = order_ids[i]
                update_order_status(order_id, status)
                orders_updated += 1
                
            # Randomly assign the rest if there are more orders than statuses
            for i in range(len(ORDER_STATUSES), len(order_ids)):
                order_id = order_ids[i]
                status = random.choice(ORDER_STATUSES)
                update_order_status(order_id, status)
                orders_updated += 1
        else:
            # Not enough orders for each status, so assign random statuses
            for order_id in order_ids:
                status = random.choice(ORDER_STATUSES)
                update_order_status(order_id, status)
                orders_updated += 1
    
    logger.info(f"Updated {orders_updated} orders by category for tenant: {tenant_name}")
    return orders_updated

def update_random_orders(orders, tenant_name):
    """
    Update orders with different statuses randomly.
    
    This is a fallback method when category-based assignment isn't possible.
    """
    orders_updated = 0
    order_ids = [order["id"] for order in orders]
    
    # If we have enough orders, make sure we have at least one with each status
    if len(order_ids) >= len(ORDER_STATUSES):
        # Shuffle the orders to randomize which ones get which status
        random.shuffle(order_ids)
        
        # Assign statuses
        for i, status in enumerate(ORDER_STATUSES):
            order_id = order_ids[i]
            update_order_status(order_id, status)
            orders_updated += 1
            
        # Randomly assign the rest if there are more orders than statuses
        for i in range(len(ORDER_STATUSES), len(order_ids)):
            order_id = order_ids[i]
            status = random.choice(ORDER_STATUSES)
            update_order_status(order_id, status)
            orders_updated += 1
    else:
        # Not enough orders for each status, so assign random statuses
        for order_id in order_ids:
            status = random.choice(ORDER_STATUSES)
            update_order_status(order_id, status)
            orders_updated += 1
    
    logger.info(f"Updated {orders_updated} orders randomly for tenant: {tenant_name}")
    return orders_updated

def update_order_status(order_id, status):
    """Update a single order's status."""
    try:
        db.session.execute(
            text("UPDATE orders SET status = :status WHERE id = :order_id"),
            {"status": status, "order_id": order_id}
        )
        db.session.commit()
        logger.info(f"Updated order {order_id} with status: {status}")
        return True
    except Exception as e:
        logger.error(f"Error updating order {order_id}: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    update_order_statuses()