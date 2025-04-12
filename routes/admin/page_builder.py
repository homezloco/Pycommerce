"""
Admin routes for page builder.

This module provides routes for managing custom pages in the admin interface.
"""
import logging
from typing import Dict, Optional, List

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from pycommerce.models.page_builder import PageManager, PageSectionManager, ContentBlockManager
from pycommerce.models.tenant import TenantManager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])

# Template setup will be passed from main app
templates = None

# Initialize managers
tenant_manager = TenantManager()
page_manager = PageManager()
section_manager = PageSectionManager()
block_manager = ContentBlockManager()

@router.get("/pages", response_class=HTMLResponse)
async def pages_list(
    request: Request,
    tenant: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for listing custom pages."""
    # Get all tenants for the sidebar
    tenants = tenant_manager.get_all()

    # Get tenant from query parameters or session
    selected_tenant_slug = tenant or request.session.get("selected_tenant")

    # If no tenant is selected and we have tenants, select the first one
    if not selected_tenant_slug and tenants:
        selected_tenant_slug = tenants[0].slug

    # Store the selected tenant in session for future requests
    if selected_tenant_slug:
        request.session["selected_tenant"] = selected_tenant_slug

    # Get tenant object and pages
    tenant_obj = None
    pages = []
    if selected_tenant_slug:
        tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
        if tenant_obj:
            pages = page_manager.list_by_tenant(str(tenant_obj.id), include_unpublished=True)

    return templates.TemplateResponse(
        "admin/pages/list.html",
        {
            "request": request,
            "selected_tenant": selected_tenant_slug,
            "tenant": tenant_obj,
            "tenants": tenants,
            "active_page": "pages",
            "pages": pages,
            "status_message": status_message,
            "status_type": status_type
        }
    )

@router.get("/pages/create", response_class=HTMLResponse)
async def create_page_form(
    request: Request,
    tenant: Optional[str] = None
):
    """Admin page for creating a new custom page."""
    # Get all tenants for the sidebar
    tenants = tenant_manager.get_all()

    # Get tenant from query parameters or session
    selected_tenant_slug = tenant or request.session.get("selected_tenant")

    # If no tenant is selected and we have tenants, select the first one
    if not selected_tenant_slug and tenants:
        selected_tenant_slug = tenants[0].slug

    # Store the selected tenant in session for future requests
    if selected_tenant_slug:
        request.session["selected_tenant"] = selected_tenant_slug

    # Get tenant object
    tenant_obj = None
    if selected_tenant_slug:
        tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)

    return templates.TemplateResponse(
        "admin/pages/create.html",
        {
            "request": request,
            "selected_tenant": selected_tenant_slug,
            "tenant": tenant_obj,
            "tenants": tenants,
            "active_page": "pages"
        }
    )

@router.post("/pages/create", response_class=RedirectResponse)
async def create_page(
    request: Request,
    tenant_id: str = Form(...),
    title: str = Form(...),
    slug: str = Form(...),
    meta_description: Optional[str] = Form(None),
    is_published: bool = Form(False)
):
    """Create a new custom page."""
    try:
        # Create page
        page_data = {
            "tenant_id": tenant_id,
            "title": title,
            "slug": slug,
            "meta_description": meta_description,
            "is_published": is_published
        }

        page = page_manager.create(page_data)

        # Get tenant slug for redirect
        tenant = tenant_manager.get(tenant_id)
        tenant_slug = tenant.slug if tenant else None

        return RedirectResponse(
            url=f"/admin/pages/edit/{page.id}?tenant={tenant_slug}&status_message=Page+created+successfully&status_type=success",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Error creating page: {str(e)}")
        return RedirectResponse(
            url=f"/admin/pages?tenant={tenant_slug if tenant_slug else ''}&status_message=Error+creating+page:+{str(e)}&status_type=danger",
            status_code=status.HTTP_303_SEE_OTHER
        )

@router.get("/pages/edit/{page_id}", response_class=HTMLResponse)
async def edit_page(
    request: Request,
    page_id: str,
    tenant: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for editing a custom page."""
    # Get all tenants for the sidebar
    tenants = tenant_manager.get_all()

    # Get tenant from query parameters or session
    selected_tenant_slug = tenant or request.session.get("selected_tenant")

    # If no tenant is selected and we have tenants, select the first one
    if not selected_tenant_slug and tenants:
        selected_tenant_slug = tenants[0].slug

    # Store the selected tenant in session for future requests
    if selected_tenant_slug:
        request.session["selected_tenant"] = selected_tenant_slug

    # Get page
    page = page_manager.get(page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    # Get page sections and blocks
    sections = section_manager.list_by_page(page_id)
    sections_with_blocks = []
    for section in sections:
        blocks = block_manager.list_by_section(str(section.id))
        sections_with_blocks.append({
            "section": section,
            "blocks": blocks
        })

    # Get tenant object
    tenant_obj = tenant_manager.get(page.tenant_id)

    return templates.TemplateResponse(
        "admin/pages/editor.html",
        {
            "request": request,
            "selected_tenant": selected_tenant_slug,
            "tenant": tenant_obj,
            "tenants": tenants,
            "active_page": "pages",
            "page": page,
            "sections": sections_with_blocks,
            "status_message": status_message,
            "status_type": status_type
        }
    )

def setup_routes(app_templates):
    """
    Set up routes with the given templates.

    Args:
        app_templates: Jinja2Templates instance from the main app
    """
    global templates
    templates = app_templates
    return router


class ContentBlockManager:
    """Manager for content block operations."""
import logging
import json
import os
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Request, Form, Body, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette import status

from pycommerce.models.tenant import TenantManager
from pycommerce.models.page_builder import (
    PageManager, PageSectionManager, ContentBlockManager, PageTemplateManager
)
from pycommerce.services.wysiwyg_service import WysiwygService
from pycommerce.services.media_service import MediaService

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])

# Initialize templates
templates_dir = os.path.join(os.getcwd(), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Initialize managers
tenant_manager = TenantManager()
page_manager = PageManager()
section_manager = PageSectionManager()
block_manager = ContentBlockManager()
template_manager = PageTemplateManager()

# Initialize services
wysiwyg_service = WysiwygService()
media_service = MediaService()

@router.get("/pages", response_class=HTMLResponse)
async def list_pages(request: Request):
    """List all pages."""
    tenant_id = request.session.get("tenant_id")
    if not tenant_id:
        return RedirectResponse("/admin/stores", status_code=status.HTTP_302_FOUND)

    pages = page_manager.list_by_tenant(tenant_id, include_unpublished=True)

    return templates.TemplateResponse(
        "admin/pages/list.html",
        {
            "request": request,
            "pages": pages,
            "active_page": "pages"
        }
    )

@router.get("/pages/create", response_class=HTMLResponse)
async def create_page_form(request: Request):
    """Show page creation form."""
    tenant_id = request.session.get("tenant_id")
    if not tenant_id:
        return RedirectResponse("/admin/stores", status_code=status.HTTP_302_FOUND)

    page_templates = template_manager.list_templates()

    return templates.TemplateResponse(
        "admin/pages/create.html",
        {
            "request": request,
            "templates": page_templates,
            "active_page": "pages"
        }
    )

@router.post("/pages/create")
async def create_page(
    request: Request,
    title: str = Form(...),
    slug: str = Form(...),
    meta_title: str = Form(None),
    meta_description: str = Form(None),
    template_id: str = Form(None)
):
    """Create a new page."""
    tenant_id = request.session.get("tenant_id")
    if not tenant_id:
        return RedirectResponse("/admin/stores", status_code=status.HTTP_302_FOUND)

    # Create page
    page_data = {
        "tenant_id": tenant_id,
        "title": title,
        "slug": slug,
        "meta_title": meta_title or title,
        "meta_description": meta_description or "",
        "is_published": False,
        "layout_data": {}
    }

    try:
        page = page_manager.create(page_data)

        # If template selected, apply template data
        if template_id:
            template = template_manager.get(template_id)
            if template and template.template_data:
                # Create sections from template
                template_sections = template.template_data.get("sections", [])
                for section_data in template_sections:
                    section = section_manager.create({
                        "page_id": page.id,
                        "section_type": section_data.get("section_type", "content"),
                        "position": section_data.get("position", 0),
                        "settings": section_data.get("settings", {})
                    })

                    # Create blocks if specified in template
                    template_blocks = section_data.get("blocks", [])
                    for block_data in template_blocks:
                        block_manager.create({
                            "section_id": section.id,
                            "block_type": block_data.get("block_type", "text"),
                            "position": block_data.get("position", 0),
                            "content": block_data.get("content", {}),
                            "settings": block_data.get("settings", {})
                        })

        # Redirect to editor
        return RedirectResponse(f"/admin/pages/edit/{page.id}", status_code=status.HTTP_302_FOUND)
    except Exception as e:
        logger.error(f"Error creating page: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Failed to create page: {str(e)}"}
        )

@router.get("/pages/edit/{page_id}", response_class=HTMLResponse)
async def edit_page(request: Request, page_id: str):
    """Edit page using visual page builder."""
    tenant_id = request.session.get("tenant_id")
    if not tenant_id:
        return RedirectResponse("/admin/stores", status_code=status.HTTP_302_FOUND)

    page = page_manager.get(page_id)
    if not page or page.tenant_id != tenant_id:
        return RedirectResponse("/admin/pages", status_code=status.HTTP_302_FOUND)

    sections = section_manager.list_by_page(page_id)

    # Get blocks for each section
    section_blocks = {}
    for section in sections:
        section_blocks[str(section.id)] = block_manager.list_by_section(section.id)

    media_items = media_service.list_media(tenant_id)

    return templates.TemplateResponse(
        "admin/pages/editor.html",
        {
            "request": request,
            "page": page,
            "sections": sections,
            "section_blocks": section_blocks,
            "media_items": media_items,
            "active_page": "pages"
        }
    )

@router.post("/pages/update/{page_id}")
async def update_page(
    request: Request,
    page_id: str,
    page_data: Dict[str, Any] = Body(...)
):
    """Update page settings."""
    tenant_id = request.session.get("tenant_id")
    if not tenant_id:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Unauthorized"}
        )

    try:
        page = page_manager.get(page_id)
        if not page or page.tenant_id != tenant_id:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Page not found"}
            )

        updated_page = page_manager.update(page_id, page_data)
        return JSONResponse(content={"success": True, "page": {
            "id": str(updated_page.id),
            "title": updated_page.title,
            "slug": updated_page.slug,
            "is_published": updated_page.is_published
        }})
    except Exception as e:
        logger.error(f"Error updating page: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Failed to update page: {str(e)}"}
        )

@router.post("/pages/delete/{page_id}")
async def delete_page(request: Request, page_id: str):
    """Delete a page."""
    tenant_id = request.session.get("tenant_id")
    if not tenant_id:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Unauthorized"}
        )

    try:
        page = page_manager.get(page_id)
        if not page or page.tenant_id != tenant_id:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Page not found"}
            )

        success = page_manager.delete(page_id)
        if success:
            return JSONResponse(content={"success": True})
        else:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Failed to delete page"}
            )
    except Exception as e:
        logger.error(f"Error deleting page: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Failed to delete page: {str(e)}"}
        )

@router.post("/pages/sections/create/{page_id}")
async def create_section(
    request: Request,
    page_id: str,
    section_data: Dict[str, Any] = Body(...)
):
    """Create a new section in a page."""
    tenant_id = request.session.get("tenant_id")
    if not tenant_id:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Unauthorized"}
        )

    try:
        page = page_manager.get(page_id)
        if not page or page.tenant_id != tenant_id:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Page not found"}
            )

        section_data["page_id"] = page_id
        section = section_manager.create(section_data)

        return JSONResponse(content={
            "success": True,
            "section": {
                "id": str(section.id),
                "section_type": section.section_type,
                "position": section.position,
                "settings": section.settings
            }
        })
    except Exception as e:
        logger.error(f"Error creating section: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Failed to create section: {str(e)}"}
        )

@router.post("/pages/blocks/create/{section_id}")
async def create_block(
    request: Request,
    section_id: str,
    block_data: Dict[str, Any] = Body(...)
):
    """Create a new content block in a section."""
    tenant_id = request.session.get("tenant_id")
    if not tenant_id:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Unauthorized"}
        )

    try:
        section = section_manager.get(section_id)
        if not section:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Section not found"}
            )

        page = page_manager.get(section.page_id)
        if not page or page.tenant_id != tenant_id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Unauthorized"}
            )

        block_data["section_id"] = section_id
        block = block_manager.create(block_data)

        return JSONResponse(content={
            "success": True,
            "block": {
                "id": str(block.id),
                "block_type": block.block_type,
                "position": block.position,
                "content": block.content,
                "settings": block.settings
            }
        })
    except Exception as e:
        logger.error(f"Error creating block: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Failed to create block: {str(e)}"}
        )


@router.get("/pages", response_class=HTMLResponse)
async def pages_list(
    request: Request,
    tenant: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page listing all pages."""
    # Get all tenants for the sidebar
    tenants = tenant_manager.get_all()

    # Get tenant from query parameters or session
    selected_tenant_slug = tenant or request.session.get("selected_tenant")

    # If no tenant is selected and we have tenants, select the first one
    if not selected_tenant_slug and tenants:
        selected_tenant_slug = tenants[0].slug

    # Store the selected tenant in session for future requests
    if selected_tenant_slug:
        request.session["selected_tenant"] = selected_tenant_slug

    # Get tenant object and pages
    tenant_obj = None
    pages = []
    if selected_tenant_slug:
        tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
        if tenant_obj:
            # Get pages for the tenant
            pages = page_manager.list_by_tenant(str(tenant_obj.id), include_unpublished=True)

    return templates.TemplateResponse(
        "admin/pages/list.html",
        {
            "request": request,
            "selected_tenant": selected_tenant_slug,
            "tenant": tenant_obj,
            "tenants": tenants,
            "pages": pages,
            "active_page": "pages",
            "search": search,
            "current_page": page,
            "limit": limit,
            "status_message": status_message,
            "status_type": status_type
        }
    )


@router.get("/pages/create", response_class=HTMLResponse)
async def page_create_form(
    request: Request,
    tenant: Optional[str] = None,
    template_id: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin form to create a new page."""
    # Get all tenants for the sidebar
    tenants = tenant_manager.get_all()

    # Get tenant from query parameters or session
    selected_tenant_slug = tenant or request.session.get("selected_tenant")

    # If no tenant is selected and we have tenants, select the first one
    if not selected_tenant_slug and tenants:
        selected_tenant_slug = tenants[0].slug

    # Store the selected tenant in session for future requests
    if selected_tenant_slug:
        request.session["selected_tenant"] = selected_tenant_slug

    # Get tenant object
    tenant_obj = None
    if selected_tenant_slug:
        tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)

    # Get page template if specified
    template = None
    if template_id:
        template = template_manager.get(template_id)

    # Get available page templates
    templates_list = template_manager.list_templates()

    # Get editor configuration
    editor_config = wysiwyg_service.get_editor_config('tinymce', {
        'tenant_id': str(tenant_obj.id) if tenant_obj else None,
        'media_browse_url': '/admin/api/media'
    })

    return templates.TemplateResponse(
        "admin/pages/create.html",
        {
            "request": request,
            "selected_tenant": selected_tenant_slug,
            "tenant": tenant_obj,
            "tenants": tenants,
            "active_page": "pages",
            "template": template,
            "templates": templates_list,
            "editor_config": json.dumps(editor_config),
            "status_message": status_message,
            "status_type": status_type
        }
    )


@router.post("/pages/create", response_class=RedirectResponse)
async def page_create(
    request: Request,
    tenant_id: str = Form(...),
    title: str = Form(...),
    slug: str = Form(...),
    meta_title: Optional[str] = Form(None),
    meta_description: Optional[str] = Form(None),
    template_id: Optional[str] = Form(None),
    is_published: bool = Form(False),
    content: Optional[str] = Form(None)
):
    """Create a new page."""
    try:
        # Get tenant
        tenant = tenant_manager.get(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=404,
                detail=f"Tenant with ID {tenant_id} not found"
            )

        # Check if the slug is already in use
        existing_page = page_manager.get_by_slug(tenant_id, slug)
        if existing_page:
            return RedirectResponse(
                url=f"/admin/pages/create?tenant={tenant.slug}&status_message=A+page+with+this+slug+already+exists&status_type=danger",
                status_code=status.HTTP_303_SEE_OTHER
            )

        # Process the content if provided
        processed_content = None
        if content:
            processed_content, media_refs = wysiwyg_service.process_editor_content(content, tenant_id)

        # Create initial layout data
        layout_data = None
        if template_id:
            template = template_manager.get(template_id)
            if template:
                layout_data = template.template_data
        else:
            # Create a basic layout if no template is selected
            layout_data = {
                "type": "page",
                "sections": []
            }

        # Create the page
        page_data = {
            "tenant_id": tenant_id,
            "title": title,
            "slug": slug,
            "meta_title": meta_title or title,
            "meta_description": meta_description,
            "is_published": is_published,
            "layout_data": layout_data
        }

        page = page_manager.create(page_data)

        # If we have content, create a default section with a text block
        if processed_content and page:
            # Create a main content section
            section_data = {
                "page_id": str(page.id),
                "section_type": "content",
                "position": 0,
                "settings": {
                    "padding": "medium",
                    "background": "white"
                }
            }

            section = section_manager.create(section_data)

            # Create a text block with the content
            block_data = {
                "section_id": str(section.id),
                "block_type": "text",
                "position": 0,
                "content": {
                    "html": processed_content
                },
                "settings": {
                    "width": "normal"
                }
            }

            block_manager.create(block_data)

        return RedirectResponse(
            url=f"/admin/pages/edit/{page.id}?tenant={tenant.slug}&status_message=Page+created+successfully&status_type=success",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Error creating page: {str(e)}")
        return RedirectResponse(
            url=f"/admin/pages/create?tenant={tenant.slug if tenant else ''}&status_message=Error+creating+page:+{str(e)}&status_type=danger",
            status_code=status.HTTP_303_SEE_OTHER
        )


@router.get("/pages/edit/{page_id}", response_class=HTMLResponse)
async def page_edit_form(
    request: Request,
    page_id: str,
    tenant: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin form to edit a page."""
    # Get the page
    page = page_manager.get(page_id)
    if not page:
        raise HTTPException(
            status_code=404,
            detail=f"Page with ID {page_id} not found"
        )

    # Get the tenant
    tenant_obj = tenant_manager.get(str(page.tenant_id))
    if not tenant_obj:
        raise HTTPException(
            status_code=404,
            detail=f"Tenant with ID {page.tenant_id} not found"
        )

    # Get all tenants for the sidebar
    tenants = tenant_manager.get_all()

    # Set the selected tenant
    selected_tenant_slug = tenant_obj.slug
    request.session["selected_tenant"] = selected_tenant_slug

    # Get page sections
    sections = section_manager.list_by_page(page_id)

    # Get blocks for each section
    sections_with_blocks = []
    for section in sections:
        blocks = block_manager.list_by_section(str(section.id))
        sections_with_blocks.append({
            "section": section,
            "blocks": blocks
        })

    # Get editor configuration
    editor_config = wysiwyg_service.get_editor_config('tinymce', {
        'tenant_id': str(tenant_obj.id),
        'media_browse_url': '/admin/api/media'
    })

    return templates.TemplateResponse(
        "admin/pages/edit.html",
        {
            "request": request,
            "selected_tenant": selected_tenant_slug,
            "tenant": tenant_obj,
            "tenants": tenants,
            "active_page": "pages",
            "page": page,
            "sections": sections_with_blocks,
            "editor_config": json.dumps(editor_config),
            "status_message": status_message,
            "status_type": status_type
        }
    )


@router.post("/pages/edit/{page_id}", response_class=RedirectResponse)
async def page_update(
    request: Request,
    page_id: str,
    title: str = Form(...),
    slug: str = Form(...),
    meta_title: Optional[str] = Form(None),
    meta_description: Optional[str] = Form(None),
    is_published: bool = Form(False),
    layout_data: Optional[str] = Form(None)
):
    """Update a page."""
    try:
        # Get the page
        page = page_manager.get(page_id)
        if not page:
            raise HTTPException(
                status_code=404,
                detail=f"Page with ID {page_id} not found"
            )

        # Get the tenant
        tenant = tenant_manager.get(str(page.tenant_id))
        if not tenant:
            raise HTTPException(
                status_code=404,
                detail=f"Tenant with ID {page.tenant_id} not found"
            )

        # Check if the slug is already in use by another page
        existing_page = page_manager.get_by_slug(str(page.tenant_id), slug)
        if existing_page and str(existing_page.id) != page_id:
            return RedirectResponse(
                url=f"/admin/pages/edit/{page_id}?tenant={tenant.slug}&status_message=A+different+page+with+this+slug+already+exists&status_type=danger",
                status_code=status.HTTP_303_SEE_OTHER
            )

        # Parse layout data if provided
        parsed_layout_data = None
        if layout_data:
            try:
                parsed_layout_data = json.loads(layout_data)
            except json.JSONDecodeError:
                return RedirectResponse(
                    url=f"/admin/pages/edit/{page_id}?tenant={tenant.slug}&status_message=Invalid+layout+data+format&status_type=danger",
                    status_code=status.HTTP_303_SEE_OTHER
                )

        # Update the page
        page_data = {
            "title": title,
            "slug": slug,
            "meta_title": meta_title or title,
            "meta_description": meta_description,
            "is_published": is_published
        }

        if parsed_layout_data:
            page_data["layout_data"] = parsed_layout_data

        page_manager.update(page_id, page_data)

        return RedirectResponse(
            url=f"/admin/pages/edit/{page_id}?tenant={tenant.slug}&status_message=Page+updated+successfully&status_type=success",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Error updating page: {str(e)}")
        # Get the tenant for redirect
        tenant_slug = ""
        try:
            page = page_manager.get(page_id)
            if page:
                tenant = tenant_manager.get(str(page.tenant_id))
                if tenant:
                    tenant_slug = tenant.slug
        except:
            pass

        return RedirectResponse(
            url=f"/admin/pages/edit/{page_id}?tenant={tenant_slug}&status_message=Error+updating+page:+{str(e)}&status_type=danger",
            status_code=status.HTTP_33_SEE_OTHER
        )


@router.post("/pages/delete/{page_id}", response_class=RedirectResponse)
async def page_delete(
    request: Request,
    page_id: str
):
    """Delete a page."""
    try:
        # Get the page
        page = page_manager.get(page_id)
        if not page:
            raise HTTPException(
                status_code=404,
                detail=f"Page with ID {page_id} not found"
            )

        # Get the tenant for redirect
        tenant = tenant_manager.get(str(page.tenant_id))
        tenant_slug = tenant.slug if tenant else ""

        # Delete the page
        page_manager.delete(page_id)

        return RedirectResponse(
            url=f"/admin/pages?tenant={tenant_slug}&status_message=Page+deleted+successfully&status_type=success",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Error deleting page: {str(e)}")
        # Try to get the tenant for redirect
        tenant_slug = ""
        try:
            page = page_manager.get(page_id)
            if page:
                tenant = tenant_manager.get(str(page.tenant_id))
                if tenant:
                    tenant_slug = tenant.slug
        except:
            pass

        return RedirectResponse(
            url=f"/admin/pages?tenant={tenant_slug}&status_message=Error+deleting+page:+{str(e)}&status_type=danger",
            status_code=status.HTTP_303_SEE_OTHER
        )


@router.get("/pages/preview/{page_id}", response_class=HTMLResponse)
async def page_preview(
    request: Request,
    page_id: str
):
    """Preview a page."""
    # Get the page
    page = page_manager.get(page_id)
    if not page:
        raise HTTPException(
            status_code=404,
            detail=f"Page with ID {page_id} not found"
        )

    # Get the tenant
    tenant = tenant_manager.get(str(page.tenant_id))
    if not tenant:
        raise HTTPException(
            status_code=404,
            detail=f"Tenant with ID {page.tenant_id} not found"
        )

    # Get page sections
    sections = section_manager.list_by_page(page_id)

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
            "preview_mode": True
        }
    )


@router.get("/page-templates", response_class=HTMLResponse)
async def page_templates_list(
    request: Request,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page listing all page templates."""
    # Get all tenants for the sidebar
    tenants = tenant_manager.get_all()

    # Get selected tenant from session
    selected_tenant_slug = request.session.get("selected_tenant")

    # Get templates
    templates_list = template_manager.list_templates()

    return templates.TemplateResponse(
        "admin/pages/templates.html",
        {
            "request": request,
            "selected_tenant": selected_tenant_slug,
            "tenants": tenants,
            "templates": templates_list,
            "active_page": "page-templates",
            "status_message": status_message,
            "status_type": status_type
        }
    )


# API routes for page builder components
@router.post("/api/pages/sections", response_class=JSONResponse)
async def create_section(
    section_data: Dict[str, Any] = Body(...)
):
    """Create a new section."""
    try:
        section = section_manager.create(section_data)
        return {
            "id": str(section.id),
            "page_id": str(section.page_id),
            "section_type": section.section_type,
            "position": section.position,
            "settings": section.settings,
            "created_at": section.created_at.isoformat(),
            "updated_at": section.updated_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Error creating section: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating section: {str(e)}")


@router.put("/api/pages/sections/{section_id}", response_class=JSONResponse)
async def update_section(
    section_id: str,
    section_data: Dict[str, Any] = Body(...)
):
    """Update a section."""
    try:
        section = section_manager.update(section_id, section_data)
        if not section:
            raise HTTPException(status_code=404, detail=f"Section with ID {section_id} not found")

        return {
            "id": str(section.id),
            "page_id": str(section.page_id),
            "section_type": section.section_type,
            "position": section.position,
            "settings": section.settings,
            "created_at": section.created_at.isoformat(),
            "updated_at": section.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating section: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating section: {str(e)}")


@router.delete("/api/pages/sections/{section_id}", response_class=JSONResponse)
async def delete_section(section_id: str):
    """Delete a section."""
    try:
        success = section_manager.delete(section_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Section with ID {section_id} not found")

        return {"success": True, "message": "Section deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting section: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting section: {str(e)}")


@router.post("/api/pages/blocks", response_class=JSONResponse)
async def create_block(
    block_data: Dict[str, Any] = Body(...)
):
    """Create a new content block."""
    try:
        # If there's HTML content, process it
        if "content" in block_data and "html" in block_data["content"]:
            tenant_id = None
            try:
                # Try to get the tenant ID from the section
                section = section_manager.get(block_data["section_id"])
                if section:
                    page = page_manager.get(str(section.page_id))
                    if page:
                        tenant_id = str(page.tenant_id)
            except:
                pass

            html_content = block_data["content"]["html"]
            processed_html, media_refs = wysiwyg_service.process_editor_content(html_content, tenant_id)
            block_data["content"]["html"] = processed_html

        block = block_manager.create(block_data)
        return {
            "id": str(block.id),
            "section_id": str(block.section_id),
            "block_type": block.block_type,
            "position": block.position,
            "content": block.content,
            "settings": block.settings,
            "created_at": block.created_at.isoformat(),
            "updated_at": block.updated_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Error creating block: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating block: {str(e)}")


@router.put("/api/pages/blocks/{block_id}", response_class=JSONResponse)
async def update_block(
    block_id: str,
    block_data: Dict[str, Any] = Body(...)
):
    """Update a content block."""
    try:
        # If there's HTML content, process it
        if "content" in block_data and "html" in block_data["content"]:
            tenant_id = None
            try:
                # Try to get the tenant ID from the block
                block = block_manager.get(block_id)
                if block:
                    section = section_manager.get(str(block.section_id))
                    if section:
                        page = page_manager.get(str(section.page_id))
                        if page:
                            tenant_id = str(page.tenant_id)
            except:
                pass

            html_content = block_data["content"]["html"]
            processed_html, media_refs = wysiwyg_service.process_editor_content(html_content, tenant_id)
            block_data["content"]["html"] = processed_html

        block = block_manager.update(block_id, block_data)
        if not block:
            raise HTTPException(status_code=404, detail=f"Block with ID {block_id} not found")

        return {
            "id": str(block.id),
            "section_id": str(block.section_id),
            "block_type": block.block_type,
            "position": block.position,
            "content": block.content,
            "settings": block.settings,
            "created_at": block.created_at.isoformat(),
            "updated_at": block.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating block: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating block: {str(e)}")


@router.delete("/api/pages/blocks/{block_id}", response_class=JSONResponse)
async def delete_block(block_id: str):
    """Delete a content block."""
    try:
        success = block_manager.delete(block_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Block with ID {block_id} not found")

        return {"success": True, "message": "Block deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting block: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting block: {str(e)}")


def setup_routes(app_templates):
    """
    Set up routes with the given templates.

    Args:
        app_templates: Jinja2Templates instance from the main app
    """
    global templates
    templates = app_templates
    return router