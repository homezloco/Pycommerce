#!/usr/bin/env python
"""
Script to create test orders for PyCommerce.

This script creates test orders for the Demo Store 1 tenant in PyCommerce.
These orders can be used to test the shipping notification functionality.
It generates orders with different statuses, types, and full customer data.
"""

import os
import sys
import logging
import uuid
import random
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project directory to Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import app context and database
from app import app, db
from models import Tenant, User, Order, OrderItem, Product

# Import the OrderType enum from the main Order module
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pycommerce'))
try:
    from pycommerce.models.order import OrderType, OrderStatus
    HAS_ORDER_ENUMS = True
except ImportError:
    logger.warning("Could not import OrderType and OrderStatus enums from pycommerce, will use string values")
    HAS_ORDER_ENUMS = False

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
        
        # Create more users for diverse orders
        additional_users = [
            {
                "email": f"testuser{i}@example.com",
                "first_name": f"Test{i}",
                "last_name": f"User{i}",
                "password": "password123",
                "phone": f"555-{100+i}-{1000+i}"
            } for i in range(1, 4)
        ]
        
        for user_data in additional_users:
            existing_user = User.query.filter_by(email=user_data["email"]).first()
            if not existing_user:
                from werkzeug.security import generate_password_hash
                new_user = User(
                    id=str(uuid.uuid4()),
                    username=user_data["email"].split('@')[0],
                    email=user_data["email"],
                    password_hash=generate_password_hash(user_data["password"]),
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(new_user)
                db.session.commit()
                logger.info(f"Created additional test user: {user_data['email']}")
        
        # Define possible order types
        order_types = ["TEST", "STANDARD", "SUBSCRIPTION", "WHOLESALE", "BACKORDER", "PREORDER", "GIFT", "EXPEDITED", "INTERNATIONAL"]
        
        # Define possible order statuses
        order_statuses = ["PENDING", "PROCESSING", "PAID", "SHIPPED", "DELIVERED", "COMPLETED", "CANCELLED", "REFUNDED"]
        
        # Define possible payment methods
        payment_methods = ["credit_card", "paypal", "stripe", "bank_transfer", "cash_on_delivery", "crypto"]
        
        created_orders = []
        
        # Create orders
        for i in range(num_orders):
            order_id = str(uuid.uuid4())
            
            # Select a user for this order (the original user or one of the additional ones)
            if i == 0:
                order_user = user  # Use the primary test user for the first order
            else:
                # For subsequent orders, randomly select from all users
                all_users = [user] + list(User.query.filter(User.email.like("testuser%@example.com"), User.email != user_email).all())
                order_user = random.choice(all_users)
            
            # Generate a realistic order date (within the last 30 days)
            order_date = datetime.utcnow() - timedelta(days=random.randint(0, 30), 
                                                      hours=random.randint(0, 23),
                                                      minutes=random.randint(0, 59))
            
            # Sample addresses with variations to test different scenarios
            state_codes = ["CA", "NY", "TX", "IL", "FL", "WA"]
            countries = ["US", "US", "CA", "MX", "GB", "DE"] # Weight towards US addresses
            
            shipping_address = {
                "first_name": order_user.first_name,
                "last_name": order_user.last_name,
                "address1": f"{100 + i * 11} {random.choice(['Main', 'Oak', 'Maple', 'Pine', 'Cedar'])} {random.choice(['St', 'Ave', 'Blvd', 'Ln', 'Dr'])}",
                "address2": random.choice([f"Apt {i+1}", f"Suite {i*10+100}", f"Unit {chr(65+i)}", ""]),
                "city": random.choice(["Springfield", "Riverside", "Franklin", "Greenville", "Clinton"]),
                "state": random.choice(state_codes),
                "postal_code": f"{random.randint(10000, 99999)}",
                "country": random.choice(countries),
                "phone": getattr(order_user, 'phone', f"555-{100+i}-{1000+i}")
            }
            
            # For some orders, make billing address different from shipping
            if i % 3 == 0:  # Every third order has different billing address
                billing_address = {
                    "first_name": order_user.first_name,
                    "last_name": order_user.last_name,
                    "address1": f"{200 + i * 15} {random.choice(['Elm', 'Willow', 'Birch', 'Aspen'])} {random.choice(['St', 'Ave', 'Rd', 'Way'])}",
                    "address2": random.choice([f"Floor {i+1}", f"Suite {i*5+200}", "", ""]),
                    "city": random.choice(["Millfield", "Lakeside", "Georgetown", "Bristol", "Newport"]),
                    "state": random.choice(state_codes),
                    "postal_code": f"{random.randint(10000, 99999)}",
                    "country": "US",  # Usually billing is domestic
                    "phone": getattr(order_user, 'phone', f"555-{100+i}-{2000+i}")
                }
            else:
                billing_address = shipping_address.copy()
            
            # Select order type - for this test, let's make 1/3 of orders TEST type
            if i < num_orders / 3:
                order_type = "TEST"
            else:
                # Exclude TEST from the random selection for the remaining orders
                order_type = random.choice([t for t in order_types if t != "TEST"])
            
            # Select order status - distribute across different statuses
            status_index = i % len(order_statuses)
            order_status = order_statuses[status_index]
            
            # Create order with diverse properties
            order_args = {
                "id": order_id,
                "tenant_id": tenant.id,
                "customer_id": order_user.id,
                "order_number": f"ORD-{order_date.strftime('%y%m%d')}-{str(uuid.uuid4())[:6].upper()}",
                "status": order_status,  # Using our calculated status
                "customer_email": order_user.email,
                "customer_name": f"{order_user.first_name} {order_user.last_name}" if order_user.first_name and order_user.last_name else order_user.username,
                "customer_phone": getattr(order_user, 'phone', f"555-{100+i}-{1000+i}"),
                
                # Shipping information
                "shipping_address_line1": shipping_address["address1"],
                "shipping_address_line2": shipping_address["address2"],
                "shipping_city": shipping_address["city"],
                "shipping_state": shipping_address["state"],
                "shipping_postal_code": shipping_address["postal_code"],
                "shipping_country": shipping_address["country"],
                
                # Billing information
                "billing_address_line1": billing_address["address1"],
                "billing_address_line2": billing_address["address2"],
                "billing_city": billing_address["city"],
                "billing_state": billing_address["state"],
                "billing_postal_code": billing_address["postal_code"],
                "billing_country": billing_address["country"],
                
                # Payment information
                "payment_method": random.choice(payment_methods),
                "payment_transaction_id": f"TRANS-{str(uuid.uuid4())[:8].upper()}",
                "created_at": order_date,
                "updated_at": order_date + timedelta(minutes=random.randint(5, 60)),
                
                # Initial values for financial fields (will be calculated below)
                "total": 0.0,
                "subtotal": 0.0,
                "tax": 0.0,
                "shipping_cost": random.choice([5.0, 10.0, 15.0, 25.0]),  # Variable shipping costs
                "discount": random.choice([0.0, 0.0, 5.0, 10.0, 15.0]),  # Some orders have discounts
            }
            
            # Set payment status based on order status
            is_paid = order_status in ["PAID", "SHIPPED", "DELIVERED", "COMPLETED"]
            order_args["is_paid"] = is_paid
            if is_paid:
                order_args["paid_at"] = order_date + timedelta(minutes=random.randint(5, 30))
            
            # Set shipping status fields for shipped orders
            if order_status in ["SHIPPED", "DELIVERED", "COMPLETED"]:
                order_args["tracking_number"] = f"TRK{random.randint(1000000, 9999999)}"
                order_args["shipping_carrier"] = random.choice(["FedEx", "UPS", "USPS", "DHL"])
                order_args["shipped_at"] = order_date + timedelta(days=random.randint(1, 3))
                
                if order_status in ["DELIVERED", "COMPLETED"]:
                    order_args["delivered_at"] = order_args["shipped_at"] + timedelta(days=random.randint(1, 5))
            
            # Check if order_type column exists in the database
            with app.app_context():
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                columns = [column['name'] for column in inspector.get_columns('orders')]
                has_order_type = 'order_type' in columns
                
                if has_order_type:
                    logger.info("Database has order_type column, setting order type")
                    try:
                        # Allow for either enum or string value
                        if HAS_ORDER_ENUMS and hasattr(OrderType, order_type):
                            order_args["order_type"] = getattr(OrderType, order_type)
                        else:
                            # If we can't use the enum, try with string (may or may not work depending on schema)
                            order_args["order_type"] = order_type
                    except (KeyError, AttributeError):
                        logger.warning(f"Couldn't set order_type to {order_type}, field may not exist")
                else:
                    logger.info("Database does not have order_type column, skipping order type")
            
            # Create the order with our arguments
            try:
                order = Order(**order_args)
                db.session.add(order)
                db.session.flush()  # Flush to get the order ID
            except Exception as e:
                logger.error(f"Error creating order: {e}")
                continue
            
            # Add 1-3 random products to each order
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
            
            # Update order subtotal and total
            order.subtotal = order_total
            # Calculate tax (let's assume 8% tax rate)
            tax_rate = 0.08
            tax_amount = round(order_total * tax_rate, 2)
            order.tax = tax_amount
            
            # Total includes subtotal, tax, and shipping, minus discounts
            order.total = order.subtotal + order.tax + order.shipping_cost - order.discount
            
            db.session.commit()
            logger.info(f"Created order {order.id} with {len(order_products)} items, subtotal: ${order.subtotal:.2f}, total: ${order.total:.2f}")
            created_orders.append(order)
        
        return created_orders

if __name__ == "__main__":
    try:
        # Create test user
        user = create_test_user()
        if not user:
            logger.error("Failed to create or retrieve test user")
            exit(1)
            
        user_email = user.email  # Store the email as a string
        
        # Create test orders - use the email string, not the user object
        try:
            orders = create_test_orders(tenant_slug="tech", user_email=user_email, num_orders=9)
            
            if orders:
                # Get only the IDs to avoid session issues
                order_count = len(orders)
                try:
                    # Try to safely extract IDs
                    order_ids = []
                    for order in orders:
                        try:
                            order_ids.append(str(order.id))
                        except:
                            pass
                    
                    logger.info(f"Successfully created {order_count} test orders")
                    if order_ids:
                        logger.info(f"Order IDs: {', '.join(order_ids)}")
                except Exception as e:
                    # Even if this fails, we know orders were created from earlier logs
                    logger.info(f"Successfully created {order_count} test orders (IDs not available)")
                    logger.debug(f"Error accessing order details: {e}")
        except Exception as e:
            logger.error(f"Error during order creation: {e}")
    except Exception as e:
        logger.error(f"Error in main process: {e}")