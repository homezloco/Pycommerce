"""
Tenant utility functions for admin routes.

This module provides helper functions for tenant selection and management
across the admin interface to ensure consistent behavior.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from fastapi import Request

from pycommerce.models.tenant import TenantManager

logger = logging.getLogger(__name__)

# Initialize tenant manager
tenant_manager = TenantManager()

def get_selected_tenant(request, tenants, tenant_param=None, allow_all=False):
    """
    Get the selected tenant based on request parameters and session data.
    
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
    
def get_current_tenant(request: Request):
    """
    Get the current tenant based on session data or query parameters.
    
    This function is used by the market analysis routes to get the current tenant
    for filtering market data.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        The tenant object or None
    """
    # Get tenant from query param or session
    tenant_slug = request.query_params.get('tenant') or request.session.get("selected_tenant")
    
    # Special case for "all" tenants
    if tenant_slug == "all":
        return None
        
    # Get tenant by slug if we have one
    if tenant_slug:
        try:
            return tenant_manager.get_by_slug(tenant_slug)
        except Exception as e:
            logger.warning(f"Could not get tenant with slug '{tenant_slug}': {str(e)}")
    
    # Fallback: get first tenant
    tenants = tenant_manager.list()
    if tenants and len(tenants) > 0:
        return tenants[0]
    
    # If no tenants found
    return None