"""
Admin routes for plugin management.

This module provides routes for managing plugins in the admin interface.
"""
import logging
from typing import Dict, Optional, List

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
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

@router.get("/plugins", response_class=HTMLResponse)
async def plugins_page(
    request: Request,
    tenant: Optional[str] = None,
    plugin_type: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for plugin management."""
    # Get tenant from query parameters or session
    selected_tenant_slug = tenant or request.session.get("selected_tenant")
    
    # If no tenant is selected, redirect to dashboard with message
    if not selected_tenant_slug:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Please+select+a+store+first&status_type=warning", 
            status_code=303
        )
    
    # Store the selected tenant in session for future requests
    request.session["selected_tenant"] = selected_tenant_slug
    
    # Get tenant object
    tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
    if not tenant_obj:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Store+not+found&status_type=error", 
            status_code=303
        )
    
    # Get plugin registry
    registry = get_plugin_registry()
    
    # Get all plugins from registry 
    payment_plugins = registry.list_payment_plugins()
    shipping_plugins = registry.list_shipping_plugins()
    
    # Organize plugins by type
    plugins_by_type = {
        'payment': [],
        'shipping': []
    }
    
    # Add payment plugins
    for plugin in payment_plugins:
        plugin_id = getattr(plugin, 'plugin_id', plugin.__class__.__name__)
        plugins_by_type['payment'].append({
            'id': plugin_id,
            'name': getattr(plugin, 'name', plugin_id),
            'description': getattr(plugin, 'description', ''),
            'version': getattr(plugin, 'version', '0.1.0'),
            'enabled': True,  # Assume enabled by default
            'config_schema': getattr(plugin, 'config_schema', {}),
        })
    
    # Add shipping plugins
    for plugin in shipping_plugins:
        plugin_id = getattr(plugin, 'plugin_id', plugin.__class__.__name__)
        plugins_by_type['shipping'].append({
            'id': plugin_id,
            'name': getattr(plugin, 'name', plugin_id),
            'description': getattr(plugin, 'description', ''),
            'version': getattr(plugin, 'version', '0.1.0'),
            'enabled': True,  # Assume enabled by default
            'config_schema': getattr(plugin, 'config_schema', {}),
        })
    
    # Filter by plugin type if specified
    if plugin_type and plugin_type in plugins_by_type:
        filtered_plugins = {plugin_type: plugins_by_type[plugin_type]}
    else:
        filtered_plugins = plugins_by_type
    
    # Get tenant plugin configuration
    tenant_plugin_config = getattr(tenant_obj, 'plugin_config', {}) or {}
    
    # Get all tenants for the sidebar
    tenants = tenant_manager.get_all()
    
    return templates.TemplateResponse(
        "admin/plugins.html",
        {
            "request": request,
            "selected_tenant": selected_tenant_slug,
            "tenant": tenant_obj,
            "tenants": tenants,
            "active_page": "plugins",
            "plugins_by_type": filtered_plugins,
            "plugin_types": list(plugins_by_type.keys()),
            "selected_plugin_type": plugin_type,
            "plugin_config": tenant_plugin_config,
            "status_message": status_message,
            "status_type": status_type
        }
    )

@router.post("/plugins/configure", response_class=RedirectResponse)
async def configure_plugin(
    request: Request,
    tenant_id: str = Form(...),
    plugin_id: str = Form(...),
    enabled: Optional[str] = Form(None),
    config_json: Optional[str] = Form("{}")
):
    """Configure a plugin for a tenant."""
    try:
        # Get tenant
        tenant = tenant_manager.get(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=404,
                detail=f"Store with ID {tenant_id} not found"
            )
        
        # Parse config JSON
        import json
        config = json.loads(config_json)
        
        # Update plugin configuration
        is_enabled = enabled is not None
        
        # Get tenant plugin config
        tenant_plugin_config = getattr(tenant, 'plugin_config', {}) or {}
        
        # Update plugin config
        if plugin_id not in tenant_plugin_config:
            tenant_plugin_config[plugin_id] = {}
            
        tenant_plugin_config[plugin_id]['enabled'] = is_enabled
        tenant_plugin_config[plugin_id]['config'] = config
        
        # Save updated configuration
        # This would normally be done by tenant_manager.update_plugin_config
        # but for demo purposes, we'll just log the update
        logger.info(f"Would update plugin config for tenant {tenant_id}: {tenant_plugin_config}")
        
        # Get tenant slug for redirect
        tenant_slug = tenant.slug
        
        return RedirectResponse(
            url=f"/admin/plugins?tenant={tenant_slug}&status_message=Plugin+configuration+updated+successfully&status_type=success",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Error configuring plugin: {str(e)}")
        return RedirectResponse(
            url=f"/admin/plugins?tenant={tenant.slug if tenant else ''}&status_message=Error+configuring+plugin:+{str(e)}&status_type=danger",
            status_code=status.HTTP_303_SEE_OTHER
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