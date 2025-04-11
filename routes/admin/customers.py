"""
Admin routes for customer management.

This module provides routes for managing customers in the admin interface.
"""
import logging
from typing import Dict, Optional, List

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from pycommerce.models.tenant import TenantManager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])

# Template setup will be passed from main app
templates = None

# Initialize managers
tenant_manager = TenantManager()

class CustomerManager:
    """Simple customer manager class for store customers."""

    @staticmethod
    def get_customers(tenant_id=None):
        """Return a list of customers for a tenant (in a real app, this would query the database)."""
        # This is a placeholder - in a real app we'd query the database
        return [
            {
                "id": "1",
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "555-123-4567",
                "address": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "postal_code": "12345",
                "country": "USA",
                "created_at": "2023-01-01T00:00:00Z",
                "orders_count": 3,
                "total_spent": 158.45
            },
            {
                "id": "2",
                "name": "Jane Smith",
                "email": "jane@example.com",
                "phone": "555-987-6543",
                "address": "456 Oak Ave",
                "city": "Somewhere",
                "state": "NY",
                "postal_code": "67890",
                "country": "USA",
                "created_at": "2023-02-15T00:00:00Z",
                "orders_count": 1,
                "total_spent": 42.99
            }
        ]

    @staticmethod
    def get_customer(customer_id):
        """Return a customer by ID (in a real app, this would query the database)."""
        # This is a placeholder - in a real app we'd query the database
        if customer_id == "1":
            return {
                "id": "1",
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "555-123-4567",
                "address": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "postal_code": "12345",
                "country": "USA",
                "created_at": "2023-01-01T00:00:00Z",
                "orders": [
                    {"id": "1001", "date": "2023-01-05", "total": 49.99, "status": "delivered"},
                    {"id": "1002", "date": "2023-02-10", "total": 78.50, "status": "delivered"},
                    {"id": "1003", "date": "2023-03-15", "total": 29.96, "status": "processing"}
                ]
            }
        elif customer_id == "2":
            return {
                "id": "2",
                "name": "Jane Smith",
                "email": "jane@example.com",
                "phone": "555-987-6543",
                "address": "456 Oak Ave",
                "city": "Somewhere",
                "state": "NY",
                "postal_code": "67890",
                "country": "USA",
                "created_at": "2023-02-15T00:00:00Z",
                "orders": [
                    {"id": "1004", "date": "2023-02-20", "total": 42.99, "status": "delivered"}
                ]
            }
        return None

# Initialize manager
customer_manager = CustomerManager()

@router.get("/customers", response_class=HTMLResponse)
async def list_customers(
    request: Request,
    tenant: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for customer management."""
    # Get tenant from query parameters or session
    selected_tenant_slug = tenant or request.session.get("selected_tenant")

    # If no tenant is selected, redirect to dashboard with message
    if not selected_tenant_slug:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Please+select+a+store+first&status_type=warning", 
            status_code=303
        )

    # Store the selected tenant in session for future requests
    request.session["selected_tenant"] = selected_tenant_slug

    # Get tenant object
    tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
    if not tenant_obj:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Store+not+found&status_type=error", 
            status_code=303
        )

    # Get customers for this tenant or all tenants
    if selected_tenant_slug.lower() == "all":
        try:
            all_tenants = tenant_manager.get_all() or []
            customers = []
            for t in all_tenants:
                customers.extend(customer_manager.get_customers(tenant_id=str(t.id)))
        except Exception as e:
            logger.error(f"Error fetching customers for all tenants: {e}")
            customers = customer_manager.get_customers() # Fallback
    else:
        customers = customer_manager.get_customers(tenant_id=str(tenant_obj.id))


    # Get all tenants for the sidebar
    tenants = tenant_manager.get_all()

    return templates.TemplateResponse(
        "admin/customers.html",
        {
            "request": request,
            "customers": customers,
            "selected_tenant": selected_tenant_slug,
            "tenant": tenant_obj,
            "tenants": tenants,
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
    # Get tenant from query parameters or session
    selected_tenant_slug = tenant or request.session.get("selected_tenant")

    # If no tenant is selected, redirect to dashboard with message
    if not selected_tenant_slug:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Please+select+a+store+first&status_type=warning", 
            status_code=303
        )

    # Store the selected tenant in session for future requests
    request.session["selected_tenant"] = selected_tenant_slug

    # Get tenant object
    tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
    if not tenant_obj:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Store+not+found&status_type=error", 
            status_code=303
        )

    # Get customer
    customer = customer_manager.get_customer(customer_id)
    if not customer:
        raise HTTPException(
            status_code=404,
            detail=f"Customer with ID {customer_id} not found"
        )

    # Get all tenants for the sidebar
    tenants = tenant_manager.get_all()

    return templates.TemplateResponse(
        "admin/customer_detail.html",
        {
            "request": request,
            "customer": customer,
            "selected_tenant": selected_tenant_slug,
            "tenant": tenant_obj,
            "tenants": tenants,
            "active_page": "customers"
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