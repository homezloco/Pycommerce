
"""
Page routes for the PyCommerce storefront.

This module defines the routes for dynamic pages created via the page builder.
"""
import logging
from typing import Optional, Dict, List, Any
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from pycommerce.models.tenant import TenantManager
from pycommerce.models.page_builder import PageManager, PageSectionManager, ContentBlockManager

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["pages"])

# Global variables initialized in setup_routes
templates = None
tenant_manager = TenantManager()
page_manager = PageManager()
section_manager = PageSectionManager()
block_manager = ContentBlockManager()

def setup_routes(jinja_templates: Jinja2Templates = None):
    """
    Setup the page routes with the given templates.
    
    Args:
        jinja_templates: The Jinja2Templates instance to use
    """
    global templates
    templates = jinja_templates
    
    # Return the router for FastAPI to use
    return router

@router.get("/page/{slug}", response_class=HTMLResponse)
async def page(request: Request, slug: str):
    """
    Render a dynamically created page.
    
    Args:
        request: The FastAPI request object
        slug: The page slug
        
    Returns:
        The rendered page or a redirect if the page is not found
    """
    tenant = tenant_manager.get_tenant_for_request(request)
    
    if not tenant:
        return RedirectResponse(url="/stores")
    
    # Get the page by slug
    page_data = page_manager.get_by_slug(str(tenant.id), slug)
    
    if not page_data:
        return RedirectResponse(url="/")
    
    # Get page sections
    sections = section_manager.list_by_page(str(page_data.id))

    # Get blocks for each section
    sections_with_blocks = []
    for section in sections:
        blocks = block_manager.list_by_section(str(section.id))
        sections_with_blocks.append({
            "section": section,
            "blocks": blocks
        })
    
    # Render the page
    return templates.TemplateResponse(
        "store/page.html",
        {
            "request": request,
            "tenant": tenant,
            "page": page_data,
            "sections": sections_with_blocks,
            "content": page_data.content if hasattr(page_data, "content") else "",
            "title": page_data.title
        }
    )
