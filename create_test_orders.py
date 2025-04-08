#!/usr/bin/env python
"""
Script to create test orders for PyCommerce.

This script creates test orders for the Demo Store 1 tenant in PyCommerce.
These orders can be used to test the shipping notification functionality.
"""

import os
import sys
import logging
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project directory to Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import app context and database
from app import app, db
from models import Tenant, User, Order, OrderItem, Product

def create_test_user(email="testuser@example.com", password="password123"):
    """Create a test user if one doesn't exist."""
    with app.app_context():
        from werkzeug.security import generate_password_hash
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if user:
            logger.info(f"Test user already exists: {email}")
            return user
        
        # Create new user
        user = User(
            id=str(uuid.uuid4()),
            username=email.split('@')[0],
            email=email,
            password_hash=generate_password_hash(password),
            first_name="Test",
            last_name="User",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(user)
        db.session.commit()
        logger.info(f"Created test user: {email}")
        return user

def create_test_orders(tenant_slug="tech", user_email="testuser@example.com", num_orders=3):
    """Create test orders for a tenant."""
    with app.app_context():
        # Get tenant
        tenant = Tenant.query.filter_by(slug=tenant_slug).first()
        if not tenant:
            logger.error(f"Tenant not found: {tenant_slug}")
            return None
        
        # Get user - get it fresh from the database instead of using one from another session
        user = User.query.filter_by(email=user_email).first()
        if not user:
            logger.error(f"User not found: {user_email}")
            return None
        
        # Get products for tenant
        products = Product.query.filter_by(tenant_id=tenant.id).all()
        if not products:
            logger.error(f"No products found for tenant: {tenant_slug}")
            return None
        
        created_orders = []
        
        # Create orders
        for i in range(num_orders):
            order_id = str(uuid.uuid4())
            
            # Sample addresses
            shipping_address = {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "address1": f"{123 + i} Main St",
                "address2": f"Apt {i+1}",
                "city": "Springfield",
                "state": "IL",
                "postal_code": f"6290{i}",
                "country": "US",
                "phone": f"555-123-{i}000"
            }
            
            billing_address = shipping_address.copy()
            
            # Create order
            order = Order(
                id=order_id,
                tenant_id=tenant.id,
                customer_id=user.id,  # Use customer_id instead of user_id
                order_number=f"ORD-{str(uuid.uuid4())[:8].upper()}",
                status="paid",  # Start as paid so it's ready for shipment
                customer_email=user.email,
                customer_name=f"{user.first_name} {user.last_name}",
                customer_phone="555-123-4567",
                shipping_address_line1=shipping_address["address1"],
                shipping_address_line2=shipping_address["address2"],
                shipping_city=shipping_address["city"],
                shipping_state=shipping_address["state"],
                shipping_postal_code=shipping_address["postal_code"],
                shipping_country=shipping_address["country"],
                billing_address_line1=billing_address["address1"],
                billing_address_line2=billing_address["address2"],
                billing_city=billing_address["city"],
                billing_state=billing_address["state"],
                billing_postal_code=billing_address["postal_code"],
                billing_country=billing_address["country"],
                payment_method="credit_card",
                payment_transaction_id=f"TRANS-{str(uuid.uuid4())[:8].upper()}",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                total=0.0,  # Will calculate below
                is_paid=True,
                paid_at=datetime.utcnow()
            )
            
            db.session.add(order)
            db.session.flush()  # Flush to get the order ID
            
            # Add 1-3 random products to each order
            import random
            order_products = random.sample(products, min(3, len(products)))
            order_total = 0.0
            
            for product in order_products:
                quantity = random.randint(1, 3)
                item_price = product.price
                item_total = item_price * quantity
                order_total += item_total
                
                # Create order item
                order_item = OrderItem(
                    id=str(uuid.uuid4()),
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    price=item_price,
                    created_at=datetime.utcnow()
                )
                
                db.session.add(order_item)
            
            # Update order total
            order.total = order_total
            
            db.session.commit()
            logger.info(f"Created order {order.id} with {len(order_products)} items, total: ${order_total:.2f}")
            created_orders.append(order)
        
        return created_orders

if __name__ == "__main__":
    try:
        # Create test user
        user = create_test_user()
        user_email = user.email  # Store the email as a string
        
        # Create test orders - use the email string, not the user object
        orders = create_test_orders(tenant_slug="tech", user_email=user_email, num_orders=3)
        
        if orders:
            logger.info(f"Successfully created {len(orders)} test orders")
            for order in orders:
                logger.info(f"Order ID: {order.id}, Total: ${order.total:.2f}")
    except Exception as e:
        logger.error(f"Error creating test orders: {e}")