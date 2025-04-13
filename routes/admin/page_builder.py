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

from pycommerce.models.page_builder import PageManager, PageSectionManager, ContentBlockManager, PageTemplateManager, Page
from pycommerce.models.tenant import TenantManager
from pycommerce.services.wysiwyg_service import WysiwygService
from pycommerce.core.db import SessionLocal

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])

# Template setup will be passed from main app
templates = None

# Initialize services
wysiwyg_service = WysiwygService()

# Managers will be initialized with a session when needed
tenant_manager = None
page_manager = None
section_manager = None
block_manager = None
template_manager = None

def get_managers():
    """Get managers with a fresh session."""
    session = SessionLocal()
    return {
        "tenant_manager": TenantManager(session),
        "page_manager": PageManager(session),
        "section_manager": PageSectionManager(session),
        "block_manager": ContentBlockManager(session),
        "template_manager": PageTemplateManager(session),
        "session": session
    }
</old_str>

# Debug endpoint
@router.get("/debug-pages", response_class=JSONResponse)
async def debug_pages(request: Request, tenant: Optional[str] = None):
    """Debug endpoint to check tenant and page data."""
    managers = get_managers()
    try:
        # Get local manager instances with a session
        tenant_manager = managers["tenant_manager"]
        page_manager = managers["page_manager"]
        
        # Get all tenants
        logger.info("Fetching all tenants")
        tenants = tenant_manager.get_all()
        logger.info(f"Found {len(tenants)} tenants")
        tenant_list = [{"id": str(t.id), "name": t.name, "slug": t.slug} for t in tenants]

        # Get selected tenant
        selected_tenant_slug = tenant or request.session.get("selected_tenant")
        logger.info(f"Selected tenant slug: {selected_tenant_slug}")
        if not selected_tenant_slug and tenants:
            selected_tenant_slug = tenants[0].slug
            logger.info(f"Auto-selected tenant slug: {selected_tenant_slug}")

        # Get tenant object
        tenant_obj = None
        tenant_pages = []
        if selected_tenant_slug:
            logger.info(f"Getting tenant by slug: {selected_tenant_slug}")
            tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
            logger.info(f"Got tenant: {tenant_obj}")
            if tenant_obj:
                # Try to get pages
                logger.info(f"Listing pages for tenant {tenant_obj.id}")
                try:
                    pages = page_manager.list_by_tenant(str(tenant_obj.id), include_unpublished=True)
                    logger.info(f"Found {len(pages)} pages")
                    tenant_pages = [{"id": str(p.id), "title": p.title, "slug": p.slug} for p in pages]
                except Exception as e:
                    logger.error(f"Error listing pages: {str(e)}")
                    tenant_pages = []

        # Check database tables
        try:
            from sqlalchemy import inspect
            from pycommerce.core.db import engine

            inspector = inspect(engine)
            tables = inspector.get_table_names()

            # Check if page builder tables exist
            has_pages_table = 'pages' in tables
            has_sections_table = 'page_sections' in tables
            has_blocks_table = 'content_blocks' in tables
            has_templates_table = 'page_templates' in tables

            # Get table counts
            page_count = 0
            section_count = 0
            block_count = 0
            template_count = 0

            from sqlalchemy import text
            with engine.connect() as conn:
                if has_pages_table:
                    result = conn.execute(text("SELECT COUNT(*) FROM pages"))
                    page_count = result.scalar()

                if has_sections_table:
                    result = conn.execute(text("SELECT COUNT(*) FROM page_sections"))
                    section_count = result.scalar()

                if has_blocks_table:
                    result = conn.execute(text("SELECT COUNT(*) FROM content_blocks"))
                    block_count = result.scalar()

                if has_templates_table:
                    result = conn.execute(text("SELECT COUNT(*) FROM page_templates"))
                    template_count = result.scalar()

            db_info = {
                "tables_exist": {
                    "pages": has_pages_table,
                    "page_sections": has_sections_table,
                    "content_blocks": has_blocks_table,
                    "page_templates": has_templates_table
                },
                "record_counts": {
                    "pages": page_count,
                    "page_sections": section_count,
                    "content_blocks": block_count,
                    "page_templates": template_count
                }
            }
        except Exception as e:
            logger.error(f"Error checking database tables: {str(e)}")
            db_info = {"error": str(e)}

        return {
            "success": True,
            "tenants_count": len(tenant_list),
            "tenants": tenant_list,
            "selected_tenant_slug": selected_tenant_slug,
            "tenant": {
                "id": str(tenant_obj.id) if tenant_obj else None,
                "name": tenant_obj.name if tenant_obj else None,
                "slug": tenant_obj.slug if tenant_obj else None
            } if tenant_obj else None,
            "pages_count": len(tenant_pages),
            "pages": tenant_pages,
            "database_info": db_info
        }
    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
    finally:
        # Make sure to close the session
        managers["session"].close()

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
    logger.info("Accessing pages listing route")
    managers = get_managers()
    session = managers["session"]
    
    try:
        # Get local manager instances with a session
        tenant_manager = managers["tenant_manager"]
        page_manager = managers["page_manager"]
        
        # Check if templates are properly set up
        if templates is None:
            logger.error("Templates object is None. Check setup_routes function.")
            return JSONResponse({"error": "Templates not properly initialized"}, status_code=500)

        # Get all tenants for the sidebar
        logger.info("Fetching all tenants")
        try:
            tenants = tenant_manager.get_all()
            logger.info(f"Found {len(tenants)} tenants: {[t.name for t in tenants]}")
        except Exception as e:
            logger.error(f"Error getting all tenants: {str(e)}")
            return JSONResponse({"error": f"Error getting tenants: {str(e)}"}, status_code=500)

        # Get tenant from query parameters or session
        selected_tenant_slug = tenant or request.session.get("selected_tenant")
        logger.info(f"Initial selected tenant slug: {selected_tenant_slug}")

        # If no tenant is selected and we have tenants, select the first one
        if not selected_tenant_slug and tenants:
            selected_tenant_slug = tenants[0].slug
            logger.info(f"Auto-selected tenant slug: {selected_tenant_slug}")

        # Store the selected tenant in session for future requests
        if selected_tenant_slug:
            request.session["selected_tenant"] = selected_tenant_slug
            logger.info(f"Stored tenant slug in session: {selected_tenant_slug}")

        # Get tenant object and pages
        tenant_obj = None
        pages = []
        if selected_tenant_slug:
            try:
                logger.info(f"Getting tenant by slug: {selected_tenant_slug}")
                tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
                logger.info(f"Found tenant: {tenant_obj.name if tenant_obj else 'None'}")

                if tenant_obj:
                    # Get pages for the tenant
                    try:
                        logger.info(f"Listing pages for tenant {tenant_obj.id}")
                        pages = page_manager.list_by_tenant(str(tenant_obj.id), include_unpublished=True)
                        logger.info(f"Found {len(pages)} pages for tenant {tenant_obj.id}")
                        for p in pages:
                            logger.info(f"  Page: {p.title} (ID: {p.id}, slug: {p.slug})")
                    except Exception as e:
                        logger.error(f"Error listing pages for tenant {tenant_obj.id}: {str(e)}")
                        status_message = f"Error loading pages: {str(e)}"
                        status_type = "error"
                else:
                    logger.warning(f"No tenant found with slug: {selected_tenant_slug}")
            except Exception as e:
                logger.error(f"Error getting tenant by slug '{selected_tenant_slug}': {str(e)}")
                status_message = f"Error loading tenant: {str(e)}"
                status_type = "error"
        else:
            logger.warning("No tenant selected for page listing")

    # Check if the template file exists
    import os
    template_path = os.path.join("templates", "admin", "pages", "list.html")
    if not os.path.exists(template_path):
        logger.error(f"Template file not found: {template_path}")
        return JSONResponse({"error": f"Template file not found: {template_path}"}, status_code=500)
    else:
        logger.info(f"Template file exists: {template_path}")

    # Return template response
    logger.info("Rendering template: admin/pages/list.html")
    try:
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
    finally:
        session.close()

@router.get("/pages/create", response_class=HTMLResponse)
async def page_create_form(
    request: Request,
    tenant: Optional[str] = None,
    template_id: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin form to create a new page."""
    managers = get_managers()
    session = managers["session"]
    
    try:
        # Get local manager instances with a session
        tenant_manager = managers["tenant_manager"]
        template_manager = managers["template_manager"]
        
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
    finally:
        session.close()

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
    session = SessionLocal()
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
        session.rollback()
        logger.error(f"Error creating page: {str(e)}")
        return RedirectResponse(
            url=f"/admin/pages/create?tenant={tenant.slug if 'tenant' in locals() and tenant else ''}&status_message=Error+creating+page:+{str(e)}&status_type=danger",
            status_code=status.HTTP_303_SEE_OTHER
        )
    finally:
        session.close()

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

@router.post("/api/pages", response_class=JSONResponse)
async def api_create_page(page_data: Dict[str, Any] = Body(...)):
    """Create a new page via API."""
    session = SessionLocal()
    try:
        page_manager = PageManager(session)
        page = page_manager.create(page_data)
        return {"id": str(page.id)}
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating page via API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating page: {str(e)}")
    finally:
        session.close()

@router.put("/api/pages/{page_id}", response_class=JSONResponse)
async def api_update_page(page_id: str, page_data: Dict[str, Any] = Body(...)):
    """Update a page via API."""
    session = SessionLocal()
    try:
        page_manager = PageManager(session)
        page = page_manager.update(page_id, page_data)
        if not page:
            raise HTTPException(status_code=404, detail=f"Page with ID {page_id} not found")
        return {"id": str(page.id)}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating page via API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating page: {str(e)}")
    finally:
        session.close()

@router.delete("/api/pages/{page_id}", response_class=JSONResponse)
async def api_delete_page(page_id: str):
    """Delete a page via API."""
    session = SessionLocal()
    try:
        page_manager = PageManager(session)
        success = page_manager.delete(page_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Page with ID {page_id} not found")
        return {"success": True, "message": "Page deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting page via API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting page: {str(e)}")
    finally:
        session.close()


@router.post("/pages/create", response_class=RedirectResponse)
async def admin_create_page(
    request: Request,
    tenant_id: str = Form(...),
    title: str = Form(...),
    slug: str = Form(...),
    meta_title: str = Form(None),
    meta_description: str = Form(None),
    is_published: bool = Form(False),
    template_id: str = Form(None)
):
    """Create a new page."""
    session = SessionLocal()
    try:
        page_manager = PageManager(session)
        template_manager = PageTemplateManager(session)

        # Get the selected template or the first available
        if template_id:
            template = template_manager.get(template_id)
        else:
            templates = template_manager.list()
            template = templates[0] if templates else None

        if not template:
            error = "No page template available. Please create a template first."
            return RedirectResponse(
                url=f"/admin/pages?tenant={tenant_id}&error={error}",
                status_code=303
            )

        # Create basic page structure from template
        page_data = {
            "tenant_id": tenant_id,
            "title": title,
            "slug": slug,
            "meta_title": meta_title,
            "meta_description": meta_description,
            "is_published": is_published == 'on' or is_published is True,
            "layout_data": {
                "template_id": str(template.id),
                "sections": []
            }
        }

        # Add sections from template
        if template.template_data and "sections" in template.template_data:
            for section_template in template.template_data["sections"]:
                page_data["layout_data"]["sections"].append({
                    "type": section_template["section_type"],
                    "settings": section_template["settings"],
                    "blocks": []
                })

        # Create the page directly with SQLAlchemy instead of using the manager
        new_page = Page(
            tenant_id=tenant_id,
            title=title,
            slug=slug,
            meta_title=meta_title,
            meta_description=meta_description,
            is_published=page_data["is_published"],
            layout_data=page_data["layout_data"]
        )

        session.add(new_page)
        session.commit()

        # Get the ID after commit
        page_id = new_page.id

        return RedirectResponse(
            url=f"/admin/pages/editor?id={page_id}&tenant={tenant_id}",
            status_code=303
        )
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating page: {str(e)}")
        return RedirectResponse(
            url=f"/admin/pages?tenant={tenant_id}&error=Error creating page: {str(e)}",
            status_code=303
        )
    finally:
        session.close()