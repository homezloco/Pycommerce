"""
Admin routes for AI configuration.

This module provides routes for managing AI settings in the admin interface.
"""
import logging
import os
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

@router.get("/ai-config", response_class=HTMLResponse)
async def ai_config_page(
    request: Request,
    tenant: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for AI configuration."""
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
    
    # Get AI settings
    ai_settings = tenant_obj.settings.get('ai_settings', {}) if tenant_obj.settings else {}
    
    # Check if OpenAI API key is available
    has_openai_key = bool(os.environ.get("OPENAI_API_KEY"))
    
    # Get all tenants for the sidebar
    tenants = tenant_manager.get_all()
    
    # Available models
    openai_models = [
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo",
    ]
    
    openai_image_models = [
        "dall-e-3",
        "dall-e-2",
    ]
    
    # Define AI providers
    ai_providers = [
        {
            'id': 'openai',
            'name': 'OpenAI',
            'description': 'Use OpenAI for AI-powered features',
            'logo': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/OpenAI_Logo.svg/1280px-OpenAI_Logo.svg.png',
            'fields': [
                {
                    'id': 'api_key',
                    'name': 'API Key',
                    'type': 'password',
                    'description': 'Your OpenAI API key',
                    'required': True,
                },
                {
                    'id': 'model',
                    'name': 'Default Model',
                    'type': 'select',
                    'options': [{'value': model, 'label': model} for model in openai_models],
                    'default': 'gpt-4-turbo',
                    'description': 'Default model to use for text generation',
                    'required': True,
                },
                {
                    'id': 'image_model',
                    'name': 'Image Generation Model',
                    'type': 'select',
                    'options': [{'value': model, 'label': model} for model in openai_image_models],
                    'default': 'dall-e-3',
                    'description': 'Model to use for image generation',
                    'required': True,
                }
            ]
        },
        {
            'id': 'azure',
            'name': 'Azure OpenAI',
            'description': 'Use Azure OpenAI for AI-powered features',
            'fields': [
                {
                    'id': 'api_key',
                    'name': 'API Key',
                    'type': 'password',
                    'description': 'Your Azure OpenAI API key',
                    'required': True,
                },
                {
                    'id': 'endpoint',
                    'name': 'Endpoint',
                    'type': 'text',
                    'description': 'Azure OpenAI endpoint URL',
                    'required': True,
                },
                {
                    'id': 'deployment_name',
                    'name': 'Deployment Name',
                    'type': 'text',
                    'description': 'Azure OpenAI deployment name',
                    'required': True,
                }
            ]
        }
    ]
    
    # Get active provider from settings
    active_provider = ai_settings.get('provider_id', 'openai')
    
    # Get selected provider, defaulting to active provider or OpenAI
    selected_provider_id = active_provider
    selected_provider = next((p for p in ai_providers if p['id'] == selected_provider_id), ai_providers[0])
    
    # Get field values for selected provider
    field_values = ai_settings.get(selected_provider_id, {})
    
    return templates.TemplateResponse(
        "admin/ai_config.html",
        {
            "request": request,
            "selected_tenant": selected_tenant_slug,
            "tenant": tenant_obj,
            "tenants": tenants,
            "active_page": "ai-config",
            "ai_settings": ai_settings,
            "has_openai_key": has_openai_key,
            "openai_models": openai_models,
            "openai_image_models": openai_image_models,
            "ai_providers": ai_providers,
            "active_provider": active_provider,
            "selected_provider": selected_provider,
            "field_values": field_values,
            "status_message": status_message,
            "status_type": status_type
        }
    )

@router.post("/ai-config/update", response_class=RedirectResponse)
async def update_ai_config(
    request: Request,
    tenant_id: str = Form(...),
    openai_enabled: Optional[str] = Form(None),
    openai_model: str = Form("gpt-4-turbo"),
    openai_image_model: str = Form("dall-e-3"),
    product_description_enabled: Optional[str] = Form(None),
    image_generation_enabled: Optional[str] = Form(None),
    max_tokens_per_request: int = Form(2000),
    temperature: float = Form(0.7)
):
    """Update AI configuration."""
    try:
        # Get tenant
        tenant = tenant_manager.get(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=404,
                detail=f"Store with ID {tenant_id} not found"
            )
        
        # Update AI settings
        settings = tenant.settings or {}
        
        # Create AI settings object
        ai_settings = {
            "openai_enabled": openai_enabled is not None,
            "openai_model": openai_model,
            "openai_image_model": openai_image_model,
            "product_description_enabled": product_description_enabled is not None,
            "image_generation_enabled": image_generation_enabled is not None,
            "max_tokens_per_request": max_tokens_per_request,
            "temperature": temperature
        }
        
        # Update settings
        settings["ai_settings"] = ai_settings
        
        # Save updated settings
        tenant_manager.update_settings(tenant_id, settings)
        
        # Get tenant slug for redirect
        tenant_slug = tenant.slug
        
        return RedirectResponse(
            url=f"/admin/ai-config?tenant={tenant_slug}&status_message=AI+settings+updated+successfully&status_type=success",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Error updating AI settings: {str(e)}")
        return RedirectResponse(
            url=f"/admin/ai-config?tenant={tenant.slug if tenant else ''}&status_message=Error+updating+AI+settings:+{str(e)}&status_type=danger",
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