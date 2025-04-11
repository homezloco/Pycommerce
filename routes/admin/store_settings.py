
"""
Admin routes for store settings.

This module provides routes for managing store settings in the admin interface.
"""
import logging
from typing import Dict, Optional, List, Any

from fastapi import APIRouter, Form, HTTPException, Request, status, Depends
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
    status_type: str = "info",
    tab: Optional[str] = None
):
    """Admin page for store settings."""
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
                logger.info(f"Retrieved settings for tenant {selected_tenant_slug}: {store_settings}")
        except Exception as e:
            logger.error(f"Error getting tenant: {str(e)}")
    
    # Get cart item count if available
    cart_item_count = request.session.get("cart_item_count", 0)
    
    # Default tab if not specified
    if not tab:
        tab = "basic"
    
    # Debug output
    logger.info(f"Rendering store settings with tenant: {tenant_obj.slug if tenant_obj else 'None'}")
    logger.info(f"Settings data: {store_settings}")
    
    return templates.TemplateResponse(
        "admin/store_settings.html",
        {
            "request": request,
            "selected_tenant": selected_tenant_slug,
            "tenant": tenant_obj,
            "tenants": tenants,
            "active_page": "store-settings",
            "config": store_settings,  # This is the key variable for the template
            "status_message": status_message,
            "status_type": status_type,
            "cart_item_count": cart_item_count,
            "tab": tab
        }
    )

@router.post("/store-settings", response_class=RedirectResponse)
async def update_basic_settings(
    request: Request,
    tab: str = Form("basic"),
    store_name: Optional[str] = Form(None),
    store_description: Optional[str] = Form(None),
    contact_email: Optional[str] = Form(None),
    currency: Optional[str] = Form("USD")
):
    """Update basic store settings."""
    try:
        # Get selected tenant from session
        selected_tenant_slug = request.session.get("selected_tenant")
        if not selected_tenant_slug:
            return RedirectResponse(
                url="/admin/store-settings?status_message=No+store+selected&status_type=danger",
                status_code=status.HTTP_303_SEE_OTHER
            )
        
        # Get tenant object
        tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
        if not tenant_obj:
            return RedirectResponse(
                url="/admin/store-settings?status_message=Store+not+found&status_type=danger",
                status_code=status.HTTP_303_SEE_OTHER
            )
        
        # Get current settings or initialize empty dict
        settings = tenant_obj.settings or {}
        
        # Update settings
        settings.update({
            "store_name": store_name,
            "store_description": store_description,
            "contact_email": contact_email,
            "currency": currency
        })
        
        # Save settings
        tenant_manager.update_settings(str(tenant_obj.id), settings)
        
        # Return to settings page with success message
        return RedirectResponse(
            url=f"/admin/store-settings?tenant={selected_tenant_slug}&status_message=Settings+updated+successfully&status_type=success&tab={tab}",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Error updating store settings: {str(e)}")
        return RedirectResponse(
            url=f"/admin/store-settings?tenant={selected_tenant_slug if 'selected_tenant_slug' in locals() else ''}&status_message=Error+updating+settings:+{str(e)}&status_type=danger&tab={tab}",
            status_code=status.HTTP_303_SEE_OTHER
        )

@router.post("/shipping-settings", response_class=RedirectResponse)
async def update_shipping_settings(
    request: Request,
    tab: str = Form("shipping"),
    store_country: Optional[str] = Form(None),
    store_postal_code: Optional[str] = Form(None),
    free_shipping_threshold: Optional[float] = Form(0.0),
    dimensional_weight_factor: Optional[int] = Form(5000),
    express_multiplier: Optional[float] = Form(1.75),
    flat_rate_domestic: Optional[float] = Form(5.0),
    flat_rate_international: Optional[float] = Form(15.0)
):
    """Update shipping settings."""
    try:
        # Get selected tenant from session
        selected_tenant_slug = request.session.get("selected_tenant")
        if not selected_tenant_slug:
            return RedirectResponse(
                url="/admin/store-settings?status_message=No+store+selected&status_type=danger&tab=shipping",
                status_code=status.HTTP_303_SEE_OTHER
            )
        
        # Get tenant object
        tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
        if not tenant_obj:
            return RedirectResponse(
                url="/admin/store-settings?status_message=Store+not+found&status_type=danger&tab=shipping",
                status_code=status.HTTP_303_SEE_OTHER
            )
        
        # Get current settings or initialize empty dict
        settings = tenant_obj.settings or {}
        
        # Update settings
        settings.update({
            "store_country": store_country,
            "store_postal_code": store_postal_code,
            "free_shipping_threshold": free_shipping_threshold,
            "dimensional_weight_factor": dimensional_weight_factor,
            "express_multiplier": express_multiplier,
            "flat_rate_domestic": flat_rate_domestic,
            "flat_rate_international": flat_rate_international
        })
        
        # Save settings
        tenant_manager.update_settings(str(tenant_obj.id), settings)
        
        # Return to settings page with success message
        return RedirectResponse(
            url=f"/admin/store-settings?tenant={selected_tenant_slug}&status_message=Shipping+settings+updated+successfully&status_type=success&tab=shipping",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Error updating shipping settings: {str(e)}")
        return RedirectResponse(
            url=f"/admin/store-settings?tenant={selected_tenant_slug if 'selected_tenant_slug' in locals() else ''}&status_message=Error+updating+shipping+settings:+{str(e)}&status_type=danger&tab=shipping",
            status_code=status.HTTP_303_SEE_OTHER
        )

@router.post("/ai-settings", response_class=RedirectResponse)
async def update_ai_settings(
    request: Request,
    tab: str = Form("ai"),
    openai_api_key: Optional[str] = Form(None),
    openai_model: Optional[str] = Form("gpt-3.5-turbo"),
    dalle_model: Optional[str] = Form("dall-e-2"),
    enable_product_descriptions: bool = Form(False),
    enable_image_generation: bool = Form(False),
    enable_chatbot: bool = Form(False)
):
    """Update AI settings."""
    try:
        # Get selected tenant from session
        selected_tenant_slug = request.session.get("selected_tenant")
        if not selected_tenant_slug:
            return RedirectResponse(
                url="/admin/store-settings?status_message=No+store+selected&status_type=danger&tab=ai",
                status_code=status.HTTP_303_SEE_OTHER
            )
        
        # Get tenant object
        tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
        if not tenant_obj:
            return RedirectResponse(
                url="/admin/store-settings?status_message=Store+not+found&status_type=danger&tab=ai",
                status_code=status.HTTP_303_SEE_OTHER
            )
        
        # Get current settings or initialize empty dict
        settings = tenant_obj.settings or {}
        
        # Update settings
        settings.update({
            "openai_api_key": openai_api_key,
            "openai_model": openai_model,
            "dalle_model": dalle_model,
            "enable_product_descriptions": enable_product_descriptions,
            "enable_image_generation": enable_image_generation,
            "enable_chatbot": enable_chatbot
        })
        
        # Save settings
        tenant_manager.update_settings(str(tenant_obj.id), settings)
        
        # Return to settings page with success message
        return RedirectResponse(
            url=f"/admin/store-settings?tenant={selected_tenant_slug}&status_message=AI+settings+updated+successfully&status_type=success&tab=ai",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Error updating AI settings: {str(e)}")
        return RedirectResponse(
            url=f"/admin/store-settings?tenant={selected_tenant_slug if 'selected_tenant_slug' in locals() else ''}&status_message=Error+updating+AI+settings:+{str(e)}&status_type=danger&tab=ai",
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
