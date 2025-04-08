"""
Admin routes for marketing management.

This module provides routes for managing marketing in the admin interface.
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

@router.get("/marketing", response_class=HTMLResponse)
async def marketing_dashboard(
    request: Request,
    tenant: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for marketing dashboard."""
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
    
    # Marketing metrics (in a real app, these would come from a database)
    metrics = {
        "total_visitors": 1250,
        "conversion_rate": 3.2,
        "average_order_value": 75.40,
        "revenue": 3024.58,
        "newsletter_subscribers": 425,
        "active_discounts": 2
    }
    
    # Recent campaigns (in a real app, these would come from a database)
    campaigns = [
        {
            "id": "1",
            "name": "Summer Sale 2023",
            "type": "discount",
            "status": "active",
            "start_date": "2023-06-01",
            "end_date": "2023-08-31",
            "metrics": {
                "views": 450,
                "conversions": 25,
                "revenue": 1875.50
            }
        },
        {
            "id": "2",
            "name": "New Customer Welcome",
            "type": "email",
            "status": "active",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "metrics": {
                "emails_sent": 120,
                "open_rate": 45.8,
                "click_rate": 12.5,
                "conversions": 8
            }
        }
    ]
    
    return templates.TemplateResponse(
        "admin/marketing.html",
        {
            "request": request,
            "selected_tenant": selected_tenant_slug,
            "tenant": tenant_obj,
            "tenants": tenants,
            "active_page": "marketing",
            "metrics": metrics,
            "campaigns": campaigns,
            "status_message": status_message,
            "status_type": status_type
        }
    )

@router.get("/marketing/discounts", response_class=HTMLResponse)
async def discounts_page(
    request: Request,
    tenant: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for discount management."""
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
    
    # Discounts (in a real app, these would come from a database)
    discounts = [
        {
            "id": "1",
            "code": "SUMMER23",
            "type": "percentage",
            "value": 20,
            "status": "active",
            "start_date": "2023-06-01",
            "end_date": "2023-08-31",
            "min_purchase": 50.0,
            "usage_limit": 100,
            "used_count": 25
        },
        {
            "id": "2",
            "code": "WELCOME10",
            "type": "fixed",
            "value": 10,
            "status": "active",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "min_purchase": 0.0,
            "usage_limit": 0, # No limit
            "used_count": 42
        }
    ]
    
    return templates.TemplateResponse(
        "admin/discounts.html",
        {
            "request": request,
            "selected_tenant": selected_tenant_slug,
            "tenant": tenant_obj,
            "tenants": tenants,
            "active_page": "marketing",
            "discounts": discounts,
            "status_message": status_message,
            "status_type": status_type
        }
    )

@router.get("/marketing/newsletters", response_class=HTMLResponse)
async def newsletters_page(
    request: Request,
    tenant: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for newsletter management."""
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
    
    # Newsletter templates (in a real app, these would come from a database)
    templates_list = [
        {
            "id": "1",
            "name": "Monthly Newsletter",
            "subject": "What's New This Month?",
            "created_at": "2023-01-15",
            "last_sent": "2023-06-01",
            "open_rate": 42.5,
            "click_rate": 12.3
        },
        {
            "id": "2",
            "name": "Welcome Email",
            "subject": "Welcome to Our Store!",
            "created_at": "2023-02-10",
            "last_sent": "2023-06-15",
            "open_rate": 68.2,
            "click_rate": 24.7
        }
    ]
    
    # Subscriber statistics
    subscriber_stats = {
        "total": 425,
        "active": 412,
        "unsubscribed": 13,
        "growth_rate": 5.2, # % growth in the last 30 days
        "sources": {
            "checkout": 210,
            "signup_form": 150,
            "imported": 65
        }
    }
    
    return templates.TemplateResponse(
        "admin/newsletters.html",
        {
            "request": request,
            "selected_tenant": selected_tenant_slug,
            "tenant": tenant_obj,
            "tenants": tenants,
            "active_page": "marketing",
            "templates": templates_list,
            "subscriber_stats": subscriber_stats,
            "status_message": status_message,
            "status_type": status_type
        }
    )

@router.get("/marketing/analytics", response_class=HTMLResponse)
async def analytics_page(
    request: Request,
    tenant: Optional[str] = None,
    period: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for analytics."""
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
    
    # Period can be: today, week, month, year
    period = period or "month"
    
    # Analytics data (in a real app, these would come from a database)
    analytics = {
        "visitors": {
            "total": 1250,
            "new": 875,
            "returning": 375,
            "bounce_rate": 45.2
        },
        "sales": {
            "total": 3024.58,
            "average_order": 75.40,
            "conversion_rate": 3.2
        },
        "products": {
            "viewed": [
                {"name": "Product A", "views": 450},
                {"name": "Product B", "views": 320},
                {"name": "Product C", "views": 280}
            ],
            "purchased": [
                {"name": "Product A", "purchases": 25},
                {"name": "Product B", "purchases": 18},
                {"name": "Product C", "purchases": 12}
            ]
        },
        "traffic_sources": {
            "direct": 35.2,
            "search": 28.7,
            "social": 18.5,
            "referral": 12.1,
            "other": 5.5
        }
    }
    
    return templates.TemplateResponse(
        "admin/analytics.html",
        {
            "request": request,
            "selected_tenant": selected_tenant_slug,
            "tenant": tenant_obj,
            "tenants": tenants,
            "active_page": "marketing",
            "analytics": analytics,
            "period": period,
            "status_message": status_message,
            "status_type": status_type
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