
"""
Admin routes for AI-generated content.

This module provides routes for generating content using AI integrations.
"""
import logging
import json
from typing import Dict, Optional, List, Any

from fastapi import APIRouter, HTTPException, Request, Body, Query, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

# Import AI provider with error handling
try:
    from pycommerce.plugins.ai.providers import get_ai_provider
    from pycommerce.plugins.ai.config import get_active_provider, get_provider_config
    HAS_AI_CONFIG = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("AI provider import failed - using fallback mock provider")
    HAS_AI_CONFIG = False

    # Create fallback mock provider
    def get_ai_provider(provider_name=None, api_key=None):
        """Mock AI provider for fallback when actual AI module is not available."""
        class MockAIProvider:
            def generate_content(self, prompt, **kwargs):
                return {
                    "content": f"AI-generated content placeholder (prompt: {prompt[:30]}...)",
                    "success": True
                }
        return MockAIProvider()
    
    def get_active_provider():
        return "mock"
    
    def get_provider_config(provider_name):
        return {"api_key": "", "model": "mock-model"}

from pycommerce.models.tenant import TenantManager

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize tenant manager
tenant_manager = TenantManager()

@router.post("/api/ai/generate-content")
async def generate_content(
    request: Request,
    prompt: str = Form(...),
    provider: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    tenant_id: Optional[str] = Form(None)
):
    """Generate content using AI.
    
    Args:
        prompt: The prompt to send to the AI
        provider: Optional provider override
        model: Optional model override
        tenant_id: Optional tenant ID for context
        
    Returns:
        Generated content
    """
    try:
        logger.info(f"Generating content with prompt: {prompt[:50]}...")
        
        # Get active provider if not specified
        if not provider and HAS_AI_CONFIG:
            provider = get_active_provider()
        
        # Get tenant context if provided
        tenant_context = ""
        if tenant_id:
            try:
                tenant = tenant_manager.get(tenant_id)
                if tenant:
                    tenant_context = f"This content is for an e-commerce store called '{tenant.name}' that focuses on {tenant.description or 'various products'}. "
            except Exception as e:
                logger.error(f"Error getting tenant context: {str(e)}")
        
        # Enhance prompt with tenant context
        enhanced_prompt = f"{tenant_context}{prompt}"
        
        # Additional parameters
        params = {}
        if model:
            params["model"] = model
        
        # Get AI provider and generate content
        ai_provider = get_ai_provider(provider)
        result = ai_provider.generate_content(enhanced_prompt, **params)
        
        # Return the result
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "content": f"Error generating content: {str(e)}",
                "error": str(e)
            }
        )

@router.get("/ai/modal")
async def ai_modal(request: Request):
    """Return the AI modal HTML."""
    templates = request.app.state.templates
    
    provider = get_active_provider() if HAS_AI_CONFIG else "mock"
    provider_config = get_provider_config(provider) if HAS_AI_CONFIG else {"model": "mock-model"}
    
    return templates.TemplateResponse(
        "admin/partials/ai_modal.html",
        {
            "request": request,
            "provider": provider,
            "models": [
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "openai"},
                {"id": "gpt-4", "name": "GPT-4", "provider": "openai"},
                {"id": "gemini-pro", "name": "Gemini Pro", "provider": "google"}
            ],
            "current_model": provider_config.get("model", "gpt-3.5-turbo")
        }
    )
