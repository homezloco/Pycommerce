"""
API routes for the page builder.

This module provides API endpoints for the page builder's AI content generation,
collaborative editing, and block template functionality.
"""
import logging
import json
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Form, HTTPException, Request, status, Body
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from pycommerce.models.page_builder import PageManager, PageSectionManager, ContentBlockManager, PageTemplateManager
from pycommerce.models.tenant import TenantManager
from pycommerce.services.ai_service import AIService
from pycommerce.core.db import SessionLocal

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin/api/pages", tags=["admin", "pages", "api"])

# Initialize AI service
ai_service = AIService()

def get_managers():
    """Get managers with a fresh session."""
    session = SessionLocal()

    # Initialize all managers with the session
    tenant_manager = TenantManager()
    tenant_manager.session = session

    page_manager = PageManager(session)
    section_manager = PageSectionManager(session)
    block_manager = ContentBlockManager(session)
    template_manager = PageTemplateManager(session)

    return {
        "tenant_manager": tenant_manager,
        "page_manager": page_manager,
        "section_manager": section_manager,
        "block_manager": block_manager,
        "template_manager": template_manager,
        "session": session
    }

# AI content generation
@router.post("/ai/generate", response_class=JSONResponse)
async def generate_ai_content(data: Dict[str, Any] = Body(...)):
    """Generate content using AI for the page builder."""
    logger.info(f"Generating AI content for type: {data.get('content_type')}")
    
    try:
        prompt = data.get("prompt")
        content_type = data.get("content_type")
        options = data.get("options", {})
        
        if not prompt:
            return JSONResponse({
                "success": False,
                "error": "No prompt provided"
            }, status_code=400)
        
        if not content_type:
            return JSONResponse({
                "success": False,
                "error": "No content type specified"
            }, status_code=400)
        
        # Generate content based on type
        result = {}
        
        if content_type == "text":
            style = options.get("style", "paragraph")
            tone = options.get("tone", "professional")
            
            # Enhance prompt based on style and tone
            enhanced_prompt = f"Write {style} content in a {tone} tone about: {prompt}"
            if style == "features":
                enhanced_prompt = f"Write a bulleted list of features in a {tone} tone about: {prompt}"
            elif style == "steps":
                enhanced_prompt = f"Write a step-by-step guide in a {tone} tone about: {prompt}"
            elif style == "quote":
                enhanced_prompt = f"Write a compelling testimonial quote in a {tone} tone about: {prompt}"
            
            # Generate content
            text_content = ai_service.generate_text(enhanced_prompt)
            
            # Format as HTML based on style
            html_content = f"<p>{text_content}</p>"
            if style == "features":
                # Convert to bullet points if not already
                if not text_content.strip().startswith("•") and not text_content.strip().startswith("-"):
                    lines = text_content.split("\n")
                    html_content = "<ul>\n"
                    for line in lines:
                        if line.strip():
                            html_content += f"<li>{line.strip()}</li>\n"
                    html_content += "</ul>"
                else:
                    # Already has bullet points, just convert to HTML list
                    lines = text_content.split("\n")
                    html_content = "<ul>\n"
                    for line in lines:
                        if line.strip():
                            # Remove existing bullet points
                            clean_line = line.strip()
                            if clean_line.startswith("•") or clean_line.startswith("-"):
                                clean_line = clean_line[1:].strip()
                            html_content += f"<li>{clean_line}</li>\n"
                    html_content += "</ul>"
            elif style == "steps":
                # Convert to numbered steps
                lines = text_content.split("\n")
                html_content = "<ol>\n"
                for line in lines:
                    if line.strip():
                        # Remove existing step numbers if present
                        clean_line = line.strip()
                        import re
                        clean_line = re.sub(r'^\d+[\.\)]\s*', '', clean_line)
                        html_content += f"<li>{clean_line}</li>\n"
                html_content += "</ol>"
            elif style == "quote":
                html_content = f'<blockquote class="blockquote">\n<p>{text_content}</p>\n</blockquote>'
            
            result = {
                "html": html_content,
                "raw_text": text_content
            }
            
        elif content_type == "heading":
            heading_type = options.get("type", "h2")
            
            # Generate heading text
            heading_text = ai_service.generate_text(f"Write a short, catchy heading for: {prompt}")
            
            # Remove any trailing punctuation
            import re
            heading_text = re.sub(r'[\.,:;!]$', '', heading_text.strip())
            
            result = {
                "tag": heading_type,
                "text": heading_text
            }
            
        elif content_type == "image":
            style = options.get("style", "realistic")
            
            # Enhance prompt based on style
            image_prompt = f"{prompt}, {style} style, high quality, detailed"
            
            # Generate image and save to media library
            try:
                from pycommerce.services.media_service import MediaService
                media_service = MediaService()
                
                # Generate the image using AI
                image_data = ai_service.generate_image(image_prompt)
                
                if image_data and "url" in image_data:
                    # If AI service returned a URL, download the image
                    import requests
                    from io import BytesIO
                    
                    response = requests.get(image_data["url"])
                    image_bytes = BytesIO(response.content)
                    
                    # Generate a filename based on the prompt
                    import re
                    safe_filename = re.sub(r'[^a-zA-Z0-9]', '-', prompt.lower())[:50]
                    filename = f"ai-generated-{safe_filename}.png"
                    
                    # Save to media library
                    media_item = media_service.save_media(
                        name=f"AI Generated: {prompt[:50]}",
                        description=f"AI generated image: {prompt}",
                        file_obj=image_bytes,
                        filename=filename,
                        content_type="image/png",
                        is_public=True
                    )
                    
                    # Return media item URL and details
                    result = {
                        "url": media_item.url,
                        "alt": prompt,
                        "width": media_item.width,
                        "height": media_item.height,
                        "media_id": str(media_item.id)
                    }
                else:
                    # Fallback if AI service couldn't generate an image
                    return JSONResponse({
                        "success": False,
                        "error": "Failed to generate image"
                    }, status_code=500)
                    
            except Exception as e:
                logger.error(f"Error generating AI image: {str(e)}")
                return JSONResponse({
                    "success": False,
                    "error": f"Error generating image: {str(e)}"
                }, status_code=500)
                
        elif content_type == "button":
            button_purpose = options.get("purpose", "cta")
            
            # Determine button style based on purpose
            button_style = "primary"
            if button_purpose == "learn":
                button_style = "outline-primary"
            elif button_purpose == "shop":
                button_style = "success"
            elif button_purpose == "signup":
                button_style = "warning"
            
            # Generate button text
            button_text = ai_service.generate_text(
                f"Generate a short, compelling button text (3-5 words) for a {button_purpose} button about: {prompt}"
            )
            
            # Clean up button text
            button_text = button_text.strip()
            import re
            button_text = re.sub(r'["""\'\'()]', '', button_text)  # Remove quotes
            button_text = re.sub(r'[\.\!]$', '', button_text)  # Remove trailing punctuation
            
            # Keep it short - max 5 words
            words = button_text.split()
            if len(words) > 5:
                button_text = " ".join(words[:5])
            
            # Generate a default URL based on purpose
            button_url = "#"
            if button_purpose == "cta" or button_purpose == "signup":
                button_url = "/contact"
            elif button_purpose == "learn":
                button_url = "/about"
            elif button_purpose == "shop":
                button_url = "/products"
            
            result = {
                "text": button_text,
                "style": button_style,
                "url": button_url
            }
        
        else:
            return JSONResponse({
                "success": False,
                "error": f"Unsupported content type: {content_type}"
            }, status_code=400)
        
        return JSONResponse({
            "success": True,
            "content_type": content_type,
            "content": result
        })
    
    except Exception as e:
        logger.error(f"Error generating AI content: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": f"Error generating content: {str(e)}"
        }, status_code=500)

# Collaborative editing routes
@router.get("/{page_id}/active-editors", response_class=JSONResponse)
async def get_active_editors(page_id: str, request: Request):
    """Get list of active editors for a page."""
    managers = get_managers()
    
    try:
        # Get the page
        page_manager = managers["page_manager"]
        page = page_manager.get(page_id)
        
        if not page:
            return JSONResponse({
                "success": False,
                "error": "Page not found"
            }, status_code=404)
        
        # Get active editors from session or cache
        # In a real implementation, this would use Redis or a database table
        # For demo purposes, we'll simulate this with a simple timestamp check
        
        # Get stored heartbeats
        active_editors = []
        
        # Get current user from session or request
        current_user_id = request.session.get("user_id", "anonymous")
        current_user_name = request.session.get("user_name", "Anonymous User")
        
        # In a real implementation, we'd check the database or cache
        # For this demo, we'll simulate collaborative editing based on the hour
        now = datetime.now()
        
        # Simulate 1-2 other editors based on time of day (for demo purposes)
        hour = now.hour
        if hour % 2 == 0:  # Even hours have 1 extra editor
            active_editors = [
                {
                    "id": current_user_id,
                    "name": current_user_name,
                    "last_active": now.isoformat()
                },
                {
                    "id": "user-123",
                    "name": "John Doe",
                    "last_active": (now - timedelta(minutes=2)).isoformat()
                }
            ]
        elif hour % 3 == 0:  # Hours divisible by 3 have 2 extra editors
            active_editors = [
                {
                    "id": current_user_id,
                    "name": current_user_name,
                    "last_active": now.isoformat()
                },
                {
                    "id": "user-123",
                    "name": "John Doe",
                    "last_active": (now - timedelta(minutes=2)).isoformat()
                },
                {
                    "id": "user-456",
                    "name": "Jane Smith",
                    "last_active": (now - timedelta(minutes=5)).isoformat()
                }
            ]
        else:  # Other hours just have the current user
            active_editors = [
                {
                    "id": current_user_id,
                    "name": current_user_name,
                    "last_active": now.isoformat()
                }
            ]
        
        return JSONResponse({
            "success": True,
            "page_id": page_id,
            "online": True,
            "active_editors": active_editors,
            "current_user_id": current_user_id
        })
    
    except Exception as e:
        logger.error(f"Error getting active editors: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": str(e),
            "online": False
        }, status_code=500)
    finally:
        managers["session"].close()

@router.post("/{page_id}/heartbeat", response_class=JSONResponse)
async def editor_heartbeat(page_id: str, request: Request, data: Dict[str, Any] = Body(...)):
    """Record editor heartbeat to show active editing."""
    # This would typically update a Redis cache or database record
    # For our demo, we'll just return success
    
    try:
        # Get current user from session
        user_id = request.session.get("user_id", "anonymous")
        
        # In a real implementation, we'd store this heartbeat
        return JSONResponse({
            "success": True,
            "timestamp": data.get("timestamp"),
            "user_id": user_id
        })
    except Exception as e:
        logger.error(f"Error recording editor heartbeat: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

# Block templates routes
@router.get("/block-templates", response_class=JSONResponse)
async def list_block_templates(request: Request):
    """List saved block templates."""
    managers = get_managers()
    
    try:
        # In a real implementation, we'd fetch these from the database
        # For demo purposes, we'll provide sample templates
        templates = [
            {
                "id": "template-1",
                "name": "Product Feature Card",
                "description": "Showcase a key product feature with image and text",
                "block_type": "text",
                "content": {
                    "html": """
                    <div class="card">
                      <div class="card-body">
                        <h5 class="card-title">Advanced Analytics</h5>
                        <p class="card-text">Our platform provides deep insights into your business performance with real-time analytics and customizable dashboards.</p>
                      </div>
                    </div>
                    """
                },
                "settings": {
                    "width": "full",
                    "alignment": "center"
                },
                "created_by": "system",
                "is_global": True
            },
            {
                "id": "template-2",
                "name": "Testimonial Block",
                "description": "Customer testimonial with quote styling",
                "block_type": "text",
                "content": {
                    "html": """
                    <blockquote class="blockquote">
                      <p>"This product transformed our business processes and saved us hours each week."</p>
                      <footer class="blockquote-footer">John Smith, <cite>CEO at TechCorp</cite></footer>
                    </blockquote>
                    """
                },
                "settings": {
                    "width": "full",
                    "alignment": "left"
                },
                "created_by": "system",
                "is_global": True
            },
            {
                "id": "template-3",
                "name": "Call to Action Button",
                "description": "Primary CTA button for important actions",
                "block_type": "button",
                "content": {
                    "text": "Get Started Today",
                    "url": "/signup",
                    "style": "primary"
                },
                "settings": {
                    "alignment": "center",
                    "size": "large"
                },
                "created_by": "system",
                "is_global": True
            }
        ]
        
        return JSONResponse({
            "success": True,
            "templates": templates
        })
    
    except Exception as e:
        logger.error(f"Error listing block templates: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)
    finally:
        managers["session"].close()

@router.post("/block-templates", response_class=JSONResponse)
async def save_block_template(request: Request, data: Dict[str, Any] = Body(...)):
    """Save a block as a reusable template."""
    managers = get_managers()
    
    try:
        block_id = data.get("block_id")
        name = data.get("name")
        description = data.get("description", "")
        is_global = data.get("is_global", True)
        
        if not block_id:
            return JSONResponse({
                "success": False,
                "error": "No block ID provided"
            }, status_code=400)
            
        if not name:
            return JSONResponse({
                "success": False,
                "error": "No template name provided"
            }, status_code=400)
        
        # Get the block to save as template
        block_manager = managers["block_manager"]
        block = block_manager.get(block_id)
        
        if not block:
            return JSONResponse({
                "success": False,
                "error": "Block not found"
            }, status_code=404)
        
        # In a real implementation, we'd save this to the database
        # For our demo, we'll just return success
        
        return JSONResponse({
            "success": True,
            "template_id": f"template-{block_id}",
            "message": f"Block saved as template: {name}"
        })
    
    except Exception as e:
        logger.error(f"Error saving block template: {str(e)}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)
    finally:
        managers["session"].close()

def setup_routes():
    """Set up routes for the page builder API."""
    logger.info("Setting up page builder API routes")
    return router