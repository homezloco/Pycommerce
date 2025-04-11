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

def get_current_tenant(request, tenant_manager_instance=None):
    """
    Get the current tenant from the request.

    Args:
        request: The FastAPI request object
        tenant_manager_instance: Optional tenant manager instance

    Returns:
        Tuple of (tenant_object, tenant_id, tenant_slug)
    """
    tm = tenant_manager_instance or tenant_manager

    # Get selected tenant from session or query param
    tenant_slug = request.query_params.get('tenant') or request.session.get("selected_tenant")
    tenant_id = request.session.get("tenant_id")

    # If no tenant is selected, try to get the first one
    if not tenant_slug or not tenant_id:
        try:
            tenants = get_all_tenants()
            if tenants:
                tenant_slug = tenants[0]["slug"]
                tenant_id = tenants[0]["id"]
                # Update session
                request.session["selected_tenant"] = tenant_slug
                request.session["tenant_id"] = tenant_id
        except Exception as e:
            logger.error(f"Error getting default tenant: {str(e)}")
            return None, None, None

    # Special case for "all" tenants
    if tenant_slug == "all":
        return None, None, "all"

    # Get the tenant object
    tenant_obj = None
    if tenant_id:
        try:
            tenant_obj = tm.get(tenant_id)
        except Exception as e:
            logger.error(f"Error getting tenant by ID {tenant_id}: {str(e)}")

    # If tenant not found by ID, try by slug
    if not tenant_obj and tenant_slug:
        try:
            tenant_obj = tm.get_by_slug(tenant_slug)
            if tenant_obj:
                tenant_id = str(tenant_obj.id)
                # Update session with correct ID
                request.session["tenant_id"] = tenant_id
        except Exception as e:
            logger.error(f"Error getting tenant by slug {tenant_slug}: {str(e)}")

    return tenant_obj, tenant_id, tenant_slug

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

def create_virtual_all_tenant():
    """Create a virtual 'All Stores' tenant object."""
    return {
        "id": "all",
        "name": "All Stores",
        "slug": "all",
        "domain": None,
        "active": True
    }

def get_products_for_all_tenants(tenant_manager, product_manager, logger, filters=None):
    """
    Fetch products from all tenants.

    Args:
        tenant_manager: The tenant manager instance
        product_manager: The product manager instance
        logger: The logger to use
        filters: Optional dictionary of filters to apply

    Returns:
        List of products from all tenants
    """
    if filters is None:
        filters = {}

    try:
        # First try to get all tenants
        all_tenants = tenant_manager.list() or []

        # Then fetch products for each tenant and combine them
        all_products = []
        for tenant in all_tenants:
            try:
                tenant_products = product_manager.get_by_tenant(
                    tenant_id=str(tenant.id),
                    **filters
                )
                all_products.extend(tenant_products)
                logger.info(f"Found {len(tenant_products)} products for tenant {tenant.name}")
            except Exception as e:
                logger.error(f"Error fetching products for tenant {tenant.name}: {str(e)}")

        logger.info(f"Found {len(all_products)} products across all stores")

        # If no products found, fall back to list() method
        if not all_products:
            logger.info("No products found using tenant queries, trying list() method")
            all_products = product_manager.list(**filters)
            logger.info(f"Found {len(all_products)} products using list() method")

        return all_products
    except Exception as e:
        logger.error(f"Error fetching all products: {str(e)}")
        # Fallback to the general list method
        all_products = product_manager.list(**filters)
        logger.info(f"Falling back to list() method, found {len(all_products)} products")
        return all_products