
"""
Routes for AI-powered content generation.
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
import logging
from pycommerce.plugins.ai.providers import get_ai_provider
from pycommerce.models.tenant import get_tenant_by_id

router = APIRouter()
logger = logging.getLogger(__name__)

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
            
            # Get AI provider
            tenant = get_tenant_by_id(tenant_id)
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
