"""
Test if OrderManager can be imported and used correctly.

This will help identify any circular import issues.
"""
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pycommerce_order_manager():
    """Test importing and using the OrderManager from pycommerce."""
    try:
        from pycommerce.models.order import OrderManager
        logger.info("Successfully imported OrderManager from pycommerce.models.order")
        
        # Try to initialize the manager
        order_manager = OrderManager()
        logger.info("Successfully initialized OrderManager")
        
        # Show available methods
        methods = [method for method in dir(order_manager) if not method.startswith('_')]
        logger.info(f"Available methods: {methods}")
        
        return True
    except Exception as e:
        logger.error(f"Error importing or using OrderManager: {str(e)}")
        return False

def test_flask_order_manager():
    """Test importing and using the OrderManager from managers.py."""
    try:
        from managers import OrderManager
        logger.info("Successfully imported OrderManager from managers")
        
        # Try to initialize the manager
        order_manager = OrderManager()
        logger.info("Successfully initialized OrderManager")
        
        # Show available methods
        methods = [method for method in dir(order_manager) if not method.startswith('_')]
        logger.info(f"Available methods: {methods}")
        
        return True
    except Exception as e:
        logger.error(f"Error importing or using OrderManager: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing PyCommerce OrderManager...")
    pycommerce_success = test_pycommerce_order_manager()
    
    print("\nTesting Flask OrderManager...")
    flask_success = test_flask_order_manager()
    
    if pycommerce_success and flask_success:
        print("\nBoth OrderManager implementations can be imported and used successfully.")
        sys.exit(0)
    else:
        print("\nThere are issues with one or both OrderManager implementations.")
        sys.exit(1)