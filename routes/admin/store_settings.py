"""
Admin routes for store settings.

This module provides routes for managing store settings in the admin interface.
"""
import logging
from typing import Dict, Optional

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

@router.get("/store-settings", response_class=HTMLResponse)
async def store_settings(
    request: Request,
    tenant: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for store settings."""
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
    
    # Get store settings
    store_settings = tenant_obj.settings or {}
    
    # Get all tenants for the sidebar
    tenants = tenant_manager.get_all()
    
    return templates.TemplateResponse(
        "admin/store_settings.html",
        {
            "request": request,
            "selected_tenant": selected_tenant_slug,
            "tenant": tenant_obj,
            "tenants": tenants,
            "active_page": "store-settings",
            "store_settings": store_settings,
            "status_message": status_message,
            "status_type": status_type
        }
    )

@router.post("/store-settings/update", response_class=RedirectResponse)
async def update_store_settings(
    request: Request,
    tenant_id: str = Form(...),
    store_name: str = Form(...),
    store_email: str = Form(...),
    store_phone: Optional[str] = Form(None),
    store_address: Optional[str] = Form(None),
    store_city: Optional[str] = Form(None),
    store_state: Optional[str] = Form(None),
    store_country: Optional[str] = Form(None),
    store_zip: Optional[str] = Form(None),
    store_currency: str = Form("USD"),
    store_language: str = Form("en-US"),
    store_timezone: str = Form("UTC"),
    store_tax_rate: float = Form(0.0),
    store_shipping_rate: float = Form(0.0)
):
    """Update store settings."""
    try:
        # Get tenant
        tenant = tenant_manager.get(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=404,
                detail=f"Store with ID {tenant_id} not found"
            )
        
        # Update tenant settings
        settings = tenant.settings or {}
        settings.update({
            "store_name": store_name,
            "store_email": store_email,
            "store_phone": store_phone,
            "store_address": store_address,
            "store_city": store_city,
            "store_state": store_state,
            "store_country": store_country,
            "store_zip": store_zip,
            "store_currency": store_currency,
            "store_language": store_language,
            "store_timezone": store_timezone,
            "store_tax_rate": store_tax_rate,
            "store_shipping_rate": store_shipping_rate
        })
        
        # Save updated settings
        tenant_manager.update_settings(tenant_id, settings)
        
        # Get tenant slug for redirect
        tenant_slug = tenant.slug
        
        return RedirectResponse(
            url=f"/admin/store-settings?tenant={tenant_slug}&status_message=Store+settings+updated+successfully&status_type=success",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Error updating store settings: {str(e)}")
        return RedirectResponse(
            url=f"/admin/store-settings?tenant={tenant.slug if tenant else ''}&status_message=Error+updating+store+settings:+{str(e)}&status_type=danger",
            status_code=status.HTTP_303_SEE_OTHER
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