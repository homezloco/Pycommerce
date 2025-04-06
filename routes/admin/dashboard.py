"""
Admin routes for dashboard and core admin functionality.

This module contains dashboard and other core admin functionality.
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

# Template setup will be passed from main app
templates = None

# Initialize logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])

# Import models and managers
try:
    from pycommerce.models.tenant import TenantManager
    from pycommerce.models.product import ProductManager
    from pycommerce.models.order import OrderManager, OrderStatus
    
    # Initialize managers
    tenant_manager = TenantManager()
    product_manager = ProductManager()
    order_manager = OrderManager()
except ImportError as e:
    logger.error(f"Error importing dashboard modules: {str(e)}")

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, status_message: Optional[str] = None, status_type: str = "info"):
    """Admin dashboard page."""
    # Get tenants
    tenants = tenant_manager.get_all()
    
    # Get selected tenant from session or use the first tenant
    selected_tenant_slug = request.session.get("selected_tenant")
    selected_tenant = None
    
    if selected_tenant_slug:
        selected_tenant = tenant_manager.get_by_slug(selected_tenant_slug)
    
    # If no tenant is selected or the selected tenant doesn't exist,
    # use the first available tenant
    if not selected_tenant and tenants:
        selected_tenant = tenants[0]
        request.session["selected_tenant"] = selected_tenant.slug
    
    # Dashboard data
    dashboard_data = {
        "products_count": 0,
        "orders_count": 0,
        "orders_pending": 0,
        "revenue": 0,
        "recent_orders": []
    }
    
    if selected_tenant:
        # Get counts and summary data for the selected tenant
        products = product_manager.get_by_tenant(selected_tenant.id)
        dashboard_data["products_count"] = len(products)
        
        orders = order_manager.get_for_tenant(selected_tenant.id)
        dashboard_data["orders_count"] = len(orders)
        
        # Get pending orders count
        pending_orders = [order for order in orders if order.status == OrderStatus.PENDING]
        dashboard_data["orders_pending"] = len(pending_orders)
        
        # Calculate revenue from completed orders
        completed_orders = [order for order in orders if order.status == OrderStatus.COMPLETED]
        dashboard_data["revenue"] = sum(order.total for order in completed_orders)
        
        # Get recent orders
        recent_orders = sorted(orders, key=lambda x: x.created_at, reverse=True)[:5]
        recent_orders_data = []
        
        for order in recent_orders:
            recent_orders_data.append({
                "id": str(order.id),
                "customer_name": f"{order.shipping_address.get('first_name', '')} {order.shipping_address.get('last_name', '')}",
                "total": order.total,
                "status": order.status.value,
                "created_at": order.created_at
            })
        
        dashboard_data["recent_orders"] = recent_orders_data
    
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
    
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "tenants": tenants_data,
            "selected_tenant": selected_tenant.slug if selected_tenant else None,
            "dashboard": dashboard_data,
            "status_message": status_message,
            "status_type": status_type,
            "cart_item_count": request.session.get("cart_item_count", 0)
        }
    )

@router.get("/change-store", response_class=RedirectResponse)
async def admin_change_store(request: Request, tenant: str = ""):
    """Change the selected store for admin management."""
    if tenant:
        # Verify tenant exists
        tenant_obj = tenant_manager.get_by_slug(tenant)
        if tenant_obj:
            # Store in session
            request.session["selected_tenant"] = tenant
            return RedirectResponse(
                url="/admin/dashboard?status_message=Store+changed+successfully&status_type=success", 
                status_code=303
            )
    
    # If tenant doesn't exist or no tenant provided, redirect back to dashboard
    return RedirectResponse(url="/admin/dashboard", status_code=303)

def setup_routes(app_templates):
    """
    Set up routes with the given templates.
    
    Args:
        app_templates: Jinja2Templates instance from the main app
    """
    global templates
    templates = app_templates
    return router