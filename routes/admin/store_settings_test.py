
"""
Admin routes for store settings test.

This module provides routes for managing store settings in the admin interface.
"""
import logging
from typing import Dict, Optional, List, Any

from fastapi import APIRouter, Form, HTTPException, Request, status, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from pycommerce.models.tenant import TenantManager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])

# Template setup will be passed from main app
templates = None

# Initialize managers
tenant_manager = TenantManager()

@router.get("/store-settings-test", response_class=HTMLResponse)
async def store_settings_test(
    request: Request,
    tenant: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info",
    tab: Optional[str] = None
):
    """Admin page for store settings (test version)."""
    # Get tenant from query parameters or session
    selected_tenant_slug = tenant or request.session.get("selected_tenant")
    
    # Get all tenants for the sidebar
    tenants = []
    try:
        tenant_list = tenant_manager.list() or []
        tenants = [t for t in tenant_list if t and hasattr(t, 'id')]
    except Exception as e:
        logger.error(f"Error getting tenants: {str(e)}")
    
    # If no tenant is selected and we have tenants, select the first one
    if not selected_tenant_slug and tenants:
        selected_tenant_slug = tenants[0].slug
        request.session["selected_tenant"] = selected_tenant_slug
    
    # Store the selected tenant in session for future requests
    request.session["selected_tenant"] = selected_tenant_slug
    
    # Get tenant object if we have a selected tenant
    tenant_obj = None
    store_settings = {}
    if selected_tenant_slug:
        try:
            tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
            if tenant_obj:
                # Make sure we have settings initialized
                store_settings = tenant_obj.settings or {}
                logger.info(f"[TEST] Retrieved settings for tenant {selected_tenant_slug}: {store_settings}")
        except Exception as e:
            logger.error(f"[TEST] Error getting tenant: {str(e)}")
    
    # Get cart item count if available
    cart_item_count = request.session.get("cart_item_count", 0)
    
    # Default tab if not specified
    if not tab:
        tab = "basic"
    
    # Debug output
    logger.info(f"[TEST] Rendering store settings with tenant: {tenant_obj.slug if tenant_obj else 'None'}")
    logger.info(f"[TEST] Settings data: {store_settings}")
    
    # Process settings to ensure we have all expected fields with defaults
    processed_settings = {
        # Basic settings with defaults
        "store_name": store_settings.get("store_name", ""),
        "store_description": store_settings.get("store_description", ""),
        "contact_email": store_settings.get("contact_email", ""),
        "currency": store_settings.get("currency", "USD"),
        
        # Theme/color settings
        "primary_color": store_settings.get("primary_color", "#3498db"),
        "secondary_color": store_settings.get("secondary_color", "#6c757d"),
        "background_color": store_settings.get("background_color", "#ffffff"),
        "text_color": store_settings.get("text_color", "#212529"),
        "font_family": store_settings.get("font_family", "Arial, sans-serif"),
        
        # Shipping settings
        "store_country": store_settings.get("store_country", "US"),
        "enable_shipping": store_settings.get("enable_shipping", True),
        "flat_rate_shipping": store_settings.get("flat_rate_shipping", 5.99),
        
        # Add additional keys from the original settings to maintain data
        **store_settings
    }
    
    # Make sure processed_settings has all needed methods/functions
    # Add dictionary methods if they're being called in the template
    processed_settings["keys"] = lambda: processed_settings.keys()
    processed_settings["__len__"] = lambda: len(processed_settings)
    
    # Log processed settings for debugging
    logger.info(f"[TEST] Processed settings for template: {processed_settings}")
    
    # Include the raw settings for debugging too
    processed_settings["_raw"] = store_settings
    
    # Return template data with processed settings
    return templates.TemplateResponse(
        "admin/store_settings_test.html",
        {
            "request": request,
            "selected_tenant": selected_tenant_slug,
            "tenant": tenant_obj,
            "tenants": tenants,
            "active_page": "store-settings",
            "config": processed_settings,  # Use processed settings
            "theme": store_settings.get('theme', {}),  # Add theme settings directly
            "status_message": status_message,
            "status_type": status_type,
            "cart_item_count": cart_item_count,
            "tab": tab,
            "display_tenant_selector": True  # Add this flag to ensure tenant selector is displayed
        }
    )

@router.post("/store-settings-test/basic", response_class=RedirectResponse)
async def update_basic_settings_test(
    request: Request,
    tab: str = Form("basic"),
    store_name: Optional[str] = Form(None),
    store_description: Optional[str] = Form(None),
    contact_email: Optional[str] = Form(None),
    currency: Optional[str] = Form("USD")
):
    """Update basic store settings (test version)."""
    try:
        # Get selected tenant from session
        selected_tenant_slug = request.session.get("selected_tenant")
        if not selected_tenant_slug:
            return RedirectResponse(
                url="/admin/store-settings-test?status_message=No+store+selected&status_type=danger",
                status_code=status.HTTP_303_SEE_OTHER
            )
        
        # Get tenant object
        tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
        if not tenant_obj:
            return RedirectResponse(
                url="/admin/store-settings-test?status_message=Store+not+found&status_type=danger",
                status_code=status.HTTP_303_SEE_OTHER
            )
        
        # Get current settings or initialize empty dict
        settings = tenant_obj.settings or {}
        
        # Log current settings before update
        logger.info(f"[TEST] Current settings before update: {settings}")
        
        # Update settings
        settings.update({
            "store_name": store_name,
            "store_description": store_description,
            "contact_email": contact_email,
            "currency": currency
        })
        
        # Log settings after update
        logger.info(f"[TEST] Updated settings: {settings}")
        
        # Save settings
        logger.info(f"[TEST] Updating settings for tenant ID: {tenant_obj.id}")
        tenant_manager.update_settings(str(tenant_obj.id), settings)
        
        # Return to settings page with success message
        return RedirectResponse(
            url=f"/admin/store-settings-test?tenant={selected_tenant_slug}&status_message=Settings+updated+successfully&status_type=success&tab={tab}",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"[TEST] Error updating store settings: {str(e)}")
        return RedirectResponse(
            url=f"/admin/store-settings-test?tenant={selected_tenant_slug if 'selected_tenant_slug' in locals() else ''}&status_message=Error+updating+settings:+{str(e)}&status_type=danger&tab={tab}",
            status_code=status.HTTP_303_SEE_OTHER
        )

@router.get("/api/store-settings-test", response_class=JSONResponse)
async def get_store_settings_test_api(
    request: Request,
    tenant: Optional[str] = None
):
    """API endpoint to check store settings data (test version)."""
    # Get tenant from query parameters or session
    selected_tenant_slug = tenant or request.session.get("selected_tenant")
    
    # Get tenant object if we have a selected tenant
    tenant_obj = None
    store_settings = {}
    if selected_tenant_slug:
        try:
            tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
            if tenant_obj:
                # Make sure we have settings initialized
                store_settings = tenant_obj.settings or {}
                logger.info(f"[TEST API] Retrieved settings for tenant {selected_tenant_slug}: {store_settings}")
        except Exception as e:
            logger.error(f"[TEST API] Error getting tenant: {str(e)}")
    
    # Debug output
    logger.info(f"[TEST API] Settings structure type: {type(store_settings)}")
    
    # Return JSON response with settings data
    return {
        "tenant_slug": selected_tenant_slug,
        "tenant_id": str(tenant_obj.id) if tenant_obj else None,
        "settings": store_settings,
        "theme": store_settings.get('theme', {})
    }

def setup_routes(app_templates):
    """
    Set up routes with the given templates.
    
    Args:
        app_templates: Jinja2Templates instance from the main app
    """
    global templates
    templates = app_templates
    return router
