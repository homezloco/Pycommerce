
"""
Tenant utility functions for admin routes.

This module provides helper functions for tenant selection and management
across the admin interface to ensure consistent behavior.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from fastapi import Request, Query, Depends
from fastapi.responses import RedirectResponse

from pycommerce.models.tenant import TenantManager, TenantDTO

logger = logging.getLogger(__name__)

# Initialize tenant manager
tenant_manager = TenantManager()

def get_selected_tenant(request: Request, tenant_param: Optional[str] = None, 
                       allow_all: bool = False) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Get the selected tenant based on request parameters and session data.
    
    Args:
        request: The FastAPI request object
        tenant_param: Optional tenant parameter from URL or form
        allow_all: Whether to allow "all" as a valid selection
        
    Returns:
        Tuple of (selected_tenant_slug, selected_tenant_dict)
    """
    # Get all tenants first for fallback
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
    except Exception as e:
        logger.error(f"Error fetching tenants: {str(e)}")
        tenants = []
    
    # Get selected tenant from param, query param, or session
    selected_tenant_slug = tenant_param or request.query_params.get('tenant') or request.session.get("selected_tenant")
    selected_tenant = None
    
    # Handle "all" selection based on allow_all parameter (case insensitive)
    if selected_tenant_slug and selected_tenant_slug.lower() == "all":
        if allow_all:
            # Keep "all" selection and update session
            request.session["selected_tenant"] = "all"
            request.session["tenant_id"] = None
            logger.info("Using 'All Stores' selection")
            return "all", None
        elif tenants:
            # Switch to first tenant if "all" not allowed
            selected_tenant_slug = tenants[0]["slug"]
            logger.info(f"'All Stores' selected but using first tenant {selected_tenant_slug} since allow_all=False")
    
    # Find the tenant in the tenants list
    if selected_tenant_slug and selected_tenant_slug.lower() != "all":
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

def get_all_tenants() -> List[Dict[str, Any]]:
    """
    Get a list of all tenants formatted for templates.
    
    Returns:
        List of tenant dictionaries
    """
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
        return tenants
    except Exception as e:
        logger.error(f"Error fetching tenants: {str(e)}")
        return []

def get_tenant_object(tenant_id_or_slug: str) -> Optional[TenantDTO]:
    """
    Get tenant object by ID or slug.
    
    Args:
        tenant_id_or_slug: Tenant ID or slug
    
    Returns:
        Tenant object or None if not found
    """
    try:
        # Try to get by ID first
        tenant = tenant_manager.get(tenant_id_or_slug)
        if tenant:
            return tenant
            
        # If not found, try by slug
        return tenant_manager.get_by_slug(tenant_id_or_slug)
    except Exception as e:
        logger.error(f"Error getting tenant {tenant_id_or_slug}: {str(e)}")
        return None
        
def redirect_to_tenant_selection(message: str = "Please select a store first", 
                               message_type: str = "warning") -> RedirectResponse:
    """
    Create a redirect response to the dashboard with a message to select a tenant.
    
    Args:
        message: Message to display
        message_type: Message type (info, warning, error, success)
        
    Returns:
        RedirectResponse to dashboard with message
    """
    return RedirectResponse(
        url=f"/admin/dashboard?status_message={message.replace(' ', '+')}&status_type={message_type}", 
        status_code=303
    )

def create_virtual_all_tenant() -> Dict[str, Any]:
    """
    Create a virtual tenant object representing "All Stores"
    
    Returns:
        Dictionary with tenant-like structure
    """
    return {
        "id": "all",
        "name": "All Stores",
        "slug": "all",
        "domain": None,
        "active": True
    }
