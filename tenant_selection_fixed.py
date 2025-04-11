"""
Tenant selection fixes for PyCommerce admin interface.

This module contains the tenant selection fixes needed for the admin interface.
Since we're having trouble with the string replacement in the web_server.py file,
this file contains the entire admin_ai_config function with the corrected tenant selection.
"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)

async def admin_ai_config(
    request: Request, 
    status_message: Optional[str] = None, 
    status_type: str = "info"
):
    """Admin page for AI configuration."""
    # Get all tenants for the store selector
    tenants = []
    selected_tenant = None
    
    try:
        tenants_list = tenant_manager.list() or []
        tenants = [
            {
                "id": str(t.id),
                "name": t.name,
                "slug": t.slug,
                "domain": t.domain if hasattr(t, 'domain') else None,
                "active": t.active if hasattr(t, 'active') else True
            }
            for t in tenants_list if t and hasattr(t, 'id')
        ]
        
        # Get selected tenant from query param or session
        selected_tenant_slug = request.query_params.get('tenant') or request.session.get("selected_tenant")
        
        # Handle "all" selection - AI config needs a specific tenant
        if selected_tenant_slug == "all" and tenants:
            selected_tenant_slug = tenants[0]["slug"]
            logger.info(f"'All Stores' selected but using first tenant {selected_tenant_slug} for AI configuration")
            
        if selected_tenant_slug:
            # Find the tenant in the tenants list
            for tenant in tenants:
                if tenant["slug"] == selected_tenant_slug:
                    selected_tenant = tenant
                    # Update session with selected tenant
                    request.session["selected_tenant"] = selected_tenant_slug
                    request.session["tenant_id"] = tenant["id"]
                    break
                    
        # Fallback if no tenant selected or found
        if not selected_tenant and tenants:
            selected_tenant = tenants[0]
            selected_tenant_slug = selected_tenant["slug"]
            # Update session with selected tenant
            request.session["selected_tenant"] = selected_tenant_slug
            request.session["tenant_id"] = selected_tenant["id"]
        
        # Get cart item count if available
        cart_item_count = 0
        session = request.session
        if 'cart_id' in session:
            try:
                cart_id = session['cart_id']
                cart = cart_manager.get(cart_id)
                cart_item_count = sum(item.quantity for item in cart.items)
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Error fetching tenants: {str(e)}")
        if status_message is None:
            status_message = f"Error fetching tenants: {str(e)}"
            status_type = "danger"
        tenants = []
        cart_item_count = 0
    
    # Get AI providers
    ai_providers = get_ai_providers()
    
    # Get active provider
    tenant_id = selected_tenant["id"] if selected_tenant else None
    config = load_ai_config(tenant_id)
    active_provider = config.get("active_provider", "openai")
    
    # Default to first provider if none selected
    selected_provider_id = request.query_params.get('provider', active_provider)
    selected_provider = next((p for p in ai_providers if p["id"] == selected_provider_id), ai_providers[0])
    
    # Get provider configuration
    field_values = {}
    provider_config = config.get("provider_config", {}) 
    
    if provider_config:
        for field in selected_provider["fields"]:
            if field["id"] in provider_config:
                field_values[field["id"]] = provider_config[field["id"]]
    
    return templates.TemplateResponse(
        "admin/ai_config.html", 
        {
            "request": request,
            "active_page": "ai_config",
            "tenants": tenants,
            "selected_tenant": selected_tenant_slug,
            "ai_providers": ai_providers,
            "active_provider": active_provider,
            "selected_provider": selected_provider,
            "field_values": field_values,
            "cart_item_count": cart_item_count,
            "status_message": status_message,
            "status_type": status_type
        }
    )

# Plugin Config
async def admin_plugin_config(
    request: Request,
    plugin_id: str,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Plugin configuration page."""
    # Get all tenants for the store selector
    tenants = []
    try:
        tenants_list = tenant_manager.list() or []
        tenants = [
            {
                "id": str(t.id),
                "name": t.name,
                "slug": t.slug,
                "domain": t.domain if hasattr(t, 'domain') else None,
                "active": t.active if hasattr(t, 'active') else True
            }
            for t in tenants_list if t and hasattr(t, 'id')
        ]
        
        # Get selected tenant from query param or session
        selected_tenant = request.query_params.get('tenant') or request.session.get("selected_tenant")
        
        # Handle "all" selection - plugins may need a specific tenant
        if selected_tenant == "all" and tenants:
            selected_tenant = tenants[0]["slug"]
            logger.info(f"'All Stores' selected but using first tenant {selected_tenant} for plugin configuration")
            
        # Fallback if no tenant selected
        if not selected_tenant and tenants:
            selected_tenant = tenants[0]["slug"]
            
        # Update session with the selected tenant
        if selected_tenant:
            request.session["selected_tenant"] = selected_tenant
            
            # Find tenant ID if available
            for t in tenants:
                if t["slug"] == selected_tenant:
                    request.session["tenant_id"] = t["id"]
                    break
        
        # Get tenant object for plugin configuration
        tenant_obj = None
        tenant_id = None
        
        if selected_tenant:
            try:
                tenant_obj = tenant_manager.get_by_slug(selected_tenant)
                tenant_id = str(tenant_obj.id) if hasattr(tenant_obj, 'id') else None
            except Exception as e:
                logger.warning(f"Could not get tenant with slug '{selected_tenant}': {str(e)}")
        
        # Get cart item count if available
        cart_item_count = 0
        session = request.session
        if 'cart_id' in session:
            try:
                cart_id = session['cart_id']
                cart = cart_manager.get(cart_id)
                cart_item_count = sum(item.quantity for item in cart.items)
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Error in admin_plugin_config: {str(e)}")
        if status_message is None:
            status_message = f"Error: {str(e)}"
            status_type = "danger"
        tenants = []
        selected_tenant = None
        cart_item_count = 0
        
    # Get the plugin metadata
    from pycommerce.core.plugin import get_plugin_metadata
    plugin_metadata = get_plugin_metadata(plugin_id)
    
    if not plugin_metadata:
        # Redirect to plugins page with error message
        return RedirectResponse(
            url=f"/admin/plugins?status_message=Plugin+not+found:+{plugin_id}&status_type=danger", 
            status_code=303
        )
    
    # Get plugin configuration
    from pycommerce.models.plugin_config import PluginConfigManager
    config_manager = PluginConfigManager()
    plugin_config = config_manager.get_config(plugin_id, tenant_id)
    
    return templates.TemplateResponse(
        "admin/plugin_config.html",
        {
            "request": request,
            "active_page": "plugins",
            "tenants": tenants,
            "selected_tenant": selected_tenant,
            "plugin": plugin_metadata,
            "config": plugin_config,
            "cart_item_count": cart_item_count,
            "status_message": status_message,
            "status_type": status_type
        }
    )