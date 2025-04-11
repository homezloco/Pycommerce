"""
Admin routes for AI configuration.

This module provides routes for managing AI settings in the admin interface.
"""
import logging
import json
from typing import Dict, Optional, List, Any

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from pycommerce.models.tenant import TenantManager
from routes.admin.tenant_utils import get_selected_tenant, redirect_to_tenant_selection, create_virtual_all_tenant

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])

# Template setup will be passed from main app
templates = None

# Initialize managers
tenant_manager = TenantManager()

import os  # Added missing import

@router.get("/ai-config", response_class=HTMLResponse)
async def ai_config_page(
    request: Request,
    tenant: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for AI configuration."""
    # Get tenant from query parameters or session
    selected_tenant_slug = tenant or request.query_params.get('tenant') or request.session.get("selected_tenant")

    # If no tenant is selected, redirect to dashboard with message
    if not selected_tenant_slug:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Please+select+a+store+first&status_type=warning", 
            status_code=303
        )

    # Store the selected tenant in session for future requests
    request.session["selected_tenant"] = selected_tenant_slug

    # Initialize tenant object
    tenant_obj = None

    # Handle the "all stores" case
    if selected_tenant_slug.lower() == "all":
        logger.info("Using 'All Stores' selection in AI config page")
        tenant_obj = type('AllStoresTenant', (), create_virtual_all_tenant())
    else:
        # Get actual tenant object
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

    # Import AI providers configuration
    from pycommerce.plugins.ai.config import get_ai_providers

    # Get AI providers from plugin configuration
    ai_providers = get_ai_providers()

    # Add icons for Bootstrap display
    for provider in ai_providers:
        if provider['id'] == 'openai':
            provider['icon'] = 'bi-cpu'
            provider['color'] = 'success'
        elif provider['id'] == 'gemini':
            provider['icon'] = 'bi-google'
            provider['color'] = 'primary'
        elif provider['id'] == 'deepseek':
            provider['icon'] = 'bi-braces'
            provider['color'] = 'info'
        elif provider['id'] == 'openrouter':
            provider['icon'] = 'bi-diagram-3'
            provider['color'] = 'warning'
        else:
            provider['icon'] = 'bi-robot'
            provider['color'] = 'secondary'

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

@router.get("/ai-config/configure/{provider_id}", response_class=HTMLResponse)
async def ai_config_configure_page(
    request: Request,
    provider_id: str,
    tenant: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for configuring a specific AI provider."""
    # Get tenant from query parameters or session
    selected_tenant_slug = tenant or request.query_params.get('tenant') or request.session.get("selected_tenant")

    # If no tenant is selected, redirect to dashboard with message
    if not selected_tenant_slug:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Please+select+a+store+first&status_type=warning", 
            status_code=303
        )

    # Store the selected tenant in session for future requests
    request.session["selected_tenant"] = selected_tenant_slug

    # Initialize tenant object
    tenant_obj = None

    # Handle the "all stores" case
    if selected_tenant_slug.lower() == "all":
        logger.info("Using 'All Stores' selection in AI config provider page")
        tenant_obj = type('AllStoresTenant', (), create_virtual_all_tenant())
    else:
        # Get actual tenant object
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

    # Import AI providers configuration
    from pycommerce.plugins.ai.config import get_ai_providers

    # Get AI providers from plugin configuration
    ai_providers = get_ai_providers()

    # Add icons for Bootstrap display
    for provider in ai_providers:
        if provider['id'] == 'openai':
            provider['icon'] = 'bi-cpu'
            provider['color'] = 'success'
        elif provider['id'] == 'gemini':
            provider['icon'] = 'bi-google'
            provider['color'] = 'primary'
        elif provider['id'] == 'deepseek':
            provider['icon'] = 'bi-braces'
            provider['color'] = 'info'
        elif provider['id'] == 'openrouter':
            provider['icon'] = 'bi-diagram-3'
            provider['color'] = 'warning'
        else:
            provider['icon'] = 'bi-robot'
            provider['color'] = 'secondary'

    # Get active provider from settings
    active_provider = ai_settings.get('provider_id', 'openai')

    # Use the requested provider from URL
    selected_provider_id = provider_id
    selected_provider = next((p for p in ai_providers if p['id'] == selected_provider_id), None)

    if not selected_provider:
        # If provider not found, redirect to the default config page
        return RedirectResponse(
            url=f"/admin/ai-config?tenant={selected_tenant_slug}&status_message=Selected+AI+provider+not+found&status_type=error", 
            status_code=303
        )

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

@router.post("/ai-config/save", response_class=RedirectResponse)
async def save_ai_config(
    request: Request,
    provider_id: str = Form(...),
    tenant: str = Form(...)
):
    """Save AI configuration for a specific provider."""
    try:
        # Get form data for the selected provider
        form_data = dict(await request.form())

        # Import AI providers configuration
        from pycommerce.plugins.ai.config import get_ai_providers

        # Get the provider configuration fields and filter form data to include only fields for this provider
        provider_fields = {}
        for provider in get_ai_providers():
            if provider['id'] == provider_id:
                for field in provider['fields']:
                    field_id = field['id']
                    if field_id in form_data:
                        provider_fields[field_id] = form_data[field_id]

        # Create a config manager
        from pycommerce.models.plugin_config import PluginConfigManager
        config_manager = PluginConfigManager()

        # Handle the "all stores" case
        if tenant == 'all':
            # Get all tenants
            tenants = tenant_manager.get_all()

            # Save configuration for each tenant
            for tenant_obj in tenants:
                config_manager.save_config(
                    f"ai_{provider_id}",
                    provider_fields,
                    str(tenant_obj.id)
                )

            logger.info(f"Saved AI configuration for provider {provider_id} for all tenants")
        else:
            # Get tenant object
            tenant_obj = tenant_manager.get_by_slug(tenant)
            if not tenant_obj:
                raise HTTPException(
                    status_code=404,
                    detail=f"Store with slug '{tenant}' not found"
                )

            # Save for single tenant
            config_manager.save_config(
                f"ai_{provider_id}",
                provider_fields,
                str(tenant_obj.id)
            )

            logger.info(f"Saved AI configuration for provider {provider_id} and tenant {tenant}")

        # Redirect back to AI config page
        return RedirectResponse(
            url=f"/admin/ai-config?tenant={tenant}&status_message=AI+configuration+saved+successfully&status_type=success",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Error saving AI configuration: {str(e)}")
        return RedirectResponse(
            url=f"/admin/ai-config?tenant={tenant}&status_message=Error+saving+AI+configuration:+{str(e)}&status_type=danger",
            status_code=status.HTTP_303_SEE_OTHER
        )

@router.post("/ai-config/set-active", response_class=RedirectResponse)
async def set_active_ai_provider(
    request: Request,
    provider_id: str = Form(...),
    tenant: str = Form(...)
):
    """Set the active AI provider for a tenant."""
    try:
        # Create a config manager
        from pycommerce.models.plugin_config import PluginConfigManager
        config_manager = PluginConfigManager()

        # Handle the "all stores" case
        if tenant == 'all':
            # Get all tenants
            tenants = tenant_manager.get_all()

            # Save active provider for each tenant
            for tenant_obj in tenants:
                config_manager.save_config(
                    "ai_active_provider",
                    {"provider": provider_id},
                    str(tenant_obj.id)
                )

            logger.info(f"Set active AI provider to {provider_id} for all tenants")
        else:
            # Get tenant object
            tenant_obj = tenant_manager.get_by_slug(tenant)
            if not tenant_obj:
                raise HTTPException(
                    status_code=404,
                    detail=f"Store with slug '{tenant}' not found"
                )

            # Save the active provider for single tenant
            config_manager.save_config(
                "ai_active_provider",
                {"provider": provider_id},
                str(tenant_obj.id)
            )

            logger.info(f"Set active AI provider to {provider_id} for tenant {tenant}")

        # Redirect back to AI config page
        return RedirectResponse(
            url=f"/admin/ai-config?tenant={tenant}&status_message=Active+AI+provider+set+to+{provider_id}&status_type=success",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Error setting active AI provider: {str(e)}")
        return RedirectResponse(
            url=f"/admin/ai-config?tenant={tenant}&status_message=Error+setting+active+AI+provider:+{str(e)}&status_type=danger",
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