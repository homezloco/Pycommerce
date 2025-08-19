"""
Generate realistic demo data for the dashboard analytics.

This script creates sample orders, products, and sales data for demonstration purposes.
"""

import logging
import random
from datetime import datetime, timedelta
import uuid
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample product data for different tenants
PRODUCT_DATA = {
    "demo1": [
        {"name": "Premium Headphones", "price": 149.99, "description": "Noise-cancelling wireless headphones", "sku": "HD-001", "stock": 45},
        {"name": "Smart Watch", "price": 199.99, "description": "Fitness tracking smartwatch", "sku": "SW-002", "stock": 30},
        {"name": "Bluetooth Speaker", "price": 79.99, "description": "Portable waterproof speaker", "sku": "BS-003", "stock": 60},
        {"name": "Wireless Earbuds", "price": 89.99, "description": "True wireless earbuds with charging case", "sku": "WE-004", "stock": 75},
        {"name": "Laptop Stand", "price": 29.99, "description": "Adjustable ergonomic laptop stand", "sku": "LS-005", "stock": 100},
    ],
    "tech": [
        {"name": "Smartphone Pro", "price": 999.99, "description": "Latest flagship smartphone", "sku": "SP-101", "stock": 25},
        {"name": "4K Monitor", "price": 349.99, "description": "Ultra HD monitor with HDR", "sku": "MON-102", "stock": 15},
        {"name": "Gaming Keyboard", "price": 129.99, "description": "Mechanical RGB gaming keyboard", "sku": "KB-103", "stock": 40},
        {"name": "Wireless Mouse", "price": 59.99, "description": "Ergonomic wireless mouse", "sku": "MS-104", "stock": 55},
        {"name": "USB-C Hub", "price": 49.99, "description": "Multi-port USB-C hub", "sku": "HUB-105", "stock": 70},
    ],
    "outdoor": [
        {"name": "Hiking Backpack", "price": 89.99, "description": "Waterproof hiking backpack", "sku": "BP-201", "stock": 35},
        {"name": "Camping Tent", "price": 199.99, "description": "4-person waterproof tent", "sku": "CT-202", "stock": 20},
        {"name": "Trekking Poles", "price": 49.99, "description": "Adjustable lightweight trekking poles", "sku": "TP-203", "stock": 45},
        {"name": "Sleeping Bag", "price": 129.99, "description": "All-weather sleeping bag", "sku": "SB-204", "stock": 30},
        {"name": "Camping Stove", "price": 69.99, "description": "Portable camping stove", "sku": "CS-205", "stock": 25},
    ],
    "fashion": [
        {"name": "Leather Jacket", "price": 199.99, "description": "Premium leather jacket", "sku": "LJ-301", "stock": 15},
        {"name": "Designer Jeans", "price": 89.99, "description": "Slim-fit designer jeans", "sku": "DJ-302", "stock": 40},
        {"name": "Cashmere Sweater", "price": 149.99, "description": "Soft cashmere sweater", "sku": "CS-303", "stock": 25},
        {"name": "Dress Shoes", "price": 129.99, "description": "Italian leather dress shoes", "sku": "DS-304", "stock": 20},
        {"name": "Designer Sunglasses", "price": 179.99, "description": "UV protection designer sunglasses", "sku": "SG-305", "stock": 30},
    ],
    "demo2": [
        {"name": "Coffee Maker", "price": 99.99, "description": "Programmable coffee maker", "sku": "CM-401", "stock": 40},
        {"name": "Blender", "price": 69.99, "description": "High-speed blender", "sku": "BL-402", "stock": 35},
        {"name": "Toaster Oven", "price": 89.99, "description": "Convection toaster oven", "sku": "TO-403", "stock": 25},
        {"name": "Food Processor", "price": 129.99, "description": "Multi-function food processor", "sku": "FP-404", "stock": 20},
        {"name": "Stand Mixer", "price": 249.99, "description": "Professional stand mixer", "sku": "SM-405", "stock": 15},
    ]
}

# Sample customer data
CUSTOMERS = [
    {"name": "John Smith", "email": "john.smith@example.com"},
    {"name": "Emma Johnson", "email": "emma.johnson@example.com"},
    {"name": "Michael Brown", "email": "michael.brown@example.com"},
    {"name": "Sarah Davis", "email": "sarah.davis@example.com"},
    {"name": "David Wilson", "email": "david.wilson@example.com"},
    {"name": "Jessica Martinez", "email": "jessica.martinez@example.com"},
    {"name": "James Taylor", "email": "james.taylor@example.com"},
    {"name": "Emily Anderson", "email": "emily.anderson@example.com"},
    {"name": "Robert Thomas", "email": "robert.thomas@example.com"},
    {"name": "Jennifer Jackson", "email": "jennifer.jackson@example.com"},
]

# Order statuses with weights for random selection
ORDER_STATUSES = {
    "PENDING": 5,
    "PROCESSING": 10,
    "PAID": 15,
    "SHIPPED": 25,
    "DELIVERED": 30,
    "COMPLETED": 10,
    "CANCELLED": 3,
    "REFUNDED": 2,
}

# Order types with weights for random selection
ORDER_TYPES = {
    "STANDARD": 70,
    "EXPEDITED": 10,
    "INTERNATIONAL": 5,
    "GIFT": 5,
    "WHOLESALE": 3,
    "SUBSCRIPTION": 3,
    "BACKORDER": 2,
    "PREORDER": 2,
}


def generate_realistic_datetime(days_back: int = 30) -> datetime:
    """Generate a realistic datetime within the last 'days_back' days."""
    random_days = random.randint(0, days_back)
    random_hours = random.randint(0, 23)
    random_minutes = random.randint(0, 59)
    
    return datetime.now() - timedelta(days=random_days, hours=random_hours, minutes=random_minutes)


def generate_order_items(tenant_slug: str, num_items: int = None) -> List[Dict[str, Any]]:
    """Generate random order items for a given tenant."""
    if num_items is None:
        num_items = random.randint(1, 3)  # Random number of items per order
    
    if tenant_slug not in PRODUCT_DATA:
        tenant_slug = random.choice(list(PRODUCT_DATA.keys()))
    
    products = PRODUCT_DATA[tenant_slug]
    order_items = []
    
    for _ in range(num_items):
        product = random.choice(products)
        quantity = random.randint(1, 3)
        
        order_items.append({
            "product_id": str(uuid.uuid4()),
            "product_name": product["name"],
            "price": product["price"],
            "quantity": quantity,
            "subtotal": round(product["price"] * quantity, 2)
        })
    
    return order_items


def create_mock_order(tenant_slug: str, days_back: int = 30) -> Dict[str, Any]:
    """Create a mock order for analytics demonstration."""
    # Generate order items
    items = generate_order_items(tenant_slug)
    
    # Calculate order totals
    subtotal = sum(item["subtotal"] for item in items)
    tax = round(subtotal * 0.08, 2)  # 8% tax
    shipping = round(random.uniform(5.0, 15.0), 2)
    total = subtotal + tax + shipping
    
    # Select random customer
    customer = random.choice(CUSTOMERS)
    
    # Generate random status and type based on weights
    status = random.choices(
        list(ORDER_STATUSES.keys()), 
        weights=list(ORDER_STATUSES.values()), 
        k=1
    )[0]
    
    order_type = random.choices(
        list(ORDER_TYPES.keys()), 
        weights=list(ORDER_TYPES.values()), 
        k=1
    )[0]
    
    # Create the order
    order = {
        "id": str(uuid.uuid4()),
        "tenant_id": f"tenant_{tenant_slug}",
        "customer_name": customer["name"],
        "customer_email": customer["email"],
        "created_at": generate_realistic_datetime(days_back),
        "updated_at": datetime.now(),
        "status": status,
        "type": order_type,
        "items": items,
        "subtotal": subtotal,
        "tax": tax,
        "shipping": shipping,
        "total": total,
        "payment_method": random.choice(["Credit Card", "PayPal", "Apple Pay"])
    }
    
    return order


def create_mock_orders_batch(tenant_slug: str, count: int = 20, days_back: int = 30) -> List[Dict[str, Any]]:
    """Create a batch of mock orders for a tenant."""
    return [create_mock_order(tenant_slug, days_back) for _ in range(count)]


def generate_sales_data_for_tenant(tenant_slug: str, days_back: int = 30) -> Dict[str, Any]:
    """
    Generate complete sales data for dashboard analytics demo.
    
    Args:
        tenant_slug: The tenant slug to generate data for
        days_back: How many days back to generate data for
    
    Returns:
        Dictionary with complete sales analytics data
    """
    # Create the orders
    orders = create_mock_orders_batch(tenant_slug, count=random.randint(20, 50), days_back=days_back)
    
    # Setup date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    date_range = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days_back + 1)]
    
    # Initialize data structures
    revenue_by_date = {date: 0.0 for date in date_range}
    orders_by_date = {date: 0 for date in date_range}
    product_sales = {}
    
    # Process orders to generate analytics data
    for order in orders:
        order_date = order["created_at"].strftime("%Y-%m-%d")
        if order_date in revenue_by_date:
            # Only count completed/shipped/delivered orders for revenue
            if order["status"] in ["COMPLETED", "SHIPPED", "DELIVERED", "PAID"]:
                revenue_by_date[order_date] += order["total"]
            
            orders_by_date[order_date] += 1
            
            # Track product sales
            for item in order["items"]:
                product_name = item["product_name"]
                if product_name not in product_sales:
                    product_sales[product_name] = {
                        "name": product_name,
                        "price": item["price"],
                        "quantity": 0,
                        "revenue": 0.0
                    }
                
                product_sales[product_name]["quantity"] += item["quantity"]
                product_sales[product_name]["revenue"] += item["subtotal"]
    
    # Sort products by revenue and get top 5
    top_products = sorted(
        product_sales.values(), 
        key=lambda x: x["revenue"], 
        reverse=True
    )[:5]
    
    # Create final data structure
    sales_data = {
        "dates": date_range,
        "revenue_data": [revenue_by_date[date] for date in date_range],
        "orders_data": [orders_by_date[date] for date in date_range],
        "top_products": top_products
    }
    
    return sales_data


def create_dashboard_demo_data():
    """Create complete dashboard demo data for all tenants."""
    from pycommerce.models.tenant import TenantManager
    from pycommerce.models.order import OrderManager
    
    tenant_manager = TenantManager()
    order_manager = OrderManager()
    
    # Get all tenants
    tenants = tenant_manager.list()
    
    for tenant in tenants:
        tenant_slug = tenant.slug
        logger.info(f"Generating demo data for tenant: {tenant_slug}")
        
        # Generate orders and add them to the order manager
        orders = create_mock_orders_batch(tenant_slug, count=random.randint(20, 50))
        for order_data in orders:
            try:
                # Convert dates to strings for the order manager
                order_data["created_at"] = order_data["created_at"].isoformat()
                order_data["updated_at"] = order_data["updated_at"].isoformat()
                
                # Add the order to the manager
                order = order_manager.create(tenant.id, order_data)
                logger.info(f"Created order {order.id} for tenant {tenant_slug}")
            except Exception as e:
                logger.error(f"Error creating order for tenant {tenant_slug}: {str(e)}")
    
    logger.info("Dashboard demo data creation complete!")


def create_sales_data_for_dashboard_demo():
    """
    Create sales data for the dashboard demo.
    
    This function returns mock sales data that can be injected into the
    dashboard controller for demonstration purposes.
    """
    demo_sales_data = {
        "dates": [],
        "revenue_data": [],
        "orders_data": [],
        "top_products": []
    }
    
    # Generate last 30 days of dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    date_range = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(31)]
    demo_sales_data["dates"] = date_range
    
    # Generate realistic revenue pattern (higher on weekends, growing trend)
    base_revenue = 500  # Base daily revenue
    growth_factor = 1.02  # 2% daily growth
    
    for i, date_str in enumerate(date_range):
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        
        # Apply growth over time
        day_revenue = base_revenue * (growth_factor ** i)
        
        # Apply weekday/weekend pattern
        if date_obj.weekday() >= 5:  # Weekend
            day_revenue *= 1.5
        
        # Add some randomness
        randomness = random.uniform(0.8, 1.2)
        day_revenue *= randomness
        
        # Round to 2 decimal places
        demo_sales_data["revenue_data"].append(round(day_revenue, 2))
    
    # Generate order counts (roughly correlated with revenue)
    for revenue in demo_sales_data["revenue_data"]:
        # On average, about 1 order per $100 of revenue, with some randomness
        order_count = int(revenue / 100 * random.uniform(0.7, 1.3))
        demo_sales_data["orders_data"].append(order_count)
    
    # Create top product data
    demo_sales_data["top_products"] = [
        {
            "name": "Smartphone Pro",
            "price": 999.99,
            "quantity": 25,
            "revenue": 24999.75
        },
        {
            "name": "4K Monitor",
            "price": 349.99,
            "quantity": 18,
            "revenue": 6299.82
        },
        {
            "name": "Premium Headphones",
            "price": 149.99,
            "quantity": 40,
            "revenue": 5999.60
        },
        {
            "name": "Gaming Keyboard",
            "price": 129.99,
            "quantity": 35,
            "revenue": 4549.65
        },
        {
            "name": "Smart Watch",
            "price": 199.99,
            "quantity": 22,
            "revenue": 4399.78
        }
    ]
    
    return demo_sales_data


if __name__ == "__main__":
    try:
        # Try to create actual orders in the database
        create_dashboard_demo_data()
    except Exception as e:
        logger.error(f"Error creating database orders: {str(e)}")
        logger.info("Falling back to static sales data generation...")
        # Generate static sales data for demo
        demo_data = create_sales_data_for_dashboard_demo()
        print("Generated demo sales data:")
        print(f"Date range: {demo_data['dates'][0]} to {demo_data['dates'][-1]}")
        print(f"Total revenue: ${sum(demo_data['revenue_data']):.2f}")
        print(f"Total orders: {sum(demo_data['orders_data'])}")
        print("Top products:")
        for product in demo_data['top_products']:
            print(f"  - {product['name']}: ${product['revenue']:.2f} ({product['quantity']} sold)")