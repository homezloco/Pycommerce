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
                       allow_all: bool = True) -> Tuple[str, Optional[Dict[str, Any]]]:
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

def get_current_tenant(request, tenant_manager):
    """
    Get the current tenant based on session and request parameters.

    Args:
        request: The request object
        tenant_manager: The tenant manager instance

    Returns:
        Tuple of (tenant object, tenant_id, tenant_slug)
    """
    # First check for tenant parameter in query string (highest priority)
    tenant_slug = request.query_params.get("tenant")

    # If not in query, check in session
    if not tenant_slug and "selected_tenant" in request.session:
        tenant_slug = request.session.get("selected_tenant")

    # Default to first tenant if none specified
    if not tenant_slug:
        tenants = tenant_manager.list()
        if tenants:
            tenant_slug = tenants[0].slug
        else:
            tenant_slug = None

    # Handle "all" case
    if tenant_slug and tenant_slug.lower() == "all":
        tenant_obj = None
        tenant_id = None
        tenant_slug = "all"

        # Ensure session is properly set for "all" stores
        request.session["selected_tenant"] = "all"
        request.session["tenant_id"] = None
        request.session["tenant_slug"] = "all"
    else:
        # Get the tenant object
        tenant_obj = tenant_manager.get_by_slug(tenant_slug)

        if tenant_obj:
            tenant_id = str(tenant_obj.id)
        else:
            # Tenant not found, default to first available
            tenants = tenant_manager.list()
            if tenants:
                tenant_obj = tenants[0]
                tenant_id = str(tenant_obj.id)
                tenant_slug = tenant_obj.slug
            else:
                tenant_obj = None
                tenant_id = None
                tenant_slug = None

    # Update session with current tenant
    request.session["selected_tenant"] = tenant_slug
    request.session["tenant_id"] = tenant_id
    request.session["tenant_slug"] = tenant_slug

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

def get_items_for_all_tenants(tenant_manager, item_manager, get_method_name, logger, filters=None):
    """
    Generic function to fetch items from all tenants.

    Args:
        tenant_manager: The tenant manager instance
        item_manager: The manager instance for specific items
        get_method_name: The method name to use to get items for a tenant (e.g., 'get_by_tenant')
        logger: The logger to use
        filters: Optional dictionary of filters to apply

    Returns:
        List of items from all tenants
    """
    if filters is None:
        filters = {}

    try:
        # First try to get all tenants
        all_tenants = tenant_manager.list() or []

        # Then fetch items for each tenant and combine them
        all_items = []
        for tenant in all_tenants:
            try:
                # Get the method to call
                get_method = getattr(item_manager, get_method_name)
                tenant_items = get_method(
                    tenant_id=str(tenant.id),
                    **filters
                )
                all_items.extend(tenant_items)
                logger.info(f"Found {len(tenant_items)} items for tenant {tenant.name}")
            except Exception as e:
                logger.error(f"Error fetching items for tenant {tenant.name}: {str(e)}")

        logger.info(f"Found {len(all_items)} items across all stores")

        # If no items found, fall back to list() method if available
        if not all_items and hasattr(item_manager, 'list'):
            logger.info("No items found using tenant queries, trying list() method")
            all_items = item_manager.list(**filters)
            logger.info(f"Found {len(all_items)} items using list() method")

        return all_items
    except Exception as e:
        logger.error(f"Error fetching all items: {str(e)}")
        # Fallback to the general list method if available
        if hasattr(item_manager, 'list'):
            all_items = item_manager.list(**filters)
            logger.info(f"Falling back to list() method, found {len(all_items)} items")
            return all_items
        return []

def get_objects_for_all_tenants(tenant_manager, object_manager, get_method_name, id_param_name='tenant_id', logger=None, filters=None, fallback_method_name=None):
    """
    Generalized function to fetch any object type from all tenants.

    Args:
        tenant_manager: The tenant manager instance
        object_manager: The manager instance for specific objects
        get_method_name: The method name to use to get objects for a tenant
        id_param_name: The parameter name for tenant ID (default: 'tenant_id')
        logger: Optional logger to use
        filters: Optional dictionary of filters to apply
        fallback_method_name: Optional fallback method name if per-tenant fetch fails

    Returns:
        List of objects from all tenants
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    if filters is None:
        filters = {}

    try:
        # First try to get all tenants
        all_tenants = tenant_manager.list() or []

        # Then fetch objects for each tenant and combine them
        all_objects = []
        for tenant in all_tenants:
            try:
                # Get the method to call
                get_method = getattr(object_manager, get_method_name)

                # Create kwargs with the tenant ID parameter
                kwargs = {id_param_name: str(tenant.id)}
                kwargs.update(filters)

                # Call the method
                tenant_objects = get_method(**kwargs)

                # Check if result is None
                if tenant_objects is None:
                    tenant_objects = []

                # If not a list, make it a list
                if not isinstance(tenant_objects, list):
                    tenant_objects = [tenant_objects]

                all_objects.extend(tenant_objects)
                logger.info(f"Found {len(tenant_objects)} objects for tenant {tenant.name}")
            except Exception as e:
                logger.error(f"Error fetching objects for tenant {tenant.name}: {str(e)}")

        logger.info(f"Found {len(all_objects)} objects across all stores")

        # If no objects found and fallback method is provided, try it
        if not all_objects and fallback_method_name and hasattr(object_manager, fallback_method_name):
            logger.info(f"No objects found using tenant queries, trying {fallback_method_name}() method")
            fallback_method = getattr(object_manager, fallback_method_name)
            all_objects = fallback_method(**filters)

            # Check if result is None
            if all_objects is None:
                all_objects = []

            # If not a list, make it a list
            if not isinstance(all_objects, list):
                all_objects = [all_objects]

            logger.info(f"Found {len(all_objects)} objects using {fallback_method_name}() method")

        return all_objects
    except Exception as e:
        logger.error(f"Error fetching all objects: {str(e)}")

        # Fallback to the general method if available
        if fallback_method_name and hasattr(object_manager, fallback_method_name):
            try:
                fallback_method = getattr(object_manager, fallback_method_name)
                all_objects = fallback_method(**filters)

                # Check if result is None
                if all_objects is None:
                    all_objects = []

                # If not a list, make it a list
                if not isinstance(all_objects, list):
                    all_objects = [all_objects]

                logger.info(f"Falling back to {fallback_method_name}() method, found {len(all_objects)} objects")
                return all_objects
            except Exception as fallback_err:
                logger.error(f"Error with fallback method: {str(fallback_err)}")

        return []

def get_orders_for_all_tenants(tenant_manager, order_manager, logger, filters=None):
    """
    Fetch orders from all tenants.

    Args:
        tenant_manager: The tenant manager instance
        order_manager: The order manager instance
        logger: The logger to use
        filters: Optional dictionary of filters to apply

    Returns:
        List of orders from all tenants
    """
    if filters is None:
        filters = {}

    try:
        # First try to get all tenants
        all_tenants = tenant_manager.list() or []

        # Then fetch orders for each tenant and combine them
        all_orders = []
        for tenant in all_tenants:
            try:
                tenant_orders = order_manager.get_for_tenant(
                    tenant_id=str(tenant.id),
                    filters=filters
                )
                all_orders.extend(tenant_orders)
                logger.info(f"Found {len(tenant_orders)} orders for tenant {tenant.name}")
            except Exception as e:
                logger.error(f"Error fetching orders for tenant {tenant.name}: {str(e)}")

        logger.info(f"Found {len(all_orders)} orders across all stores")

        # If no orders found, fall back to a list method if available
        if not all_orders and hasattr(order_manager, 'list'):
            logger.info("No orders found using tenant queries, trying list() method")
            all_orders = order_manager.list(**filters)
            logger.info(f"Found {len(all_orders)} orders using list() method")

        return all_orders
    except Exception as e:
        logger.error(f"Error fetching all orders: {str(e)}")
        # Fallback to the general list method if available
        if hasattr(order_manager, 'list'):
            all_orders = order_manager.list(**filters)
            logger.info(f"Falling back to list() method, found {len(all_orders)} orders")
            return all_orders
        return []

def get_categories_for_all_tenants(tenant_manager, category_manager, logger, include_inactive=False):
    """
    Fetch categories from all tenants.

    Args:
        tenant_manager: The tenant manager instance
        category_manager: The category manager instance
        logger: The logger to use
        include_inactive: Whether to include inactive categories

    Returns:
        List of categories from all tenants
    """
    try:
        # First try to get all tenants
        all_tenants = tenant_manager.list() or []

        # Then fetch categories for each tenant and combine them
        all_categories = []
        for tenant in all_tenants:
            try:
                if category_manager:
                    tenant_categories = category_manager.get_all_categories(
                        tenant_id=str(tenant.id),
                        include_inactive=include_inactive
                    )
                    logger.info(f"Found {len(tenant_categories)} categories for tenant {tenant.name}")

                    # Add tenant name to category objects for display
                    for category in tenant_categories:
                        category.tenant_name = tenant.name
                        all_categories.append(category)
                else:
                    logger.warning(f"Category manager not available for tenant {tenant.name}")
            except Exception as e:
                logger.error(f"Error fetching categories for tenant {tenant.name}: {str(e)}")

        logger.info(f"Found {len(all_categories)} categories across all stores")
        return all_categories
    except Exception as e:
        logger.error(f"Error fetching categories from all tenants: {str(e)}")
        return []