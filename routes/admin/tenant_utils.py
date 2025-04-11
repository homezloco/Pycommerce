"""
Utility functions for tenant management in admin routes.

This module provides utility functions for consistent tenant handling
across all admin routes in PyCommerce.
"""
import logging
from typing import Optional, Dict, Any, Tuple

from fastapi import Request
from pycommerce.models.tenant import TenantManager

logger = logging.getLogger(__name__)

def get_current_tenant(
    request: Request, 
    tenant_manager: TenantManager,
    default_tenant_slug: str = "tech"
) -> Tuple[Any, str, str]:
    """
    Get the current tenant based on session data and URL parameters.
    
    This utility function provides consistent tenant selection logic for all admin routes.
    It prioritizes tenant selection in this order:
    1. Request query parameter 'tenant'
    2. Session value for 'selected_tenant'
    3. Session value for 'tenant_id' (with lookup to get the slug)
    4. Default tenant slug provided
    
    Args:
        request: FastAPI request object
        tenant_manager: Instance of TenantManager
        default_tenant_slug: Default tenant slug to use if no tenant is found
        
    Returns:
        Tuple of (tenant_object, tenant_id, tenant_slug)
    """
    # First check if there's a tenant parameter in the request
    query_tenant = request.query_params.get('tenant')
    
    # Get tenant from session - prioritize selected_tenant (from store switcher)
    session_tenant_slug = request.session.get("selected_tenant")
    session_tenant_id = request.session.get("tenant_id")
    
    # The tenant slug we'll use
    tenant_slug = None
    
    # Initialize tenant_obj and tenant_id for later use
    tenant_obj = None
    tenant_id = ""  # Initialize as empty string instead of None
    
    # Priority 1: Use query parameter if available
    if query_tenant:
        tenant_slug = query_tenant
        logger.info(f"Using tenant from query parameter: {tenant_slug}")
    
    # Priority 2: Use session tenant slug if available
    elif session_tenant_slug:
        tenant_slug = session_tenant_slug
        logger.info(f"Using tenant from session (selected_tenant): {tenant_slug}")
    
    # Priority 3: Try to lookup tenant by ID from session
    elif session_tenant_id:
        logger.info(f"Looking up tenant by ID from session: {session_tenant_id}")
        # Try to find the tenant by ID
        try:
            # Get all tenants and find the one with matching ID
            tenants_list = tenant_manager.list() or []
            for tenant in tenants_list:
                if str(tenant.id) == str(session_tenant_id):
                    tenant_obj = tenant
                    tenant_slug = tenant.slug
                    tenant_id = str(tenant.id)
                    logger.info(f"Found tenant {tenant_slug} by ID: {tenant_id}")
                    break
            
            if not tenant_obj:
                logger.warning(f"No tenant found for ID: {session_tenant_id}")
        except Exception as e:
            logger.error(f"Error looking up tenant by ID: {e}")
    
    # Priority 4: Use default tenant slug
    if not tenant_slug:
        tenant_slug = default_tenant_slug
        logger.info(f"Using default tenant: {tenant_slug}")
    
    # Now get or confirm the tenant object and ID
    if not tenant_obj:
        try:
            tenant_obj = tenant_manager.get_by_slug(tenant_slug)
            
            if tenant_obj:
                tenant_id = str(tenant_obj.id)
                # Update session values for consistency
                request.session["selected_tenant"] = tenant_slug
                request.session["tenant_id"] = tenant_id
                logger.info(f"Found tenant_id: {tenant_id} for slug: {tenant_slug}")
            else:
                logger.warning(f"No tenant found for slug: {tenant_slug}")
                # Try to get first available tenant
                try:
                    tenants_list = tenant_manager.list() or []
                    if tenants_list and len(tenants_list) > 0:
                        tenant_obj = tenants_list[0]
                        tenant_id = str(tenant_obj.id)
                        tenant_slug = tenant_obj.slug
                        # Update session
                        request.session["selected_tenant"] = tenant_slug
                        request.session["tenant_id"] = tenant_id
                        logger.info(f"Using first available tenant: {tenant_slug} ({tenant_id})")
                except Exception as e:
                    logger.error(f"Error finding alternative tenant: {e}")
        except Exception as e:
            logger.error(f"Error looking up tenant by slug: {e}")
    
    # Ensure we always return string values, not None
    if tenant_id is None:
        tenant_id = ""
    if tenant_slug is None:
        tenant_slug = default_tenant_slug
        
    return tenant_obj, tenant_id, tenant_slug