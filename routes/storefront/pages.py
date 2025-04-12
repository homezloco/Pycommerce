
"""
Storefront routes for page rendering.

This module provides routes for rendering custom website pages created with the page builder.
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

from pycommerce.models.tenant import TenantManager
from pycommerce.models.page_builder import PageManager, PageSectionManager, ContentBlockManager

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize templates
templates_dir = os.path.join(os.getcwd(), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Initialize managers
tenant_manager = TenantManager()
page_manager = PageManager()
section_manager = PageSectionManager()
block_manager = ContentBlockManager()

@router.get("/{tenant_slug}/pages/{page_slug}", response_class=HTMLResponse)
async def view_page(request: Request, tenant_slug: str, page_slug: str):
    """Render a custom page."""
    # Get the tenant
    tenant = tenant_manager.get_by_slug(tenant_slug)
    if not tenant:
        raise HTTPException(status_code=404, detail="Store not found")
    
    # Get the page
    page = page_manager.get_by_slug(str(tenant.id), page_slug)
    if not page or not page.is_published:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Get page sections
    sections = section_manager.list_by_page(str(page.id))
    
    # Get blocks for each section
    sections_with_blocks = []
    for section in sections:
        blocks = block_manager.list_by_section(str(section.id))
        sections_with_blocks.append({
            "section": section,
            "blocks": blocks
        })
    
    return templates.TemplateResponse(
        "store/page.html",
        {
            "request": request,
            "tenant": tenant,
            "page": page,
            "sections": sections_with_blocks,
            "preview_mode": False
        }
    )

def setup_routes(app):
    """Set up routes for the application."""
    app.include_router(router)
