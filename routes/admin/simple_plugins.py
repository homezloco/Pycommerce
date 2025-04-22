"""
Admin routes for simplified plugin management.

This module provides routes for managing plugins in the admin interface.
"""
import logging
from typing import Dict, Optional, List

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from pycommerce.models.tenant import TenantManager
from pycommerce.plugins import get_plugin_registry

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])

# Template setup will be passed from main app
templates = None

# Initialize managers
tenant_manager = TenantManager()

@router.get("/plugins-simple", response_class=HTMLResponse)
async def plugins_page_simple(
    request: Request,
    tenant: Optional[str] = None,
    plugin_type: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for simplified plugin management."""
    # Get all tenants for the sidebar
    tenants = tenant_manager.get_all()
    
    # Get tenant from query parameters or session
    selected_tenant_slug = tenant or request.session.get("selected_tenant")
    
    # Create a simplified list of plugins
    plugins = [
        {
            'id': 'stripe_payment',
            'name': 'Stripe Payments',
            'description': 'Process credit card payments with Stripe',
            'version': '0.1.0',
            'type': 'payment',
            'enabled': True,
        },
        {
            'id': 'paypal_payment',
            'name': 'PayPal Payments',
            'description': 'Process payments with PayPal',
            'version': '0.1.0',
            'type': 'payment',
            'enabled': True,
        },
        {
            'id': 'standard_shipping',
            'name': 'Standard Shipping',
            'description': 'Calculate shipping rates for standard delivery',
            'version': '0.1.0',
            'type': 'shipping',
            'enabled': True,
        }
    ]
    
    logger.info(f"Simple plugins page loaded with {len(plugins)} plugins")
    
    return templates.TemplateResponse(
        "admin/plugins_simple.html",
        {
            "request": request,
            "selected_tenant": selected_tenant_slug,
            "tenants": tenants,
            "active_page": "plugins",
            "plugins": plugins,
            "plugin_types": ['payment', 'shipping'],
            "status_message": status_message,
            "status_type": status_type
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