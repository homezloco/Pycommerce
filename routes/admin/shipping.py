"""
Shipping management routes for the admin dashboard.

This module provides routes for managing shipping methods, zones, rates, and labels.
"""
import logging
import sys

# Add parent directory to path to allow imports
sys.path.append("..")

try:
    from fastapi import APIRouter, Request, Depends
    from fastapi.templating import Jinja2Templates
    from fastapi.responses import HTMLResponse
    from pycommerce.models.tenant import TenantManager
    from routes.admin.tenant_utils import (
        get_selected_tenant, 
        get_all_tenants,
        redirect_to_tenant_selection, 
        create_virtual_all_tenant
    )
except ImportError as e:
    logging.error(f"Error importing required modules in shipping.py: {e}")

# Initialize managers
tenant_manager = None
try:
    tenant_manager = TenantManager()
except Exception as e:
    logging.error(f"Error initializing managers in shipping.py: {e}")

def setup_routes(templates: Jinja2Templates):
    """
    Set up shipping management routes.

    Args:
        templates: Jinja2Templates for rendering

    Returns:
        APIRouter: FastAPI router with shipping routes
    """
    router = APIRouter()

    @router.get("/admin/shipping", response_class=HTMLResponse)
    async def shipping(request: Request):
        """Shipping management dashboard."""
        status_message = request.query_params.get('status_message')
        status_type = request.query_params.get('status_type', 'info')

        # Get tenants
        tenants = []
        if tenant_manager:
            try:
                tenants = get_all_tenants()
            except Exception as e:
                logging.error(f"Error getting tenants in shipping route: {e}")

        # Add "All Stores" virtual tenant
        all_stores = create_virtual_all_tenant()
        tenants_with_all = [all_stores] + tenants

        # Get selected tenant parameter from request
        tenant_param = request.query_params.get('tenant')

        # Get selected tenant using the utility function
        result = get_selected_tenant(request, tenant_param)
        if len(result) == 2:
            selected_tenant_slug, selected_tenant = result
            is_all_tenants = (selected_tenant_slug == "all")
        else:
            selected_tenant_slug, selected_tenant, is_all_tenants = result

        # Determine if all stores is selected
        all_stores_selected = (selected_tenant_slug == "all")

        # If no tenant is selected, redirect to dashboard with message
        if not selected_tenant_slug:
            return redirect_to_tenant_selection(request, "Please select a store first", "warning")

        # If tenant not found (and not "all"), redirect to dashboard
        if not is_all_tenants and not selected_tenant:
            return redirect_to_tenant_selection(request, "Store not found", "error")


        return templates.TemplateResponse(
            "admin/shipping.html",
            {
                "request": request,
                "active_page": "shipping",
                "status_message": status_message,
                "status_type": status_type,
                "tenants": tenants_with_all,
                "selected_tenant": selected_tenant_slug,
                "tenant": selected_tenant,
                "cart_item_count": request.session.get("cart_item_count", 0),
                "all_stores_selected": all_stores_selected
            }
        )

    return router