"""
Simplified admin routes for plugin management.

This provides a minimal implementation for the plugins page.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Initialize logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])

# Templates will be set by the calling application
templates = None

@router.get("/simple-plugins", response_class=HTMLResponse)
async def simple_plugins_page(request: Request):
    """Simple plugins page displaying hardcoded plugin data."""
    
    # Create a hardcoded list of plugins
    plugins = [
        {
            'id': 'stripe_payment',
            'name': 'Stripe Payments',
            'description': 'Process credit card payments with Stripe',
            'version': '0.1.0',
            'type': 'payment',
            'enabled': True,
            'configured': True,
            'removable': False,
        },
        {
            'id': 'paypal_payment',
            'name': 'PayPal Payments',
            'description': 'Process payments with PayPal',
            'version': '0.1.0',
            'type': 'payment',
            'enabled': True,
            'configured': True,
            'removable': False,
        },
        {
            'id': 'standard_shipping',
            'name': 'Standard Shipping',
            'description': 'Calculate shipping rates for standard delivery',
            'version': '0.1.0',
            'type': 'shipping',
            'enabled': True,
            'configured': True,
            'removable': False,
        }
    ]
    
    # Log the plugin data to help with debugging
    logger.info(f"Rendering simple plugins page with {len(plugins)} plugins")
    for plugin in plugins:
        logger.info(f"Plugin: {plugin['name']} [{plugin['id']}] type={plugin['type']}")
    
    return templates.TemplateResponse(
        "admin/simple_plugins.html",
        {
            "request": request,
            "active_page": "plugins",
            "plugins": plugins,
            "title": "Simple Plugins Page"
        }
    )

def setup_routes(app_templates):
    """
    Set up routes with the given templates.
    
    Args:
        app_templates: Jinja2Templates instance from the main app
    """
    global templates
    templates = app_templates
    return router