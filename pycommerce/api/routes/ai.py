"""
API routes for AI-powered content generation.

This module provides API endpoints for generating and enhancing content using various AI providers.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from starlette.requests import Request

from pycommerce.plugins.ai.config import load_ai_config, get_ai_providers
from pycommerce.plugins.ai.providers import get_ai_provider
from pycommerce.models.plugin_config import PluginConfigManager

# Configure logging
logger = logging.getLogger(__name__)

# Create a router for AI routes
router = APIRouter()

# Create config manager
config_manager = PluginConfigManager()


class GenerateContentRequest(BaseModel):
    prompt: str
    provider: Optional[str] = None
    model: Optional[str] = None


class EnhanceContentRequest(BaseModel):
    text: str
    instructions: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None


class AIContentResponse(BaseModel):
    content: str


class AIProviderInfo(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    fields: List[Dict[str, Any]]


class AIProvidersResponse(BaseModel):
    providers: List[AIProviderInfo]
    active_provider: str


@router.post("/generate", response_model=AIContentResponse)
async def generate_content(
    request: GenerateContentRequest,
    tenant_id: Optional[str] = Query(None, description="Tenant ID for tenant-specific configuration")
):
    """
    Generate content using AI.
    
    Args:
        request: Contains the prompt for generating content
        tenant_id: Optional tenant ID for tenant-specific configuration
    
    Returns:
        Generated content
    """
    try:
        # Load AI configuration
        config = load_ai_config(tenant_id)
        
        # Get provider ID (either from request or from configuration)
        provider_id = request.provider or config.get("active_provider", "openai")
        
        # Get provider configuration
        provider_config = config.get("provider_config", {})
        
        # Override model if specified in request
        if request.model:
            provider_config["model"] = request.model
        
        # Get provider
        provider = get_ai_provider(provider_id, provider_config)
        
        # Generate content
        content = provider.generate_text(request.prompt)
        
        return AIContentResponse(content=content)
    
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating content: {str(e)}")


@router.post("/enhance", response_model=AIContentResponse)
async def enhance_content(
    request: EnhanceContentRequest,
    tenant_id: Optional[str] = Query(None, description="Tenant ID for tenant-specific configuration")
):
    """
    Enhance existing content using AI.
    
    Args:
        request: Contains the text to enhance and optional instructions
        tenant_id: Optional tenant ID for tenant-specific configuration
    
    Returns:
        Enhanced content
    """
    try:
        # Load AI configuration
        config = load_ai_config(tenant_id)
        
        # Get provider ID (either from request or from configuration)
        provider_id = request.provider or config.get("active_provider", "openai")
        
        # Get provider configuration
        provider_config = config.get("provider_config", {})
        
        # Override model if specified in request
        if request.model:
            provider_config["model"] = request.model
        
        # Get provider
        provider = get_ai_provider(provider_id, provider_config)
        
        # Enhance content
        content = provider.enhance_text(request.text, request.instructions)
        
        return AIContentResponse(content=content)
    
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error enhancing content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error enhancing content: {str(e)}")


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