"""
Debug script to diagnose Market Analysis data issues.
"""
import os
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize database connection
def get_session():
    """Create a database session."""
    engine = create_engine(os.environ.get('DATABASE_URL'))
    Session = sessionmaker(bind=engine)
    return Session()

def main():
    """Main debugging function."""
    session = get_session()
    
    # Step 1: Get the Tech tenant
    from models import Tenant
    tech_tenant = session.query(Tenant).filter_by(slug='tech').first()
    tenant_id = tech_tenant.id if tech_tenant else None
    
    if not tenant_id:
        logger.error("Tech tenant not found")
        return
    
    logger.info(f"Tech tenant ID: {tenant_id}")
    
    # Step 2: Get orders for this tenant
    from models import Order
    orders = session.query(Order).filter_by(tenant_id=tenant_id).all()
    logger.info(f"Total orders for tenant: {len(orders)}")
    
    # Step 3: Apply the same date filter logic as in market_analysis.py
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=30)
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    logger.info(f"Date range filter: {start_date_str} to {end_date_str}")
    
    # Exactly match the filtering logic in market_analysis.py
    filtered_orders = [order for order in orders 
                     if order.created_at.strftime("%Y-%m-%d") >= start_date_str 
                     and order.created_at.strftime("%Y-%m-%d") <= end_date_str]
    
    logger.info(f"Orders after date filter: {len(filtered_orders)}")
    
    # Let's check each order to see what's happening
    passing_orders = []
    failing_orders = []
    
    for order in orders:
        order_date_str = order.created_at.strftime("%Y-%m-%d")
        
        condition1 = order_date_str >= start_date_str
        condition2 = order_date_str <= end_date_str
        
        if condition1 and condition2:
            passing_orders.append(order)
        else:
            failing_orders.append((order, condition1, condition2))
    
    logger.info(f"Orders passing both conditions: {len(passing_orders)}")
    logger.info(f"Orders failing one or both conditions: {len(failing_orders)}")
    
    # Print a few examples of passing and failing orders
    if passing_orders:
        logger.info("\nExample passing orders:")
        for i, order in enumerate(passing_orders[:5]):
            logger.info(f"  {i+1}. Order {order.order_number} created at {order.created_at} - date string: {order.created_at.strftime('%Y-%m-%d')}")
    
    if failing_orders:
        logger.info("\nExample failing orders:")
        for i, (order, pass1, pass2) in enumerate(failing_orders[:5]):
            logger.info(f"  {i+1}. Order {order.order_number} created at {order.created_at} - date string: {order.created_at.strftime('%Y-%m-%d')}")
            logger.info(f"     Condition 1 (>= {start_date_str}): {pass1}")
            logger.info(f"     Condition 2 (<= {end_date_str}): {pass2}")
    
    # Let's check if we're using the right tenant_id and orders collection method in MarketAnalysisService
    from routes.admin.market_analysis import setup_routes
    from pycommerce.services.market_analysis import MarketAnalysisService
    
    # Check what tenant_id is being used in the session
    try:
        from fastapi import Request
        from fastapi.templating import Jinja2Templates
        
        # Create a minimal templates object to satisfy the function signature
        templates = Jinja2Templates(directory="templates")
        
        # Set up routes to get access to the market_analysis_service instance
        router = setup_routes(templates)
        
        # Access the market_analysis_service directly
        # This is hacky but gives us access to the instance
        for route in router.routes:
            if hasattr(route, "endpoint") and route.endpoint.__name__ == "market_analysis_dashboard":
                market_analysis_service = route.endpoint.__closure__[2].cell_contents
                logger.info("\nChecking MarketAnalysisService methods:")
                
                # Execute the get_sales_trends method with debug logging
                logger.info(f"Calling get_sales_trends with tenant_id={tenant_id}")
                result = market_analysis_service.get_sales_trends(
                    tenant_id=tenant_id,
                    start_date=start_date_str,
                    end_date=end_date_str
                )
                
                logger.info(f"Result status: {result.get('status')}")
                logger.info(f"Result message: {result.get('message', '')}")
                logger.info(f"Trends count: {len(result.get('data', {}).get('trends', []))}")
                logger.info(f"Total revenue: {result.get('data', {}).get('total_revenue', 0)}")
                logger.info(f"Total orders: {result.get('data', {}).get('total_orders', 0)}")
                
                break
    except Exception as e:
        logger.error(f"Error accessing market_analysis_service: {str(e)}")
    
    # Alternative method: Create our own instance and test it directly
    try:
        logger.info("\nTesting with fresh MarketAnalysisService instance:")
        service = MarketAnalysisService()
        result = service.get_sales_trends(
            tenant_id=tenant_id,
            start_date=start_date_str,
            end_date=end_date_str
        )
        
        logger.info(f"Result status: {result.get('status')}")
        logger.info(f"Result message: {result.get('message', '')}")
        logger.info(f"Trends count: {len(result.get('data', {}).get('trends', []))}")
        logger.info(f"Total revenue: {result.get('data', {}).get('total_revenue', 0)}")
        logger.info(f"Total orders: {result.get('data', {}).get('total_orders', 0)}")
    except Exception as e:
        logger.error(f"Error with test service: {str(e)}")

if __name__ == "__main__":
    main()