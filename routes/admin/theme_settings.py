"""
Admin routes for theme settings.

This module provides routes for managing theme settings in the admin interface.
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

@router.get("/theme-settings", response_class=HTMLResponse)
async def theme_settings_page(
    request: Request,
    tenant: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for theme settings."""
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
    
    # Get theme settings
    theme = tenant_obj.settings or {}
    
    # Get all tenants for the sidebar
    tenants = tenant_manager.get_all()
    
    # Font families
    font_families = [
        "Arial, sans-serif",
        "Helvetica, sans-serif",
        "Verdana, sans-serif",
        "Georgia, serif",
        "Tahoma, sans-serif",
        "Times New Roman, serif",
        "Courier New, monospace",
        "Roboto, sans-serif",
        "Open Sans, sans-serif",
        "Lato, sans-serif",
    ]
    
    # Logo positions
    logo_positions = ["left", "center", "right"]
    
    return templates.TemplateResponse(
        "admin/theme_settings.html",
        {
            "request": request,
            "selected_tenant": selected_tenant_slug,
            "tenant": tenant_obj,
            "tenants": tenants,
            "active_page": "theme-settings",
            "theme": theme,
            "font_families": font_families,
            "logo_positions": logo_positions,
            "status_message": status_message,
            "status_type": status_type
        }
    )

@router.post("/theme-settings/update", response_class=RedirectResponse)
async def update_theme_settings(
    request: Request,
    tenant_id: str = Form(...),
    primary_color: str = Form("#3498db"),
    secondary_color: str = Form("#6c757d"),
    background_color: str = Form("#ffffff"),
    text_color: str = Form("#212529"),
    font_family: str = Form("Arial, sans-serif"),
    logo_position: str = Form("left"),
    custom_css: Optional[str] = Form(None)
):
    """Update theme settings."""
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
            "primary_color": primary_color,
            "secondary_color": secondary_color,
            "background_color": background_color,
            "text_color": text_color,
            "font_family": font_family,
            "logo_position": logo_position
        })
        
        if custom_css:
            settings["custom_css"] = custom_css
        
        # Save updated settings
        tenant_manager.update_settings(tenant_id, settings)
        
        # Get tenant slug for redirect
        tenant_slug = tenant.slug
        
        return RedirectResponse(
            url=f"/admin/theme-settings?tenant={tenant_slug}&status_message=Theme+settings+updated+successfully&status_type=success",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Error updating theme settings: {str(e)}")
        return RedirectResponse(
            url=f"/admin/theme-settings?tenant={tenant.slug if tenant else ''}&status_message=Error+updating+theme+settings:+{str(e)}&status_type=danger",
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