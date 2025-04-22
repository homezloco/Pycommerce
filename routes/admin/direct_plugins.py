"""
Admin routes for direct plugin management.

This module provides a fresh approach to plugin management in the admin interface
by directly accessing the plugin registry.
"""
import logging
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Import the plugin system
from pycommerce import payment_plugins, shipping_plugins
from pycommerce.plugins import get_plugin_registry

# Initialize logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])

# Template setup will be passed from main app
templates = None

def get_all_plugins():
    """
    Get all plugins from both payment and shipping registries.
    
    Returns:
        List of plugin dictionaries with standardized structure
    """
    # Get plugin registry
    registry = get_plugin_registry()
    
    # Get payment plugins
    payment_plugin_list = registry.list_payment_plugins()
    shipping_plugin_list = registry.list_shipping_plugins()
    
    # Log what we found for debugging
    logger.info(f"Found {len(payment_plugin_list)} payment plugins")
    for plugin in payment_plugin_list:
        logger.info(f"Payment plugin: {plugin.name} [{plugin.id}]")
    
    logger.info(f"Found {len(shipping_plugin_list)} shipping plugins")
    for plugin in shipping_plugin_list:
        logger.info(f"Shipping plugin: {plugin.name} [{plugin.id}]")
    
    # Convert to standardized format
    plugins = []
    
    # Process payment plugins
    for plugin in payment_plugin_list:
        plugin_info = {
            'id': getattr(plugin, 'id', str(hash(plugin))),
            'name': getattr(plugin, 'name', type(plugin).__name__),
            'description': getattr(plugin, 'description', 'Payment processor plugin'),
            'version': getattr(plugin, 'version', '1.0.0'),
            'type': 'payment',
            'enabled': True,  # Assume enabled since it's registered
            'configured': True,  # Assume configured
            'removable': False,  # Core plugins can't be removed
        }
        plugins.append(plugin_info)
    
    # Process shipping plugins
    for plugin in shipping_plugin_list:
        plugin_info = {
            'id': getattr(plugin, 'id', str(hash(plugin))),
            'name': getattr(plugin, 'name', type(plugin).__name__),
            'description': getattr(plugin, 'description', 'Shipping method plugin'),
            'version': getattr(plugin, 'version', '1.0.0'),
            'type': 'shipping',
            'enabled': True,  # Assume enabled since it's registered
            'configured': True,  # Assume configured
            'removable': False,  # Core plugins can't be removed
        }
        plugins.append(plugin_info)
    
    logger.info(f"Processed {len(plugins)} total plugins")
    return plugins

@router.get("/direct-plugins", response_class=HTMLResponse)
async def direct_plugins_page(request: Request):
    """Direct plugins page that accesses the plugin registry directly."""
    
    # Get all plugins
    plugins = get_all_plugins()
    
    # Group plugins by type
    plugins_by_type = {}
    for plugin in plugins:
        plugin_type = plugin['type']
        if plugin_type not in plugins_by_type:
            plugins_by_type[plugin_type] = []
        plugins_by_type[plugin_type].append(plugin)
    
    # Log for debugging
    logger.info(f"Serving direct plugins page with {len(plugins)} plugins")
    for plugin_type, plugin_list in plugins_by_type.items():
        logger.info(f"Plugin type {plugin_type}: {len(plugin_list)} plugins")
    
    return templates.TemplateResponse(
        "admin/simple_plugins.html",
        {
            "request": request,
            "active_page": "plugins",
            "plugins": plugins,
            "plugins_by_type": plugins_by_type,
            "plugin_types": list(plugins_by_type.keys()),
            "title": "Direct Plugins"
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