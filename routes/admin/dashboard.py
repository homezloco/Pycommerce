"""
Admin routes for dashboard and core admin functionality.

This module contains dashboard and other core admin functionality.
"""
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import calendar
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

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
    from pycommerce.models.order import OrderManager, OrderStatus, OrderType
    from pycommerce.models.user import UserManager
    
    # Initialize managers
    tenant_manager = TenantManager()
    product_manager = ProductManager()
    order_manager = OrderManager()
    user_manager = UserManager()
except ImportError as e:
    logger.error(f"Error importing dashboard modules: {str(e)}")

def get_date_range(time_period: str) -> tuple:
    """Get start and end dates based on the selected time period."""
    today = datetime.utcnow()
    
    if time_period == "today":
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif time_period == "yesterday":
        yesterday = today - timedelta(days=1)
        start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif time_period == "last7days":
        start_date = (today - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif time_period == "last30days":
        start_date = (today - timedelta(days=29)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif time_period == "thismonth":
        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif time_period == "lastmonth":
        last_month = today.month - 1
        year = today.year
        if last_month == 0:
            last_month = 12
            year -= 1
        
        # Get the last day of the month
        last_day = calendar.monthrange(year, last_month)[1]
        
        start_date = datetime(year, last_month, 1, 0, 0, 0, 0)
        end_date = datetime(year, last_month, last_day, 23, 59, 59, 999999)
    else:  # default to last 7 days
        start_date = (today - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return start_date, end_date

def get_sales_data_by_period(tenant_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get daily sales data for the given period."""
    filters = {
        "date_from": start_date,
        "date_to": end_date
    }
    
    orders = order_manager.get_for_tenant(tenant_id, filters)
    
    # Initialize data structure for sales by day
    delta = end_date.date() - start_date.date()
    days = [start_date.date() + timedelta(days=i) for i in range(delta.days + 1)]
    
    daily_revenue = {day.strftime("%Y-%m-%d"): 0.0 for day in days}
    daily_orders = {day.strftime("%Y-%m-%d"): 0 for day in days}
    
    # Process orders
    completed_statuses = ["COMPLETED", "DELIVERED", "SHIPPED"]
    total_revenue = 0.0
    order_count = len(orders)
    completed_count = 0
    
    # Process orders by date
    for order in orders:
        order_date = order.created_at.date().strftime("%Y-%m-%d")
        if order_date in daily_orders:
            daily_orders[order_date] += 1
            
            # Only count revenue for completed/shipped/delivered orders
            if order.status in completed_statuses or str(order.status) in completed_statuses:
                daily_revenue[order_date] += order.total
                total_revenue += order.total
                completed_count += 1
    
    # Convert to lists for Chart.js
    dates = list(daily_revenue.keys())
    revenue_data = list(daily_revenue.values())
    orders_data = list(daily_orders.values())
    
    # Get top products for this period
    product_sales = defaultdict(lambda: {"quantity": 0, "revenue": 0.0})
    product_ids = set()
    
    for order in orders:
        for item in order.items:
            product_id = item.product_id
            product_ids.add(product_id)
            product_sales[product_id]["quantity"] += item.quantity
            product_sales[product_id]["revenue"] += (item.price * item.quantity)
    
    # Look up product details for the top products
    products = {}
    if product_ids:
        for product_id in product_ids:
            product = product_manager.get_by_id(product_id)
            if product:
                products[product_id] = {
                    "name": product.name,
                    "price": product.price,
                    "sku": product.sku
                }
    
    # Create top products list with complete info
    top_products = []
    for product_id, sales_data in product_sales.items():
        if product_id in products:
            top_products.append({
                "id": product_id,
                "name": products[product_id]["name"],
                "price": products[product_id]["price"],
                "quantity": sales_data["quantity"],
                "revenue": sales_data["revenue"]
            })
    
    # Sort by revenue (highest first)
    top_products.sort(key=lambda x: x["revenue"], reverse=True)
    top_products = top_products[:5]  # Limit to top 5
    
    return {
        "dates": dates,
        "revenue_data": revenue_data,
        "orders_data": orders_data,
        "total_revenue": total_revenue,
        "order_count": order_count,
        "completed_count": completed_count,
        "top_products": top_products
    }

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request, 
    status_message: Optional[str] = None, 
    status_type: str = "info",
    time_period: str = "last7days"
):
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
    
    # Get date range based on selected time period
    start_date, end_date = get_date_range(time_period)
    
    # Dashboard data
    dashboard_data = {
        "products_count": 0,
        "orders_count": 0,
        "orders_pending": 0,
        "revenue": 0,
        "recent_orders": [],
        "sales_data": {
            "dates": [],
            "revenue_data": [],
            "orders_data": [],
            "top_products": []
        },
        "customers_count": 0,
        "time_period": time_period
    }
    
    if selected_tenant:
        # Get counts and summary data for the selected tenant
        products = product_manager.get_by_tenant(str(selected_tenant.id))
        dashboard_data["products_count"] = len(products)
        
        # Get all users (customers)
        users = user_manager.get_all()
        dashboard_data["customers_count"] = len(users)
        
        # Get orders for the selected time period
        filters = {
            "date_from": start_date,
            "date_to": end_date
        }
        
        orders = order_manager.get_for_tenant(str(selected_tenant.id), filters)
        dashboard_data["orders_count"] = len(orders)
        
        # Get pending orders count
        pending_orders = [order for order in orders if order.status == "PENDING" or str(order.status) == "PENDING"]
        dashboard_data["orders_pending"] = len(pending_orders)
        
        # Calculate revenue from completed orders
        completed_statuses = ["COMPLETED", "DELIVERED", "SHIPPED"]
        completed_orders = [order for order in orders if order.status in completed_statuses or str(order.status) in completed_statuses]
        dashboard_data["revenue"] = sum(order.total for order in completed_orders)
        
        # Get recent orders - last 5 regardless of time period
        all_orders = order_manager.get_for_tenant(str(selected_tenant.id))
        recent_orders = sorted(all_orders, key=lambda x: x.created_at, reverse=True)[:5]
        recent_orders_data = []
        
        for order in recent_orders:
            # Create customer name from available fields
            customer_name = order.customer_name if hasattr(order, 'customer_name') and order.customer_name else ""
            if not customer_name and hasattr(order, 'shipping_address_line1') and order.shipping_address_line1:
                # If we have shipping info but no customer name, use that
                customer_name = f"{order.shipping_address_line1}"
            
            # Append order data
            recent_orders_data.append({
                "id": str(order.id),
                "customer_name": customer_name,
                "total": order.total,
                "status": order.status if isinstance(order.status, str) else order.status.name if hasattr(order.status, "name") else str(order.status),
                "created_at": order.created_at
            })
        
        dashboard_data["recent_orders"] = recent_orders_data
        
        # Get detailed sales data for charts
        sales_data = get_sales_data_by_period(
            str(selected_tenant.id),
            start_date,
            end_date
        )
        
        dashboard_data["sales_data"] = sales_data
    
    # Format tenants for template with order and revenue counts
    tenants_data = []
    for tenant in tenants:
        tenant_orders = order_manager.get_for_tenant(str(tenant.id))
        orders_count = len(tenant_orders)
        completed_statuses = ["COMPLETED", "DELIVERED", "SHIPPED"]
        completed_orders = [order for order in tenant_orders if order.status in completed_statuses or str(order.status) in completed_statuses]
        revenue = sum(order.total for order in completed_orders)
        
        tenants_data.append({
            "id": str(tenant.id),
            "name": tenant.name,
            "slug": tenant.slug,
            "domain": tenant.domain,
            "active": tenant.active,
            "orders_count": orders_count,
            "revenue": revenue
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

@router.get("/dashboard/data", response_class=JSONResponse)
async def admin_dashboard_data(
    request: Request,
    time_period: str = "last7days"
):
    """API endpoint to get dashboard data for charts."""
    # Get selected tenant from session
    selected_tenant_slug = request.session.get("selected_tenant")
    
    if not selected_tenant_slug:
        return JSONResponse(content={"error": "No tenant selected"}, status_code=400)
    
    selected_tenant = tenant_manager.get_by_slug(selected_tenant_slug)
    
    if not selected_tenant:
        return JSONResponse(content={"error": "Selected tenant not found"}, status_code=404)
    
    # Get date range based on selected time period
    start_date, end_date = get_date_range(time_period)
    
    # Get detailed sales data for charts
    sales_data = get_sales_data_by_period(
        str(selected_tenant.id),
        start_date,
        end_date
    )
    
    return JSONResponse(content=sales_data)

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