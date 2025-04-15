"""
AI API routes for PyCommerce.

This module provides API endpoints for AI content generation.
"""

import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel

from pycommerce.plugins.ai.config import get_ai_providers, load_ai_config, get_ai_provider_instance
from pycommerce.models.plugin_config import PluginConfigManager

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger(__name__)

# Models for request/response
class GenerateContentRequest(BaseModel):
    """Request model for content generation."""
    prompt: str
    content_type: Optional[str] = "general"
    tone: Optional[str] = "professional"
    max_length: Optional[int] = None

class GenerateContentResponse(BaseModel):
    """Response model for content generation."""
    content: str
    provider: str

class AIProvidersResponse(BaseModel):
    """Response model for AI providers list."""
    providers: List[Dict[str, Any]]
    active_provider: str

@router.post("/generate-content", response_model=GenerateContentResponse)
async def generate_content(
    request: GenerateContentRequest,
    tenant_id: Optional[str] = Query(None, description="Tenant ID for tenant-specific configuration")
):
    """
    Generate content using the active AI provider.

    Args:
        request: Content generation request
        tenant_id: Optional tenant ID for tenant-specific configuration

    Returns:
        Generated content
    """
    try:
        # Get AI provider
        provider = None
        provider_id = "unknown"

        try:
            provider = get_ai_provider_instance(tenant_id)
            config = load_ai_config(tenant_id)
            provider_id = config.get("active_provider", "openai")
        except ValueError as e:
            # If API key is not configured, try to use a mock response for development
            if "localhost" in str(e) or "development" in str(e) or "API key" in str(e):
                logger.warning("AI provider not configured. Using mock response for development.")
                return GenerateContentResponse(
                    content="<p>This is a sample AI-generated content for testing purposes.</p><p>Since the AI service is not available, we're showing this placeholder text.</p><p>In a production environment, this would be replaced with actual AI-generated content based on your prompt.</p>",
                    provider="mock"
                )
            else:
                raise

        # Customize prompt based on content type and tone
        full_prompt = request.prompt

        if request.content_type == "heading":
            full_prompt = f"Create a compelling headline or heading in a {request.tone} tone: {request.prompt}"
        elif request.content_type == "description":
            full_prompt = f"Write a detailed description in a {request.tone} tone: {request.prompt}"
        elif request.content_type == "list":
            full_prompt = f"Create a bulleted list in a {request.tone} tone about: {request.prompt}"
        else:
            full_prompt = f"Generate content in a {request.tone} tone: {request.prompt}"

        # Generate content
        content = provider.generate_text(full_prompt)

        return GenerateContentResponse(
            content=content,
            provider=provider_id
        )

    except ValueError as e:
        logger.error(f"Error generating content: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail=f"AI provider not configured correctly: {str(e)}"
        )

    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating content: {str(e)}"
        )

@router.get("/providers", response_model=AIProvidersResponse)
async def get_providers(
    tenant_id: Optional[str] = Query(None, description="Tenant ID for tenant-specific configuration")
):
    """
    Get available AI providers and active provider.

    Args:
        tenant_id: Optional tenant ID for tenant-specific configuration

    Returns:
        List of available providers and active provider
    """
    try:
        # Load AI configuration
        config = load_ai_config(tenant_id)

        # Get active provider
        active_provider = config.get("active_provider", "openai")

        # Get available providers
        providers = get_ai_providers()

        return AIProvidersResponse(
            providers=providers,
            active_provider=active_provider
        )

    except Exception as e:
        logger.error(f"Error getting AI providers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting AI providers: {str(e)}")

@router.post("/set-provider")
async def set_active_provider(
    provider_id: str = Query(..., description="Provider ID to set as active"),
    tenant_id: Optional[str] = Query(None, description="Tenant ID for tenant-specific configuration")
):
    """
    Set the active AI provider.

    Args:
        provider_id: Provider ID to set as active
        tenant_id: Optional tenant ID for tenant-specific configuration

    Returns:
        Success message
    """
    try:
        # Validate provider ID
        providers = get_ai_providers()
        valid_providers = [p["id"] for p in providers]

        if provider_id not in valid_providers:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider ID. Valid providers are: {', '.join(valid_providers)}"
            )

        # Save active provider
        config_manager = PluginConfigManager()
        config_manager.save_config(
            "ai_active_provider",
            {"provider": provider_id},
            tenant_id
        )

        return {"success": True, "message": f"Active provider set to {provider_id}"}

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error setting active AI provider: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error setting active AI provider: {str(e)}")