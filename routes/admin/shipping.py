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
    from routes.admin.tenant_utils import get_selected_tenant, redirect_to_tenant_selection, create_virtual_all_tenant
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
                tenants = tenant_manager.get_all()
            except Exception as e:
                logging.error(f"Error getting tenants in shipping route: {e}")

        # Use helper function to get selected tenant, handling "All Stores" case
        selected_tenant, all_stores_selected = get_selected_tenant(request, tenants)

        # Format tenants for template
        tenants_data = []
        for tenant in tenants:
            tenants_data.append({
                "id": str(tenant.id),
                "name": tenant.name,
                "slug": tenant.slug,
                "domain": tenant.domain,
                "active": tenant.active
            })

        # Add "All Stores" option to tenants if applicable
        if all_stores_selected:
            tenants_data.insert(0, create_virtual_all_tenant())


        return templates.TemplateResponse(
            "admin/shipping.html",
            {
                "request": request,
                "active_page": "shipping",
                "status_message": status_message,
                "status_type": status_type,
                "tenants": tenants_data,
                "selected_tenant": selected_tenant.slug if selected_tenant else None,
                "cart_item_count": request.session.get("cart_item_count", 0),
                "all_stores_selected": all_stores_selected
            }
        )

    return router