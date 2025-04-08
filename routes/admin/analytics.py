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
from pycommerce.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])

# Template setup will be passed from main app
templates = None

# Initialize managers and services
tenant_manager = TenantManager()
analytics_service = AnalyticsService()

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
    
    # Convert dates to datetime objects for the analytics service
    start_datetime = datetime.combine(start, datetime.min.time())
    end_datetime = datetime.combine(end, datetime.max.time())
    
    # Get analytics data from our service
    try:
        analytics_data = analytics_service.get_order_analytics(
            tenant_id=tenant_obj.id,
            start_date=start_datetime,
            end_date=end_datetime,
            previous_period=True
        )
        
        # Add period information to the analytics data
        analytics_data["period"] = period
        analytics_data["period_label"] = period_label
        analytics_data["date_range"] = {
            "start": start.isoformat(),
            "end": end.isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting analytics data: {str(e)}")
        # Provide fallback data structure to avoid template errors
        analytics_data = {
            "period": period,
            "period_label": period_label,
            "date_range": {
                "start": start.isoformat(),
                "end": end.isoformat(),
            },
            "summary": {
                "orders": 0,
                "revenue": 0.0,
                "avg_order_value": 0.0,
                "conversion_rate": 0.0,
            },
            "comparison": {
                "orders": 0.0,
                "revenue": 0.0,
                "avg_order_value": 0.0,
                "conversion_rate": 0.0,
            },
            "orders_by_day": [],
            "top_products": [],
            "traffic_sources": {
                "direct": 0,
                "organic": 0,
                "referral": 0,
                "social": 0,
                "email": 0,
            },
            "device_types": {
                "desktop": 0,
                "mobile": 0,
                "tablet": 0,
            },
            "customer_locations": {
                "United States": 0,
                "Other": 0,
            }
        }
        status_message = f"Error loading analytics data: {str(e)}"
        status_type = "error"
    
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