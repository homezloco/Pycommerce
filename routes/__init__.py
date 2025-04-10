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
from routes.admin.products import setup_routes as setup_admin_products_routes
from routes.admin.settings import setup_routes as setup_settings_routes
from routes.admin.stores import setup_routes as setup_stores_admin_routes
# Import new admin routes
from routes.admin.store_settings import setup_routes as setup_store_settings_routes
from routes.admin.theme_settings import setup_routes as setup_theme_settings_routes
from routes.admin.plugins import setup_routes as setup_plugins_routes
from routes.admin.ai_config import setup_routes as setup_ai_config_routes
from routes.admin.users import setup_routes as setup_users_routes
from routes.admin.customers import setup_routes as setup_customers_routes
from routes.admin.marketing import setup_routes as setup_marketing_routes
from routes.admin.analytics import setup_routes as setup_analytics_routes
from routes.admin.shipping import setup_routes as setup_shipping_routes
from routes.admin.reports import setup_routes as setup_reports_routes
from routes.admin.returns import setup_routes as setup_returns_routes
from routes.admin.market_analysis import setup_routes as setup_market_analysis_routes
# We've moved the test_products implementation to products.py

# Import storefront routes
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
    # Using updated products implementation
    app.include_router(setup_admin_products_routes(templates))
    app.include_router(setup_settings_routes(templates))
    app.include_router(setup_stores_admin_routes(templates))
    
    # Register new admin routes
    app.include_router(setup_store_settings_routes(templates))
    app.include_router(setup_theme_settings_routes(templates))
    app.include_router(setup_plugins_routes(templates))
    app.include_router(setup_ai_config_routes(templates))
    app.include_router(setup_users_routes(templates))
    app.include_router(setup_customers_routes(templates))
    app.include_router(setup_marketing_routes(templates))
    app.include_router(setup_analytics_routes(templates))
    
    # Register shipping, returns, reports, and market analysis routes
    app.include_router(setup_shipping_routes(templates))
    app.include_router(setup_returns_routes(templates))
    app.include_router(setup_reports_routes(templates))
    app.include_router(setup_market_analysis_routes(templates))
    
    # Register storefront routes
    app.include_router(setup_home_routes(templates))
    app.include_router(setup_products_routes(templates))
    app.include_router(setup_stores_routes(templates))
    app.include_router(setup_cart_routes(templates))
    app.include_router(setup_checkout_routes(templates))