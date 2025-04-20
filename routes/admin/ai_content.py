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

# Import our new AI Service
from pycommerce.services.ai_service import AIService

# Import AI provider with error handling (legacy support)
try:
    from pycommerce.plugins.ai.providers import get_ai_provider
    from pycommerce.plugins.ai.config import get_ai_provider_instance, get_ai_settings, is_ai_enabled, update_ai_settings, load_ai_config
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"AI provider import failed: {str(e)} - using fallback mock provider")

    # Create fallback mock provider
    class MockAIProvider:
        def generate_text(self, prompt, **kwargs):
            return f"AI-generated content placeholder (prompt: {prompt[:30]}...)"

        def enhance_text(self, text, instructions=None, **kwargs):
            return f"Enhanced: {text[:50]}..."

    def get_ai_provider(provider_name=None, api_key=None):
        """Mock AI provider for fallback when actual AI module is not available."""
        return MockAIProvider()

    def get_ai_provider_instance(tenant_id=None):
        """Mock AI provider instance function."""
        return MockAIProvider()

    def get_ai_settings():
        return {}

    def is_ai_enabled():
        return False

    def update_ai_settings(data):
        return {}
    
    def load_ai_config():
        return {}


from pycommerce.models.tenant import TenantManager

# Configure logging
logger = logging.getLogger(__name__)

# Initialize tenant manager
tenant_manager = TenantManager()

# Initialize AI service
ai_service = AIService()

# Template setup will be passed from main app
templates = None

# Create API router
router = APIRouter(tags=["admin"])

@router.post("/admin/api/ai/generate-content")
async def generate_content_api(request: Request):
    """
    Generate content using AI based on a prompt.
    
    This endpoint supports the page builder's AI content generation feature
    for Quill editor integration.
    """
    try:
        # Parse request data
        data = await request.json()
        prompt = data.get("prompt", "")
        style = data.get("style", "informative")

        if not prompt:
            return JSONResponse(
                content={
                    "success": False,
                    "error": "Prompt is required"
                },
                status_code=400
            )

        # Get tenant information from session if available
        tenant_id = None
        if hasattr(request, 'session') and "selected_tenant" in request.session:
            tenant_slug = request.session.get("selected_tenant")
            if tenant_slug and tenant_slug != 'all':
                tenant = tenant_manager.get_by_slug(tenant_slug)
                if tenant:
                    tenant_id = str(tenant.id)

        # Generate content using our AI service
        logger.info(f"Generating content with prompt: {prompt[:50]}... (style: {style})")
        result = ai_service.generate_content(prompt, style, tenant_id)

        if "error" in result:
            return JSONResponse(
                content={
                    "success": False,
                    "error": result["error"]
                },
                status_code=400
            )

        return JSONResponse(
            content={
                "success": True,
                "content": result["content"]
            }
        )

    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        return JSONResponse(
            content={
                "success": False,
                "error": f"Error generating content: {str(e)}"
            },
            status_code=500
        )

@router.post("/admin/ai/generate-content", response_class=JSONResponse)
async def generate_content_form(
    request: Request,
    prompt: str = Form(...),
    context: Optional[str] = Form(None),
    format: Optional[str] = Form("html")
):
    """Generate content using AI for form-based requests."""
    try:
        # Check if AI is enabled in the legacy system
        if not is_ai_enabled():
            # Try using our new AI service instead
            if not ai_service.openai_client:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": "AI functionality is disabled in the system",
                        "message": "AI functionality is disabled. Please enable AI in the settings."
                    }
                )

        # Get selected tenant from session
        tenant_id = None
        if 'selected_tenant' in request.session:
            tenant_slug = request.session['selected_tenant']
            if tenant_slug and tenant_slug != 'all':
                tenant = tenant_manager.get_by_slug(tenant_slug)
                if tenant:
                    tenant_id = str(tenant.id)

        # Build complete prompt
        generation_prompt = f"{prompt}"
        if context:
            generation_prompt = f"Context:\n{context}\n\nPrompt:\n{prompt}"

        # Try using our new AI service first
        try:
            style = "informative"  # Default style
            result = ai_service.generate_content(generation_prompt, style, tenant_id)
            
            if "error" not in result and "content" in result:
                return {
                    "success": True,
                    "content": result["content"],
                    "format": format
                }
        except Exception as e:
            logger.warning(f"New AI service failed, falling back to legacy provider: {str(e)}")
            
        # Fall back to legacy AI provider if our service fails
        try:
            ai_provider = get_ai_provider_instance(tenant_id)
            content = ai_provider.generate_text(generation_prompt)
            
            return {
                "success": True,
                "content": content,
                "format": format
            }
        except ValueError as e:
            logger.warning(f"AI provider not configured properly: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": str(e),
                    "message": "AI provider not configured. Please set up AI in the configuration page."
                }
            )

    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "message": "An error occurred while generating content"
            }
        )

@router.post("/admin/ai/enhance-content", response_class=JSONResponse)
async def enhance_content(
    request: Request,
    content: str = Form(...),
    instructions: str = Form(...),
    format: Optional[str] = Form("html")
):
    """Enhance existing content using AI."""
    try:
        # Check if AI is enabled
        if not is_ai_enabled() and not ai_service.openai_client:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "AI functionality is disabled in the system",
                    "message": "AI functionality is disabled. Please enable AI in the settings."
                }
            )
        # Get selected tenant from session
        tenant_id = None
        if 'selected_tenant' in request.session:
            tenant_slug = request.session['selected_tenant']
            if tenant_slug and tenant_slug != 'all':
                tenant = tenant_manager.get_by_slug(tenant_slug)
                if tenant:
                    tenant_id = str(tenant.id)

        # Get AI provider
        try:
            ai_provider = get_ai_provider_instance(tenant_id)
        except ValueError as e:
            logger.warning(f"AI provider not configured properly: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": str(e),
                    "message": "AI provider not configured. Please set up AI in the configuration page."
                }
            )

        # Enhance content
        enhanced_content = ai_provider.enhance_text(content, instructions)

        return {
            "success": True,
            "content": enhanced_content,
            "format": format
        }
    except Exception as e:
        logger.error(f"Error enhancing content: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "message": "An error occurred while enhancing content"
            }
        )

@router.get("/admin/api/ai/settings")
async def get_ai_config(request: Request):
    """Get current AI configuration settings."""
    try:
        # Get settings (but filter out sensitive information like API keys)
        settings = get_ai_settings()
        safe_settings = {
            "enabled": settings.get("enabled", False),
            "default_provider": settings.get("default_provider", "openai"),
            "temperature": settings.get("temperature", 0.7),
            "max_tokens": settings.get("max_tokens", 500),
            # Include provider information but remove API keys
            "providers": [k for k in settings.keys() if isinstance(settings[k], dict)]
        }

        return JSONResponse(content={"settings": safe_settings})
    except Exception as e:
        logger.error(f"Error retrieving AI settings: {str(e)}")
        return JSONResponse(
            content={"error": f"Failed to retrieve AI settings: {str(e)}"},
            status_code=500
        )


@router.post("/admin/api/ai/settings")
async def update_ai_config(request: Request):
    """Update AI configuration settings."""
    try:
        data = await request.json()

        # Update settings
        updated_settings = update_ai_settings(data)

        return JSONResponse(content={"success": True, "message": "AI settings updated successfully"})
    except Exception as e:
        logger.error(f"Error updating AI settings: {str(e)}")
        return JSONResponse(
            content={"error": f"Failed to update AI settings: {str(e)}"},
            status_code=500
        )

def _build_prompt(content_type: str, user_prompt: str, tone: str, length: str) -> str:
    """
    Build a complete prompt for the AI.

    Args:
        content_type: Type of content to generate
        user_prompt: User's input prompt
        tone: Desired tone for the content
        length: Desired length of the content

    Returns:
        Complete prompt for the AI
    """
    # Map length to approximate word count
    length_map = {
        "short": "100-200 words",
        "medium": "300-500 words",
        "long": "800-1000 words"
    }

    # Map content type to instruction
    content_instructions = {
        "product_description": "Write a product description that highlights features and benefits",
        "marketing_copy": "Write marketing copy that persuades customers to purchase",
        "blog_post": "Write a blog post with an introduction, main points, and conclusion",
        "seo_content": "Write SEO-friendly content with relevant keywords and proper headings",
        "social_media": "Write an engaging social media post that encourages likes and shares"
    }

    # Get the appropriate instruction
    instruction = content_instructions.get(content_type, content_instructions["product_description"])

    # Build the prompt
    prompt = f"{instruction} in a {tone} tone. Length should be {length_map.get(length, 'medium')}."

    if user_prompt:
        prompt += f" Here are specific details to include: {user_prompt}"

    return prompt

def setup_routes(app_templates):
    """
    Set up routes with the given templates.

    Args:
        app_templates: Jinja2Templates instance from the main app
    """
    global templates
    templates = app_templates
    return router