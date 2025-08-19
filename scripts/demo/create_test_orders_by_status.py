"""
Create test orders with different statuses.

This script creates test orders with various statuses (PENDING, PROCESSING,
SHIPPED, DELIVERED, COMPLETED) to test revenue calculations that should only
include SHIPPED, DELIVERED, and COMPLETED orders.
"""
import logging
import random
from datetime import datetime, timedelta
import uuid
from sqlalchemy import text

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_orders():
    """Create test orders with different statuses."""
    try:
        from app import db, app
        
        with app.app_context():
            # Get tenant IDs
            tenant_result = db.session.execute(text("SELECT id, name, slug FROM tenants")).fetchall()
            tenants = [{"id": str(row[0]), "name": row[1], "slug": row[2]} for row in tenant_result]
            
            if not tenants:
                logger.error("No tenants found in the database")
                return
                
            logger.info(f"Found {len(tenants)} tenants")
            
            # Get a user ID to associate with orders
            user_result = db.session.execute(text("SELECT id FROM users LIMIT 1")).fetchone()
            if not user_result:
                logger.error("No users found in the database")
                return
                
            user_id = str(user_result[0])
            logger.info(f"Using user ID: {user_id}")
            
            # Status to test (these affect revenue calculations)
            statuses = ["PENDING", "PROCESSING", "SHIPPED", "DELIVERED", "COMPLETED"]
            
            total_orders = 0
            
            # Process each tenant
            for tenant in tenants:
                tenant_id = tenant["id"]
                
                # Get products for this tenant
                product_result = db.session.execute(
                    text("SELECT id, name, price FROM products WHERE tenant_id = :tenant_id"),
                    {"tenant_id": tenant_id}
                ).fetchall()
                
                if not product_result:
                    logger.warning(f"No products found for tenant {tenant['name']}")
                    continue
                    
                products = [{"id": str(row[0]), "name": row[1], "price": float(row[2])} for row in product_result]
                logger.info(f"Found {len(products)} products for tenant {tenant['name']}")
                
                # Get categories for this tenant
                category_result = db.session.execute(
                    text("SELECT id, name FROM categories WHERE tenant_id = :tenant_id"),
                    {"tenant_id": tenant_id}
                ).fetchall()
                
                if not category_result:
                    logger.warning(f"No categories found for tenant {tenant['name']}")
                    # Create at least one test category
                    cat_id = str(uuid.uuid4())
                    db.session.execute(
                        text("INSERT INTO categories (id, name, tenant_id) VALUES (:id, :name, :tenant_id)"),
                        {"id": cat_id, "name": "Test Category", "tenant_id": tenant_id}
                    )
                    db.session.commit()
                    categories = [{"id": cat_id, "name": "Test Category"}]
                else:
                    categories = [{"id": str(row[0]), "name": row[1]} for row in category_result]
                    
                logger.info(f"Found {len(categories)} categories for tenant {tenant['name']}")
                
                # Make sure each product is assigned to at least one category
                for product in products:
                    product_id = product["id"]
                    
                    # Check if product already has categories
                    cat_check = db.session.execute(
                        text("SELECT category_id FROM product_categories WHERE product_id = :product_id"),
                        {"product_id": product_id}
                    ).fetchone()
                    
                    if not cat_check and categories:
                        # Assign product to a random category
                        category = random.choice(categories)
                        
                        db.session.execute(
                            text("""
                            INSERT INTO product_categories (product_id, category_id) 
                            VALUES (:product_id, :category_id)
                            """),
                            {"product_id": product_id, "category_id": category["id"]}
                        )
                        logger.info(f"Assigned product {product['name']} to category {category['name']}")
                        db.session.commit()
                
                # Create orders with different statuses for this tenant
                for status in statuses:
                    # Create 2 orders with each status for more testing data
                    for _ in range(2):
                        # Skip if no products
                        if not products:
                            continue
                            
                        # Create order
                        order_id = str(uuid.uuid4())
                        created_at = datetime.now() - timedelta(days=random.randint(1, 30))
                        reference = f"TST-{uuid.uuid4().hex[:6].upper()}"
                        
                        # Add 1-3 items to the order
                        num_items = random.randint(1, 3)
                        order_items = []
                        
                        order_total = 0
                        
                        for _ in range(num_items):
                            product = random.choice(products)
                            quantity = random.randint(1, 5)
                            price = product["price"]
                            item_total = price * quantity
                            order_total += item_total
                            
                            order_items.append({
                                "id": str(uuid.uuid4()),
                                "product_id": product["id"],
                                "name": product["name"],
                                "quantity": quantity,
                                "price": price,
                                "total": item_total
                            })
                        
                        # Insert the order
                        db.session.execute(
                            text("""
                            INSERT INTO orders (
                                id, tenant_id, user_id, status, type, 
                                created_at, updated_at, total, reference,
                                shipping_address_line1, shipping_city, shipping_state, 
                                shipping_postal_code, shipping_country, 
                                billing_address_line1, billing_city, billing_state, 
                                billing_postal_code, billing_country,
                                customer_name, customer_email, customer_phone, 
                                payment_method, payment_status, notes
                            ) VALUES (
                                :id, :tenant_id, :user_id, :status, :type, 
                                :created_at, :updated_at, :total, :reference,
                                :shipping_address_line1, :shipping_city, :shipping_state, 
                                :shipping_postal_code, :shipping_country, 
                                :billing_address_line1, :billing_city, :billing_state, 
                                :billing_postal_code, :billing_country,
                                :customer_name, :customer_email, :customer_phone, 
                                :payment_method, :payment_status, :notes
                            )
                            """),
                            {
                                "id": order_id,
                                "tenant_id": tenant_id,
                                "user_id": user_id,
                                "status": status,
                                "type": "STANDARD",
                                "created_at": created_at,
                                "updated_at": created_at,
                                "total": order_total,
                                "reference": reference,
                                "shipping_address_line1": "123 Test Street",
                                "shipping_city": "Test City",
                                "shipping_state": "TS",
                                "shipping_postal_code": "12345",
                                "shipping_country": "Test Country",
                                "billing_address_line1": "123 Test Street",
                                "billing_city": "Test City",
                                "billing_state": "TS",
                                "billing_postal_code": "12345",
                                "billing_country": "Test Country",
                                "customer_name": "Test User",
                                "customer_email": "testuser@example.com",
                                "customer_phone": "555-123-4567",
                                "payment_method": "credit_card",
                                "payment_status": "PAID",
                                "notes": f"Test order with status {status}"
                            }
                        )
                        
                        # Insert order items
                        for item in order_items:
                            db.session.execute(
                                text("""
                                INSERT INTO order_items (
                                    id, order_id, product_id, quantity, price, total, name
                                ) VALUES (
                                    :id, :order_id, :product_id, :quantity, :price, :total, :name
                                )
                                """),
                                {
                                    "id": item["id"],
                                    "order_id": order_id,
                                    "product_id": item["product_id"],
                                    "quantity": item["quantity"],
                                    "price": item["price"],
                                    "total": item["total"],
                                    "name": item["name"]
                                }
                            )
                        
                        db.session.commit()
                        logger.info(f"Created order {reference} with status {status} for tenant {tenant['name']}")
                        total_orders += 1
            
            logger.info(f"Created {total_orders} test orders across all tenants")
    
    except Exception as e:
        logger.error(f"Error creating test orders: {str(e)}")
        raise

if __name__ == "__main__":
    create_test_orders()