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
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("AI provider import failed - using fallback mock provider")

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

from pycommerce.models.tenant import TenantManager

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize tenant manager
tenant_manager = TenantManager()

def setup_routes(templates):
    """Set up the AI content routes."""

    @router.post("/admin/api/ai/generate-content")
    async def generate_content(request: Request):
        """
        Generate content using AI based on a prompt.
        """
        try:
            data = await request.json()
            prompt = data.get("prompt", "")

            if not prompt:
                return JSONResponse({
                    "success": False,
                    "message": "Prompt is required"
                })

            # Get tenant information
            tenant_id = request.session.get("selected_tenant")
            if not tenant_id:
                logger.warning("No tenant selected for content generation")
                return JSONResponse({
                    "success": False, 
                    "message": "No store selected"
                })

            # Get tenant using TenantManager
            tenant = tenant_manager.get_by_slug(tenant_id)
            if not tenant:
                logger.warning(f"Tenant not found: {tenant_id}")
                return JSONResponse({
                    "success": False,
                    "message": "Store not found"
                })

            # Get AI provider
            provider = get_ai_provider(tenant)
            if not provider:
                logger.warning(f"No AI provider configured for tenant: {tenant_id}")
                return JSONResponse({
                    "success": False,
                    "message": "AI service not configured for this store"
                })

            # Generate content
            logger.info(f"Generating content for tenant {tenant_id} with prompt: {prompt[:50]}...")
            content = provider.generate_content(prompt)

            return JSONResponse({
                "success": True,
                "content": content
            })
        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            return JSONResponse({
                "success": False,
                "message": f"Error generating content: {str(e)}"
            })

    return router
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, Depends, HTTPException, Form, Body
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette import status

# Import AI provider functionality
from pycommerce.plugins.ai.config import load_ai_config, get_ai_providers
from pycommerce.models.plugin_config import PluginConfigManager

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/api/ai/generate-content")
async def generate_ai_content(request: Request, data: Dict[str, Any] = Body(...)):
    """
    Generate or modify content using AI.
    
    Args:
        request: The request object
        data: The request data containing task, prompt, and optional content
    
    Returns:
        JSON response with generated content
    """
    try:
        # Get tenant information
        tenant_id = None
        if hasattr(request.state, 'tenant') and request.state.tenant:
            tenant_id = request.state.tenant.id
            
        # Get task details
        task = data.get('task', 'generate')
        prompt = data.get('prompt', '')
        content = data.get('content', '')
        
        # Load AI configuration
        config = load_ai_config(tenant_id)
        
        if not config or not config.get("provider_config", {}).get("api_key"):
            logger.warning("AI configuration not available or API key not set")
            return JSONResponse(
                status_code=400,
                content={"error": "AI service not configured. Please configure AI in admin settings."}
            )
        
        # Get AI provider
        try:
            from pycommerce.plugins.ai.providers import get_ai_provider
            provider = get_ai_provider(
                config.get("active_provider", "openai"),
                config.get("provider_config", {})
            )
        except Exception as e:
            logger.error(f"Error initializing AI provider: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Error initializing AI provider: {str(e)}"}
            )
        
        # Generate content based on task
        try:
            result = ""
            
            if task == "generate":
                # Generate new content
                result = provider.generate_text(prompt)
            elif task == "improve":
                # Improve existing content
                result = provider.enhance_text(content, f"Improve this text. {prompt}")
            elif task == "expand":
                # Expand existing content
                result = provider.enhance_text(content, f"Expand this text with more details. {prompt}")
            elif task == "shorten":
                # Shorten existing content
                result = provider.enhance_text(content, f"Shorten this text while preserving key information. {prompt}")
            elif task == "proofread":
                # Proofread and fix errors
                result = provider.enhance_text(content, f"Proofread this text and fix any errors. {prompt}")
            else:
                # Default to generate
                result = provider.generate_text(prompt)
                
            return JSONResponse(content={"content": result})
            
        except Exception as e:
            logger.error(f"Error generating content with AI: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Error generating content: {str(e)}"}
            )
            
    except Exception as e:
        logger.error(f"Error in AI content generation endpoint: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal server error: {str(e)}"}
        )
