"""
Admin routes for analytics.

This module provides routes for analytics in the admin interface.
"""
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta

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

@router.get("/analytics", response_class=HTMLResponse)
async def analytics_dashboard(
    request: Request,
    tenant: Optional[str] = None,
    period: Optional[str] = "month",  # day, week, month, year
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for analytics dashboard."""
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
    
    # Get all tenants for the sidebar
    tenants = tenant_manager.get_all()
    
    # Calculate date range based on period
    today = datetime.now().date()
    if period == "day":
        start = today
        end = today
        period_label = "Today"
    elif period == "week":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        period_label = f"{start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}"
    elif period == "month":
        start = today.replace(day=1)
        if today.month == 12:
            end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        period_label = start.strftime('%B %Y')
    elif period == "year":
        start = today.replace(month=1, day=1)
        end = today.replace(month=12, day=31)
        period_label = start.strftime('%Y')
    else:  # Custom date range
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                period_label = f"{start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}"
            except ValueError:
                start = today.replace(day=1)
                end = (today.replace(month=today.month + 1, day=1) if today.month < 12 
                      else today.replace(year=today.year + 1, month=1, day=1)) - timedelta(days=1)
                period_label = start.strftime('%B %Y')
        else:
            start = today.replace(day=1)
            end = (today.replace(month=today.month + 1, day=1) if today.month < 12 
                  else today.replace(year=today.year + 1, month=1, day=1)) - timedelta(days=1)
            period_label = start.strftime('%B %Y')
    
    # In a real app, fetch analytics data from a database or analytics service
    # For demo purposes, we'll use placeholder data
    analytics_data = {
        "period": period,
        "period_label": period_label,
        "date_range": {
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
        "summary": {
            "orders": 156,
            "revenue": 12485.75,
            "avg_order_value": 80.04,
            "conversion_rate": 3.25,
        },
        "comparison": {
            "orders": +12.5,  # percent change from previous period
            "revenue": +8.3,
            "avg_order_value": -2.1,
            "conversion_rate": +0.5,
        },
        "orders_by_day": [
            {"date": "2023-06-01", "orders": 5, "revenue": 425.80},
            {"date": "2023-06-02", "orders": 8, "revenue": 632.40},
            {"date": "2023-06-03", "orders": 12, "revenue": 956.76},
            # ... more days ...
        ],
        "top_products": [
            {"name": "Product A", "orders": 45, "revenue": 3150.75},
            {"name": "Product B", "orders": 38, "revenue": 2678.50},
            {"name": "Product C", "orders": 29, "revenue": 1885.00},
            # ... more products ...
        ],
        "traffic_sources": {
            "direct": 35,
            "organic": 25,
            "referral": 15,
            "social": 20,
            "email": 5,
        },
        "device_types": {
            "desktop": 45,
            "mobile": 40,
            "tablet": 15,
        },
        "customer_locations": {
            "United States": 65,
            "Canada": 15,
            "United Kingdom": 10,
            "Australia": 5,
            "Other": 5,
        }
    }
    
    return templates.TemplateResponse(
        "admin/analytics.html",
        {
            "request": request,
            "selected_tenant": selected_tenant_slug,
            "tenant": tenant_obj,
            "tenants": tenants,
            "active_page": "analytics",
            "analytics": analytics_data,
            "status_message": status_message,
            "status_type": status_type,
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