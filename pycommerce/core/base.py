"""
Base module for the PyCommerce SDK.

This module contains the main PyCommerce class which serves as the central
entry point for using the SDK's functionality.
"""

from typing import Dict, List, Optional, Type, Union
import logging
from fastapi import FastAPI

from pycommerce.core.plugin import PluginManager
from pycommerce.models.product import ProductManager
from pycommerce.models.cart import CartManager
from pycommerce.models.order import OrderManager
from pycommerce.models.user import UserManager
from pycommerce.api.routes import products, cart, checkout, users

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pycommerce")


class PyCommerce:
    """
    Main class for the PyCommerce SDK.
    
    This class serves as the central entry point for using the SDK and
    provides access to all core functionality.
    """
    
    def __init__(self, debug: bool = False):
        """
        Initialize a new PyCommerce instance.
        
        Args:
            debug: Whether to enable debug mode
        """
        self.debug = debug
        if debug:
            logger.setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled")
        
        # Initialize managers
        self.plugins = PluginManager()
        self.products = ProductManager()
        self.carts = CartManager()
        self.orders = OrderManager()
        self.users = UserManager()
        
        # Initialize FastAPI app
        self.app = None
    
    def create_app(self, title: str = "PyCommerce API", 
                  description: str = "API for PyCommerce SDK",
                  version: str = "0.1.0") -> FastAPI:
        """
        Create and configure a FastAPI application with all routes.
        
        Args:
            title: The title of the API
            description: The description of the API
            version: The version of the API
            
        Returns:
            The configured FastAPI application
        """
        self.app = FastAPI(title=title, description=description, version=version)
        
        # Include API routes
        self.app.include_router(products.router, prefix="/api/products", tags=["products"])
        self.app.include_router(cart.router, prefix="/api/cart", tags=["cart"])
        self.app.include_router(checkout.router, prefix="/api/checkout", tags=["checkout"])
        self.app.include_router(users.router, prefix="/api/users", tags=["users"])
        
        # Set dependencies for routes
        products.set_product_manager(self.products)
        cart.set_cart_manager(self.carts)
        checkout.set_order_manager(self.orders)
        users.set_user_manager(self.users)
        
        # Register plugin routes
        self.plugins.register_routes(self.app)
        
        # Add root endpoint with SDK info
        @self.app.get("/", tags=["info"])
        async def get_info():
            return {
                "name": "PyCommerce SDK",
                "version": version,
                "plugins": self.plugins.list_plugins(),
            }
        
        logger.info(f"Created FastAPI application with title: {title}")
        return self.app
