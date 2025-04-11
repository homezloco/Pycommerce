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
    
    # Handle multi-value tenant slug (list)
    if isinstance(selected_tenant_slug, list):
        selected_tenant_slug = selected_tenant_slug[0] if selected_tenant_slug else None
    
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
        if selected_tenant_slug.lower() == "all":
            # Fetch analytics for all tenants
            logger.info("Fetching analytics for all stores")
            try:
                # First try to get all tenants
                all_tenants = tenant_manager.list() or []
                
                # Initialize combined analytics data
                combined_analytics = {
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
                    "customer_locations": {}
                }
                
                # Fetch analytics for each tenant and combine them
                for tenant in all_tenants:
                    try:
                        tenant_analytics = analytics_service.get_order_analytics(
                            tenant_id=str(tenant.id),
                            start_date=start_datetime,
                            end_date=end_datetime,
                            previous_period=True
                        )
                        
                        # Add to combined summary
                        if "summary" in tenant_analytics:
                            combined_analytics["summary"]["orders"] += tenant_analytics["summary"].get("orders", 0)
                            combined_analytics["summary"]["revenue"] += tenant_analytics["summary"].get("revenue", 0.0)
                            # We'll recalculate average order value later
                        
                        # Add to top products
                        if "top_products" in tenant_analytics:
                            combined_analytics["top_products"].extend(tenant_analytics["top_products"])
                        
                        # Add to location data
                        if "customer_locations" in tenant_analytics:
                            for location, count in tenant_analytics["customer_locations"].items():
                                if location in combined_analytics["customer_locations"]:
                                    combined_analytics["customer_locations"][location] += count
                                else:
                                    combined_analytics["customer_locations"][location] = count
                                    
                        # Add traffic sources
                        if "traffic_sources" in tenant_analytics:
                            for source, count in tenant_analytics["traffic_sources"].items():
                                combined_analytics["traffic_sources"][source] += count
                        
                        # Add device types
                        if "device_types" in tenant_analytics:
                            for device, count in tenant_analytics["device_types"].items():
                                combined_analytics["device_types"][device] += count
                                
                        logger.info(f"Added analytics for tenant {tenant.name}")
                    except Exception as e:
                        logger.error(f"Error fetching analytics for tenant {tenant.name}: {str(e)}")
                
                # Calculate average order value for combined data
                if combined_analytics["summary"]["orders"] > 0:
                    combined_analytics["summary"]["avg_order_value"] = combined_analytics["summary"]["revenue"] / combined_analytics["summary"]["orders"]
                
                # Sort top products by revenue and limit to top 10
                combined_analytics["top_products"] = sorted(
                    combined_analytics["top_products"], 
                    key=lambda x: x.get("revenue", 0), 
                    reverse=True
                )[:10]
                
                analytics_data = combined_analytics
                logger.info(f"Combined analytics data for all stores")
            except Exception as e:
                logger.error(f"Error combining analytics data: {str(e)}")
                # Fallback to empty structure
                analytics_data = {
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
                    "traffic_sources": {},
                    "device_types": {},
                    "customer_locations": {}
                }
        else:
            # Regular single tenant analytics
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