"""
Tenant selection improvements for PyCommerce admin interface.

This module contains improved tenant selection code for various admin sections to ensure
consistent tenant selection behavior across the admin interface.
"""

import logging

logger = logging.getLogger(__name__)

# AI Config Section Improvements
ai_config_tenant_selection = """
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
                    request.session["tenant_id"] = tenant["id"]  # Also store the tenant ID
                    break
                    
        # Fallback if no tenant selected or found
        if not selected_tenant and tenants:
            selected_tenant = tenants[0]
            selected_tenant_slug = selected_tenant["slug"]
            # Update session with selected tenant
            request.session["selected_tenant"] = selected_tenant_slug
            request.session["tenant_id"] = selected_tenant["id"]
"""

# Plugin Config Improvements
plugin_config_tenant_selection = """
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
"""

def get_or_create_tenant_selection(request, tenants, tenant_param=None, allow_all=False):
    """
    Consistent tenant selection helper function.
    
    Args:
        request: The FastAPI request object
        tenants: List of tenant dictionaries
        tenant_param: Optional tenant parameter from URL or form
        allow_all: Whether to allow "all" as a valid selection
        
    Returns:
        Tuple of (selected_tenant_slug, selected_tenant_dict)
    """
    # Get selected tenant from param, query param, or session
    selected_tenant_slug = tenant_param or request.query_params.get('tenant') or request.session.get("selected_tenant")
    selected_tenant = None
    
    # Handle "all" selection based on allow_all
    if selected_tenant_slug == "all":
        if allow_all:
            # Keep "all" selection and update session
            request.session["selected_tenant"] = "all"
            request.session["tenant_id"] = None
            return "all", None
        elif tenants:
            # Switch to first tenant if "all" not allowed
            selected_tenant_slug = tenants[0]["slug"]
            logger.info(f"'All Stores' selected but using first tenant {selected_tenant_slug}")
    
    # Find the tenant in the tenants list
    if selected_tenant_slug:
        for tenant in tenants:
            if tenant["slug"] == selected_tenant_slug:
                selected_tenant = tenant
                # Update session
                request.session["selected_tenant"] = selected_tenant_slug
                request.session["tenant_id"] = tenant["id"]
                break
    
    # Fallback if no tenant selected or found
    if not selected_tenant and tenants:
        selected_tenant = tenants[0]
        selected_tenant_slug = selected_tenant["slug"]
        # Update session
        request.session["selected_tenant"] = selected_tenant_slug
        request.session["tenant_id"] = selected_tenant["id"]
        
    return selected_tenant_slug, selected_tenant
"""

def update_ai_config_route(web_server_py):
    """Replace the tenant selection code in the AI config route."""
    start_marker = "        # Get selected tenant from query param"
    end_marker = "        # Get cart item count if available"
    replacement = ai_config_tenant_selection
    
    start_index = web_server_py.find(start_marker)
    end_index = web_server_py.find(end_marker)
    
    if start_index > 0 and end_index > start_index:
        # Replace the tenant selection code
        web_server_py = web_server_py[:start_index] + replacement + web_server_py[end_index:]
        
    return web_server_py