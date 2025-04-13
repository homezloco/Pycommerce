"""
Admin routes for page builder.

This module provides routes for managing custom pages in the admin interface.
"""
import logging
import json
from typing import Dict, Optional, List, Any

from fastapi import APIRouter, Form, HTTPException, Request, status, Body
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from pycommerce.models.page_builder import PageManager, PageSectionManager, ContentBlockManager, PageTemplateManager
from pycommerce.models.tenant import TenantManager
from pycommerce.services.wysiwyg_service import WysiwygService

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
template_manager = PageTemplateManager()
wysiwyg_service = WysiwygService()

def setup_routes(jinja_templates: Jinja2Templates = None):
    """Setup page builder routes with the given templates."""
    global templates
    templates = jinja_templates
    logger.info("Setting up page builder routes with templates")
    # Ensure the router is properly configured and returned
    return router

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
            url=f"/admin/pages/create?tenant={tenant.slug if 'tenant' in locals() and tenant else ''}&status_message=Error+creating+page:+{str(e)}&status_type=danger",
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
            status_code=status.HTTP_303_SEE_OTHER
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