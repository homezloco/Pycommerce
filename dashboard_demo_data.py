"""
Dashboard demo data provider.

This module provides mock data for the dashboard to demonstrate its analytics capabilities.
"""

from datetime import datetime, timedelta
import random


def get_demo_sales_data(time_period="last7days"):
    """
    Get mock sales data for the dashboard based on the requested time period.
    
    Args:
        time_period: The time period to generate data for.
            Valid values: today, yesterday, last7days, last30days, thismonth, lastmonth
    
    Returns:
        Dictionary with sales data
    """
    # Calculate date range based on selected time period
    end_date = datetime.now()
    
    if time_period == "today":
        days = 1
        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_period == "yesterday":
        days = 1
        start_date = (end_date - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1, microseconds=-1)
    elif time_period == "last7days":
        days = 7
        start_date = end_date - timedelta(days=days-1)
    elif time_period == "last30days":
        days = 30
        start_date = end_date - timedelta(days=days-1)
    elif time_period == "thismonth":
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        days = (end_date - start_date).days + 1
    elif time_period == "lastmonth":
        this_month_start = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_date = (this_month_start - timedelta(days=1)).replace(day=1)
        end_date = this_month_start - timedelta(microseconds=1)
        days = (end_date - start_date).days + 1
    else:
        # Default to last 7 days
        days = 7
        start_date = end_date - timedelta(days=days-1)
    
    # Generate dates
    date_range = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    
    # Generate realistic revenue pattern (higher on weekends, growing trend)
    base_revenue = 500  # Base daily revenue
    growth_factor = 1.02  # 2% daily growth
    revenue_data = []
    
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
        revenue_data.append(round(day_revenue, 2))
    
    # Generate order counts (roughly correlated with revenue)
    orders_data = [int(revenue / 100 * random.uniform(0.7, 1.3)) for revenue in revenue_data]
    
    # Create top product data
    top_products = [
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
    
    # Return final data structure
    return {
        "dates": date_range,
        "revenue_data": revenue_data,
        "orders_data": orders_data,
        "top_products": top_products
    }


def get_demo_orders(count=5):
    """
    Get mock recent orders for the dashboard.
    
    Args:
        count: Number of orders to generate
    
    Returns:
        List of order dictionaries
    """
    order_statuses = ["PENDING", "PROCESSING", "PAID", "SHIPPED", "DELIVERED", "COMPLETED"]
    customer_names = [
        "John Smith", "Emma Johnson", "Michael Brown", "Sarah Davis", 
        "David Wilson", "Jessica Martinez", "James Taylor", "Emily Anderson"
    ]
    
    orders = []
    for i in range(count):
        created_at = datetime.now() - timedelta(days=random.randint(0, 7), 
                                              hours=random.randint(0, 23), 
                                              minutes=random.randint(0, 59))
        
        orders.append({
            "id": f"ORDER-{1000 + i}",
            "customer_name": random.choice(customer_names),
            "total": round(random.uniform(50, 500), 2),
            "status": random.choice(order_statuses),
            "created_at": created_at
        })
    
    # Sort by creation date, most recent first
    orders.sort(key=lambda x: x["created_at"], reverse=True)
    return orders