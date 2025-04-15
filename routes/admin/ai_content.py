
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
    from pycommerce.plugins.ai.config import get_ai_provider_instance
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
        
    def get_ai_provider_instance(tenant_id=None):
        """Mock AI provider instance function."""
        return get_ai_provider()

from pycommerce.models.tenant import TenantManager

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize tenant manager
tenant_manager = TenantManager()

def setup_routes(templates):
    """Set up the AI content routes."""
    router = APIRouter()

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

            try:
                # Get AI provider
                ai_provider = get_ai_provider_instance(tenant_id)
                
                # Generate content
                logger.info(f"Generating content for tenant {tenant_id} with prompt: {prompt[:50]}...")
                content = ai_provider.generate_text(prompt)
                
                return JSONResponse({
                    "success": True,
                    "content": content
                })
            except ValueError as e:
                logger.warning(f"AI provider error: {str(e)}")
                return JSONResponse({
                    "success": False,
                    "message": f"AI service error: {str(e)}"
                })

        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            return JSONResponse({
                "success": False,
                "message": f"Error generating content: {str(e)}"
            })

    return router
