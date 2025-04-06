"""
Routes package for PyCommerce application.

This package contains all the route modules for both admin and storefront.
"""

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

# Import module setup functions
from routes.admin.dashboard import setup_routes as setup_dashboard_routes
from routes.admin.media import setup_routes as setup_media_routes
from routes.admin.orders import setup_routes as setup_orders_routes
from routes.storefront.cart import setup_routes as setup_cart_routes
from routes.storefront.checkout import setup_routes as setup_checkout_routes
from routes.storefront.products import setup_routes as setup_products_routes
from routes.storefront.stores import setup_routes as setup_stores_routes
from routes.storefront.home import setup_routes as setup_home_routes

def register_routes(app: FastAPI, templates: Jinja2Templates):
    """
    Register all routes with the FastAPI application.
    
    Args:
        app: FastAPI application
        templates: Jinja2Templates for template rendering
    """
    # Register admin routes
    app.include_router(setup_dashboard_routes(templates))
    app.include_router(setup_media_routes(templates))
    app.include_router(setup_orders_routes(templates))
    
    # Register storefront routes
    app.include_router(setup_home_routes(templates))
    app.include_router(setup_products_routes(templates))
    app.include_router(setup_stores_routes(templates))
    app.include_router(setup_cart_routes(templates))
    app.include_router(setup_checkout_routes(templates))