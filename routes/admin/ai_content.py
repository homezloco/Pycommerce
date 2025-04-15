"""
Admin routes for AI-assisted content generation.
"""
import logging
from typing import Dict, Optional

from fastapi import APIRouter, Request, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from pycommerce.plugins.ai import get_ai_provider
from pycommerce.plugins.ai.config import get_ai_config

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin", "ai"])

# Template setup will be passed from main app
templates = None

def setup_routes(jinja_templates: Optional[Jinja2Templates] = None):
    """Set up routes for AI content generation."""
    global templates
    templates = jinja_templates
    logger.info("Setting up AI content routes")
    return router

@router.post("/api/ai/generate-content", response_class=JSONResponse)
async def generate_content(
    request: Request,
    data: Dict = Body(...),
):
    """Generate content using AI."""
    try:
        prompt = data.get("prompt", "")
        style = data.get("style", "informative")
        length = data.get("length", "medium")

        if not prompt:
            return JSONResponse(
                {"success": False, "error": "Prompt is required"},
                status_code=400
            )

        # Get AI configuration
        ai_config = get_ai_config()
        if not ai_config:
            return JSONResponse(
                {"success": False, "error": "AI not configured"},
                status_code=500
            )

        # Get AI provider based on config
        ai_provider = get_ai_provider()
        if not ai_provider:
            return JSONResponse(
                {"success": False, "error": "No AI provider available"},
                status_code=500
            )

        # Enhance prompt with style and length
        enhanced_prompt = f"Write content in a {style} style, with {length} length: {prompt}"

        # Generate content with AI provider
        try:
            content = ai_provider.generate_content(enhanced_prompt)

            return JSONResponse({
                "success": True,
                "content": content
            })
        except Exception as e:
            logger.error(f"Error generating content with AI provider: {str(e)}")
            return JSONResponse(
                {"success": False, "error": f"AI generation error: {str(e)}"},
                status_code=500
            )

    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        return JSONResponse(
            {"success": False, "error": f"Error: {str(e)}"},
            status_code=500
        )

@router.get("/ai-content", response_class=HTMLResponse)
async def ai_content_page(request: Request):
    """Admin page for AI content generation."""
    try:
        if not templates:
            return HTMLResponse(
                content="<h1>Error: Templates not configured</h1>",
                status_code=500
            )

        return templates.TemplateResponse(
            "admin/ai_content.html",
            {
                "request": request,
                "active_page": "ai_content"
            }
        )
    except Exception as e:
        logger.error(f"Error rendering AI content page: {str(e)}")
        return HTMLResponse(
            content=f"<h1>Error</h1><p>{str(e)}</p>",
            status_code=500
        )