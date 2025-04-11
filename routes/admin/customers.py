"""
Admin routes for customer management.

This module provides routes for managing customers in the admin interface.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import HTTPException

from pycommerce.models.tenant import TenantManager
# Use the UserManager class from routes.admin.users which has the get_users_by_tenant method
from routes.admin.users import UserManager

from routes.admin.tenant_utils import get_selected_tenant

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])

# Template setup will be passed from main app
templates = None

# Initialize managers
tenant_manager = TenantManager()
user_manager = UserManager()

@router.get("/customers", response_class=HTMLResponse)
async def customers_page(
    request: Request,
    tenant: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for customer management."""
    # Import tenant utils for consistent tenant selection
    from routes.admin.tenant_utils import get_selected_tenant, redirect_to_tenant_selection, create_virtual_all_tenant

    # Get selected tenant using the unified utility
    selected_tenant_slug, tenant_obj = get_selected_tenant(
        request=request, 
        tenant_param=tenant,
        allow_all=True
    )

    # Check if "all" is selected
    is_all_tenants = (selected_tenant_slug == "all")

    # If no tenant is selected, redirect to dashboard with message
    if not selected_tenant_slug:
        return redirect_to_tenant_selection()

    # If tenant not found (and not "all"), redirect to dashboard
    if not is_all_tenants and not tenant_obj:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Store+not+found&status_type=error", 
            status_code=303
        )

    # For "all" tenants case, create a virtual tenant object
    if is_all_tenants:
        tenant_obj = create_virtual_all_tenant()

    # Get all tenants for the sidebar
    tenants = tenant_manager.get_all()

    # Get customers based on tenant selection
    if is_all_tenants:
        customers = []
        for tenant in tenants:
            try:
                # Use the get_users_by_tenant method from UserManager
                tenant_id = tenant.id if hasattr(tenant, 'id') else tenant.get('id')
                tenant_name = tenant.name if hasattr(tenant, 'name') else tenant.get('name')
                
                tenant_customers = user_manager.get_users_by_tenant(str(tenant_id))
                # Add tenant name to each customer for display
                for customer in tenant_customers:
                    if isinstance(customer, dict):
                        customer["tenant_name"] = tenant_name
                    else:
                        customer.tenant_name = tenant_name
                customers.extend(tenant_customers)
            except Exception as e:
                logger.error(f"Error listing customers for tenant {tenant_id}: {e}")

        logger.info(f"Retrieved {len(customers)} customers across all stores")
    else:
        # Use the get_users_by_tenant method from UserManager
        tenant_id = tenant_obj.id if hasattr(tenant_obj, 'id') else tenant_obj.get('id')
        tenant_name = tenant_obj.name if hasattr(tenant_obj, 'name') else tenant_obj.get('name')
        
        customers = user_manager.get_users_by_tenant(str(tenant_id))
        logger.info(f"Retrieved {len(customers)} customers for store {tenant_name}")

    return templates.TemplateResponse(
        "admin/customers.html",
        {
            "request": request,
            "selected_tenant": selected_tenant_slug,
            "tenant": tenant_obj,
            "tenants": tenants,
            "customers": customers,
            "active_page": "customers",
            "status_message": status_message,
            "status_type": status_type
        }
    )

@router.get("/customers/{customer_id}", response_class=HTMLResponse)
async def view_customer(
    request: Request,
    customer_id: str,
    tenant: Optional[str] = None
):
    """View customer details."""
    # Use tenant_utils to get selected tenant
    from routes.admin.tenant_utils import get_selected_tenant, redirect_to_tenant_selection, get_all_tenants, create_virtual_all_tenant

    # Get tenant parameter from request
    tenant_param = tenant or request.query_params.get('tenant')

    # For customer details, we need a specific tenant, not "all"
    selected_tenant_slug, selected_tenant = get_selected_tenant(request, tenant_param, allow_all=False)

    # If no tenant is selected, redirect to dashboard with message
    if not selected_tenant_slug:
        return redirect_to_tenant_selection()

    # Get tenant object (should not be null since allow_all=False)
    # Use the tenant object from get_selected_tenant instead of fetching again
    if not selected_tenant:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Store+not+found&status_type=error", 
            status_code=303
        )

    # Get customer
    customer = user_manager.get_user(customer_id) # Assuming get_user is the correct method.  get_customer is undefined.
    if not customer:
        raise HTTPException(
            status_code=404,
            detail=f"Customer with ID {customer_id} not found"
        )

    # Get all tenants for the dropdown
    all_tenants = tenant_manager.get_all() #Fixed this line as well.

    # Add virtual "All Stores" tenant if needed
    if "all" not in [t.slug for t in all_tenants]:
        all_tenants_with_all = [create_virtual_all_tenant()] + all_tenants
    else:
        all_tenants_with_all = all_tenants

    return templates.TemplateResponse(
        "admin/customer_detail.html",
        {
            "request": request,
            "customer": customer,
            "selected_tenant": selected_tenant_slug,
            "tenant": selected_tenant, # Using selected_tenant here
            "tenants": all_tenants_with_all,
            "active_page": "customers",
            "all_stores_selected": False  # Always false for customer details view
        }
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