"""
Script to create test orders with different statuses for each category.

This script creates test orders for products in different categories
with a variety of order statuses: PENDING, PROCESSING, SHIPPED, DELIVERED, and COMPLETED.
This helps test the revenue calculations which should only include SHIPPED, DELIVERED, and COMPLETED orders.
"""
import logging
import random
from datetime import datetime, timedelta
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import necessary modules
try:
    from pycommerce.models.tenant import TenantManager
    from pycommerce.models.product import ProductManager
    from pycommerce.models.order import OrderManager, OrderStatus, OrderType
    from pycommerce.models.category import CategoryManager
    # We'll use direct database access instead of the UserManager
except ImportError as e:
    logger.error(f"Error importing modules: {str(e)}")
    raise

def create_or_get_test_user(email="testuser@example.com", password="password123"):
    """Get an existing test user or create one using direct database access."""
    try:
        # Try to directly use the app context and SQLAlchemy
        from app import db, app
        from models import User
        from sqlalchemy import text
        
        with app.app_context():
            # Check if user exists
            user = db.session.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email}).fetchone()
            
            if not user:
                # Create a new user
                from werkzeug.security import generate_password_hash
                
                logger.info(f"Creating test user with email: {email}")
                hashed_password = generate_password_hash(password)
                
                result = db.session.execute(
                    text("""
                    INSERT INTO users (email, username, password_hash, name, active) 
                    VALUES (:email, :username, :password_hash, :name, :active)
                    RETURNING id
                    """),
                    {
                        "email": email,
                        "username": email.split("@")[0],
                        "password_hash": hashed_password,
                        "name": "Test User",
                        "active": True
                    }
                )
                
                user_id = result.fetchone()[0]
                db.session.commit()
                
                logger.info(f"Created test user with ID: {user_id}")
                
                # Create a simple user object with just the ID for our purposes
                class SimpleUser:
                    def __init__(self, id):
                        self.id = id
                
                return SimpleUser(user_id)
            else:
                # User exists, return a simple object with the ID
                user_id = user[0]  # Assuming ID is first column
                logger.info(f"Using existing test user with ID: {user_id}")
                
                class SimpleUser:
                    def __init__(self, id):
                        self.id = id
                
                return SimpleUser(user_id)
    except Exception as e:
        logger.error(f"Error creating/getting test user: {str(e)}")
        
        # Return a placeholder user ID that should work with existing orders
        logger.warning("Using placeholder user ID for test orders")
        class SimpleUser:
            def __init__(self, id):
                self.id = id
        
        return SimpleUser("1")

def get_products_by_category(tenant_id):
    """Group products by their categories."""
    product_manager = ProductManager()
    category_manager = CategoryManager()
    
    products = product_manager.get_by_tenant(tenant_id)
    
    products_by_category = {}
    
    for product in products:
        # Get categories for this product
        try:
            categories = category_manager.get_product_categories(product.id)
            
            # If product has no categories assigned, skip it
            if not categories:
                continue
                
            # Add product to each of its categories
            for category in categories:
                category_name = category.name if hasattr(category, 'name') else str(category)
                
                if category_name not in products_by_category:
                    products_by_category[category_name] = []
                    
                products_by_category[category_name].append(product)
        except Exception as e:
            logger.warning(f"Error getting categories for product {product.id}: {str(e)}")
    
    return products_by_category

def create_order(tenant_id, product, status, user_id, order_type=OrderType.STANDARD):
    """Create a test order with the given product and status using direct database access."""
    try:
        from app import db, app
        from sqlalchemy import text
        import json
        
        # Generate random order details
        order_date = datetime.now() - timedelta(days=random.randint(1, 90))
        quantity = random.randint(1, 5)
        
        # Create a unique order reference and ID
        order_ref = f"TST-{uuid.uuid4().hex[:6].upper()}"
        order_id = str(uuid.uuid4())
        
        # Convert order type and status to string if they're enums
        if not isinstance(order_type, str):
            order_type = str(order_type.name if hasattr(order_type, 'name') else order_type)
        
        if not isinstance(status, str):
            status = str(status.name if hasattr(status, 'name') else status)
        
        # Calculate total
        item_total = quantity * float(product.price)
        
        with app.app_context():
            # Insert order into the database
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
                    "type": order_type,
                    "created_at": order_date,
                    "updated_at": order_date,
                    "total": item_total,
                    "reference": order_ref,
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
                    "notes": f"Test order with status {status} for product {product.name}"
                }
            )
            
            # Create order item
            item_id = str(uuid.uuid4())
            
            db.session.execute(
                text("""
                INSERT INTO order_items (
                    id, order_id, product_id, quantity, price, total, name
                ) VALUES (
                    :id, :order_id, :product_id, :quantity, :price, :total, :name
                )
                """),
                {
                    "id": item_id,
                    "order_id": order_id,
                    "product_id": str(product.id),
                    "quantity": quantity,
                    "price": float(product.price),
                    "total": item_total,
                    "name": product.name
                }
            )
            
            # Commit transaction
            db.session.commit()
            
            logger.info(f"Created order {order_id} with status {status} for product {product.name}")
            
            # Create a simple order object for return value
            class SimpleOrder:
                def __init__(self, id):
                    self.id = id
            
            return SimpleOrder(order_id)
            
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        return None

def create_test_orders_for_tenant(tenant_slug):
    """Create test orders for each category with different statuses."""
    tenant_manager = TenantManager()
    
    # Get tenant by slug
    tenant = tenant_manager.get_by_slug(tenant_slug)
    if not tenant:
        logger.error(f"Tenant not found: {tenant_slug}")
        return
    
    tenant_id = str(tenant.id)
    logger.info(f"Creating test orders for tenant: {tenant.name} (ID: {tenant_id})")
    
    # Create or get test user
    user = create_or_get_test_user()
    if not user:
        logger.error("Failed to create or get test user")
        return
    
    # Get products by category
    products_by_category = get_products_by_category(tenant_id)
    
    if not products_by_category:
        logger.warning(f"No products with categories found for tenant {tenant.name}")
        return
    
    # Different order statuses to test
    statuses = [
        OrderStatus.PENDING,
        OrderStatus.PROCESSING,
        OrderStatus.SHIPPED,
        OrderStatus.DELIVERED,
        OrderStatus.COMPLETED
    ]
    
    orders_created = 0
    
    # Create orders for each category with different statuses
    for category_name, products in products_by_category.items():
        if not products:
            logger.warning(f"No products in category: {category_name}")
            continue
            
        logger.info(f"Creating orders for category: {category_name} with {len(products)} products")
        
        for status in statuses:
            # Select a random product from this category
            product = random.choice(products)
            
            # Create an order with this product and status
            order = create_order(tenant_id, product, status, user.id)
            
            if order:
                orders_created += 1
    
    logger.info(f"Created {orders_created} test orders for tenant {tenant.name}")
    return orders_created

def main():
    """Main function to create test orders for all tenants."""
    tenant_manager = TenantManager()
    tenants = tenant_manager.list()
    
    total_orders = 0
    
    # Create orders for each tenant
    for tenant in tenants:
        orders = create_test_orders_for_tenant(tenant.slug)
        if orders:
            total_orders += orders
    
    logger.info(f"Total orders created: {total_orders}")

if __name__ == "__main__":
    main()