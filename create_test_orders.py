#!/usr/bin/env python
"""
Script to create test orders for PyCommerce.

This script creates test orders for the Tech tenant in PyCommerce.
These orders can be used to test the shipping notification functionality.
It generates orders with different statuses, types, and full customer data.
"""

import logging
import random
from datetime import datetime, timedelta
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_user(email="testuser@example.com", password="password123"):
    """Create a test user if one doesn't exist."""
    from app import app, db
    from models import User
    from werkzeug.security import generate_password_hash
    
    with app.app_context():
        # Check if user exists
        user = db.session.query(User).filter_by(email=email).first()
        if user:
            logger.info(f"Test user already exists: {email}")
            return user.id
            
        # Create test user
        user_id = str(uuid.uuid4())
        new_user = User(
            id=user_id,
            email=email,
            username=email.split('@')[0],
            password_hash=generate_password_hash(password),
            is_active=True,
            first_name="Test",
            last_name="User"
        )
        db.session.add(new_user)
        db.session.commit()
        logger.info(f"Created test user: {email} with ID {user_id}")
        return user_id

def create_test_orders(tenant_slug="tech", user_email="testuser@example.com", num_orders=9):
    """
    Create test orders for a tenant with various order types and statuses.
    
    This function creates a mix of different order types and statuses to
    test all aspects of the order management system.
    
    Args:
        tenant_slug: Slug of the tenant to create orders for
        user_email: Email of the user to associate orders with
        num_orders: Number of orders to create (default: 9 to test different combinations)
        
    Returns:
        List of created orders
    """
    from app import app, db
    from sqlalchemy import text
    
    # Create a test user
    user_id = create_test_user(user_email)
    
    with app.app_context():
        # Get tenant ID
        tenant_result = db.session.execute(
            text("SELECT id FROM tenants WHERE slug = :slug"),
            {"slug": tenant_slug}
        ).fetchone()
        
        if not tenant_result:
            logger.error(f"Tenant not found with slug: {tenant_slug}")
            return []
        
        tenant_id = tenant_result[0]
        logger.info(f"Found tenant {tenant_slug} with ID: {tenant_id}")
        
        # Get available products
        products = db.session.execute(
            text("SELECT id, name, price FROM products WHERE tenant_id = :tenant_id"),
            {"tenant_id": tenant_id}
        ).fetchall()
        
        if not products:
            logger.error(f"No products found for tenant: {tenant_slug}")
            return []
        
        logger.info(f"Found {len(products)} products for tenant")
        
        # Create orders
        created_orders = []
        
        order_statuses = ["pending", "processing", "shipped", "delivered", "cancelled", "refunded"]
        order_types = ["STANDARD", "EXPRESS", "INTERNATIONAL"]
        
        for i in range(num_orders):
            # Create random order date within last 30 days
            days_ago = random.randint(0, 29)
            order_date = datetime.utcnow() - timedelta(days=days_ago)
            
            # Pick random status
            status = order_statuses[i % len(order_statuses)]
            
            # Pick random type
            order_type = order_types[i % len(order_types)]
            
            # Generate order ID and number
            order_id = str(uuid.uuid4())
            order_number = f"ORD-{order_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            
            # Add 1-4 random products to order
            num_items = random.randint(1, 4)
            order_items = []
            
            # Select random products
            for _ in range(num_items):
                product = random.choice(products)
                product_id = product[0]
                product_price = float(product[2])
                quantity = random.randint(1, 3)
                
                order_items.append({
                    "id": str(uuid.uuid4()),
                    "product_id": product_id,
                    "price": product_price,
                    "quantity": quantity
                })
            
            # Calculate totals
            subtotal = sum(item["price"] * item["quantity"] for item in order_items)
            tax = round(subtotal * 0.08, 2)  # 8% tax
            shipping = round(10.0 if order_type == "STANDARD" else 20.0, 2)
            total = round(subtotal + tax + shipping, 2)
            
            # Create timestamps based on status
            shipped_at = None
            delivered_at = None
            paid_at = None
            
            if status in ["shipped", "delivered"]:
                shipped_at = order_date + timedelta(hours=random.randint(2, 48))
                
            if status == "delivered":
                delivered_at = shipped_at + timedelta(hours=random.randint(24, 72))
                
            if status not in ["pending", "cancelled"]:
                paid_at = order_date + timedelta(minutes=random.randint(10, 120))
            
            # Create order in database
            db.session.execute(
                text("""
                    INSERT INTO orders (
                        id, tenant_id, customer_id, order_number, status, order_type,
                        total, subtotal, tax, shipping_cost, discount,
                        customer_email, customer_name, customer_phone,
                        shipping_address_line1, shipping_city, shipping_state, shipping_postal_code, shipping_country,
                        billing_address_line1, billing_city, billing_state, billing_postal_code, billing_country,
                        payment_method, payment_transaction_id, is_paid, paid_at,
                        tracking_number, shipping_carrier, shipped_at, delivered_at,
                        created_at, updated_at
                    )
                    VALUES (
                        :id, :tenant_id, :customer_id, :order_number, :status, :order_type,
                        :total, :subtotal, :tax, :shipping_cost, :discount,
                        :customer_email, :customer_name, :customer_phone,
                        :shipping_address_line1, :shipping_city, :shipping_state, :shipping_postal_code, :shipping_country,
                        :billing_address_line1, :billing_city, :billing_state, :billing_postal_code, :billing_country,
                        :payment_method, :payment_transaction_id, :is_paid, :paid_at,
                        :tracking_number, :shipping_carrier, :shipped_at, :delivered_at,
                        :created_at, :updated_at
                    )
                """),
                {
                    "id": order_id,
                    "tenant_id": tenant_id,
                    "customer_id": user_id,
                    "order_number": order_number,
                    "status": status,
                    "order_type": order_type,
                    "total": total,
                    "subtotal": subtotal,
                    "tax": tax,
                    "shipping_cost": shipping,
                    "discount": 0,
                    "customer_email": user_email,
                    "customer_name": "Test User",
                    "customer_phone": "555-123-4567",
                    "shipping_address_line1": "123 Main St",
                    "shipping_city": "Anytown",
                    "shipping_state": "CA",
                    "shipping_postal_code": "12345",
                    "shipping_country": "USA",
                    "billing_address_line1": "123 Main St",
                    "billing_city": "Anytown",
                    "billing_state": "CA",
                    "billing_postal_code": "12345",
                    "billing_country": "USA",
                    "payment_method": "credit_card",
                    "payment_transaction_id": f"txn_{uuid.uuid4().hex[:10]}",
                    "is_paid": status not in ["pending", "cancelled"],
                    "paid_at": paid_at,
                    "tracking_number": f"TRK{random.randint(10000, 99999)}" if status in ["shipped", "delivered"] else None,
                    "shipping_carrier": "TestShipper" if status in ["shipped", "delivered"] else None,
                    "shipped_at": shipped_at,
                    "delivered_at": delivered_at,
                    "created_at": order_date,
                    "updated_at": datetime.utcnow()
                }
            )
            
            # Add order items
            for item in order_items:
                db.session.execute(
                    text("""
                        INSERT INTO order_items (id, order_id, product_id, quantity, price, created_at)
                        VALUES (:id, :order_id, :product_id, :quantity, :price, :created_at)
                    """),
                    {
                        "id": item["id"],
                        "order_id": order_id,
                        "product_id": item["product_id"],
                        "quantity": item["quantity"],
                        "price": item["price"],
                        "created_at": order_date
                    }
                )
            
            # Check if the order_notes table has the author column
            has_author_column = False
            try:
                column_check = db.session.execute(
                    text("SELECT column_name FROM information_schema.columns WHERE table_name = 'order_notes' AND column_name = 'author'")
                ).fetchone()
                has_author_column = column_check is not None
            except Exception as e:
                logger.warning(f"Could not check order_notes schema: {e}")
                
            # Add a note based on schema
            note_id = str(uuid.uuid4())
            if has_author_column:
                db.session.execute(
                    text("""
                        INSERT INTO order_notes (id, order_id, content, author, is_customer_visible, created_at)
                        VALUES (:id, :order_id, :content, :author, :is_customer_visible, :created_at)
                    """),
                    {
                        "id": note_id,
                        "order_id": order_id,
                        "content": f"Test note for {status} order",
                        "author": "System",
                        "is_customer_visible": False,
                        "created_at": order_date
                    }
                )
            else:
                # Try without author column
                db.session.execute(
                    text("""
                        INSERT INTO order_notes (id, order_id, content, is_customer_visible, created_at)
                        VALUES (:id, :order_id, :content, :is_customer_visible, :created_at)
                    """),
                    {
                        "id": note_id,
                        "order_id": order_id,
                        "content": f"Test note for {status} order",
                        "is_customer_visible": False,
                        "created_at": order_date
                    }
                )
            
            created_orders.append({
                "id": order_id,
                "order_number": order_number,
                "status": status,
                "type": order_type,
                "total": total,
                "created_at": order_date
            })
            
            logger.info(f"Created {status} {order_type} order: {order_number} with {len(order_items)} items, total: ${total}")
        
        # Commit all changes
        db.session.commit()
        logger.info(f"Successfully created {len(created_orders)} test orders")
        
        return created_orders

if __name__ == "__main__":
    try:
        logger.info("Starting test order creation")
        orders = create_test_orders()
        logger.info(f"Created {len(orders)} test orders")
    except Exception as e:
        logger.error(f"Error creating test orders: {str(e)}")