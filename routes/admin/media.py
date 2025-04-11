"""
Admin routes for media management.

This module contains all the routes for managing media files in the admin interface.
"""
import logging
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response

# Template setup will be passed from main app
templates = None

# Initialize logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])

# Initialize services
try:
    from pycommerce.models.tenant import TenantManager
    from pycommerce.services.media_service import MediaService
    
    # Initialize managers and services
    tenant_manager = TenantManager()
    media_service = MediaService()
except ImportError as e:
    logger.error(f"Error importing media modules: {str(e)}")
    tenant_manager = None
    media_service = None

@router.get("/media", response_class=HTMLResponse)
async def admin_media(
    request: Request,
    tenant: Optional[str] = None,
    file_type: Optional[str] = None,
    is_ai_generated: Optional[str] = None,
    sharing_level: Optional[str] = None,
    search: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for managing media files."""
    # Get tenant from query parameters or session
    selected_tenant_slug = tenant or request.session.get("selected_tenant")
    
    # If no tenant is selected, redirect to dashboard with message
    if not selected_tenant_slug:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Please+select+a+store+first&status_type=warning", 
            status_code=303
        )
    
    # Store the selected tenant in session for future requests
    request.session["selected_tenant"] = selected_tenant_slug
    
    # Get tenant object
    tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
    if not tenant_obj:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Store+not+found&status_type=error", 
            status_code=303
        )
        
    # Get all tenants for the dropdown menu
    tenants = tenant_manager.get_all()
    
    # Convert query parameters to filter criteria
    filter_criteria = {}
    
    if file_type:
        filter_criteria["file_type"] = file_type
    if is_ai_generated == "true":
        filter_criteria["is_ai_generated"] = True
    elif is_ai_generated == "false":
        filter_criteria["is_ai_generated"] = False
    if sharing_level:
        filter_criteria["sharing_level"] = sharing_level
    if search:
        filter_criteria["search"] = search
    
    # Get media files for tenant
    file_type = filter_criteria.get("file_type", None)
    is_ai_generated = filter_criteria.get("is_ai_generated", None)
    sharing_level_filter = filter_criteria.get("sharing_level", None)
    search_term = filter_criteria.get("search", None)
    
    # Convert string 'is_ai_generated' to boolean explicitly
    bool_is_ai_generated = None
    if isinstance(is_ai_generated, bool):
        bool_is_ai_generated = is_ai_generated
    
    # Get all media files that match the criteria
    if selected_tenant_slug.lower() == "all":
        # Fetch media for all tenants
        logger.info("Fetching media for all stores")
        try:
            # First try to get all tenants
            all_tenants = tenant_manager.list() or []
            
            # Then fetch media for each tenant and combine them
            all_media_files = []
            for tenant in all_tenants:
                try:
                    tenant_media = media_service.list_media(
                        tenant_id=str(tenant.id),
                        file_type=file_type,
                        is_ai_generated=bool_is_ai_generated,
                        search_term=search_term
                    )
                    all_media_files.extend(tenant_media)
                    logger.info(f"Found {len(tenant_media)} media files for tenant {tenant.name}")
                except Exception as e:
                    logger.error(f"Error fetching media for tenant {tenant.name}: {str(e)}")
            
            media_files = all_media_files
            logger.info(f"Found {len(media_files)} media files across all stores")
        except Exception as e:
            logger.error(f"Error fetching all media files: {str(e)}")
            media_files = []
    else:
        # Fetch media for specific tenant
        selected_tenant_id = str(tenant_obj.id) if tenant_obj else None
        media_files = media_service.list_media(
            tenant_id=selected_tenant_id,
            file_type=file_type,
            is_ai_generated=bool_is_ai_generated,
            search_term=search_term
        )
    
    # Filter by sharing level if specified (this must be done in Python since MediaService 
    # doesn't directly support filtering by sharing_level in the JSON metadata)
    if sharing_level_filter:
        filtered_media_files = []
        for media in media_files:
            # Check for sharing level in metadata
            media_sharing_level = None
            if hasattr(media, 'meta_data') and media.meta_data and 'sharing_level' in media.meta_data:
                media_sharing_level = media.meta_data.get('sharing_level')
            
            # For older files without sharing_level, infer from is_public
            elif hasattr(media, 'is_public'):
                media_sharing_level = "community" if media.is_public else "store"
            
            # If the sharing level matches the filter, include this media
            if media_sharing_level == sharing_level_filter:
                filtered_media_files.append(media)
        
        # Replace the unfiltered list with our filtered one
        media_files = filtered_media_files
    
    # Format media data for template
    media_data = []
    for media in media_files:
        media_item = {
            "id": str(media.id),
            "file_name": media.file_name,
            "file_type": media.file_type,
            "file_size": media.file_size,
            "alt_text": media.alt_text,
            "description": media.description,
            "is_ai_generated": media.is_ai_generated,
            "is_public": media.is_public if hasattr(media, 'is_public') else False,
            "url": media.url,
            "thumbnail_url": media.thumbnail_url or media.url,
            "created_at": media.created_at,
            "meta_data": media.meta_data if hasattr(media, 'meta_data') else {}
        }
        media_data.append(media_item)
    
    # Group media files by type for filtering
    file_types = set(media.file_type for media in media_files)
    
    # Check if we have an OpenAI API key for AI image generation
    has_openai_key = False
    try:
        import os
        has_openai_key = bool(os.environ.get("OPENAI_API_KEY"))
    except Exception as e:
        logger.warning(f"Error checking for OpenAI API key: {str(e)}")
    
    # Add simple pagination data (can be enhanced later)
    pagination = {
        "total": len(media_files),
        "limit": 12,  # Items per page
        "page": 1,    # Current page
        "pages": max(1, (len(media_files) + 11) // 12)  # Total pages (ceiling division)
    }
    
    return templates.TemplateResponse(
        "admin/media.html",
        {
            "request": request,
            "media_files": media_data,
            "selected_tenant": selected_tenant_slug,
            "tenant": tenant_obj,
            "tenant_id": str(tenant_obj.id),
            "tenants": tenants,  # Add the list of tenants for dropdown
            "file_types": file_types,
            "filters": {
                "file_type": file_type,
                "is_ai_generated": is_ai_generated,
                "sharing_level": sharing_level_filter,
                "search": search
            },
            "has_openai_key": has_openai_key,
            "status_message": status_message,
            "status_type": status_type,
            "cart_item_count": request.session.get("cart_item_count", 0),
            "pagination": pagination
        }
    )

@router.post("/media/upload", response_class=RedirectResponse)
async def admin_upload_media(
    request: Request,
    file: UploadFile = File(...),
    tenant_id: str = Form(...),
    sharing_level: str = Form("store"),
    alt_text: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """Upload a media file."""
    try:
        # Read file content
        file_content = await file.read()
        
        # Determine sharing settings based on sharing_level
        is_public = sharing_level == "community"
        
        # Create metadata with sharing info
        metadata = {
            "sharing_level": sharing_level,
            "upload_date": datetime.now().isoformat()
        }
        
        # Upload file
        result = await media_service.upload_file(
            file=file_content,
            filename=file.filename,
            tenant_id=tenant_id,
            alt_text=alt_text,
            description=description,
            metadata=metadata,
            is_public=is_public
        )
        
        if result:
            return RedirectResponse(
                url=f"/admin/media?tenant={tenant_id}&status_message=File+uploaded+successfully&status_type=success", 
                status_code=303
            )
        else:
            error_message = "Failed to upload file"
            return RedirectResponse(
                url=f"/admin/media?tenant={tenant_id}&status_message={error_message}&status_type=danger", 
                status_code=303
            )
    except Exception as e:
        logger.error(f"Error uploading media: {str(e)}")
        error_message = f"Error uploading media: {str(e)}"
        return RedirectResponse(
            url=f"/admin/media?tenant={tenant_id if tenant_id else ''}&status_message={error_message}&status_type=danger", 
            status_code=303
        )

@router.post("/media/generate-image", response_class=RedirectResponse)
async def admin_generate_image(
    request: Request,
    prompt: str = Form(...),
    tenant_id: str = Form(...),
    sharing_level: str = Form("store"),
    size: str = Form("1024x1024"),
    quality: str = Form("standard"),
    alt_text: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """Generate an image using DALL-E."""
    try:
        # Determine sharing settings based on sharing_level
        is_public = sharing_level == "community"
        
        # Create metadata with sharing info and add to existing metadata
        sharing_metadata = {
            "sharing_level": sharing_level,
            "generation_date": datetime.now().isoformat()
        }
        
        # Generate image
        result = await media_service.generate_image(
            tenant_id=tenant_id,
            prompt=prompt,
            size=size,
            quality=quality,
            alt_text=alt_text or prompt,
            description=description or f"AI-generated image from prompt: {prompt}",
            metadata=sharing_metadata,
            is_public=is_public
        )
        
        if result:
            return RedirectResponse(
                url=f"/admin/media?tenant={tenant_id}&status_message=Image+generated+successfully&status_type=success", 
                status_code=303
            )
        else:
            error_message = "Failed to generate image"
            return RedirectResponse(
                url=f"/admin/media?tenant={tenant_id}&status_message={error_message}&status_type=danger", 
                status_code=303
            )
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        error_message = f"Error generating image: {str(e)}"
        return RedirectResponse(
            url=f"/admin/media?tenant={tenant_id if tenant_id else ''}&status_message={error_message}&status_type=danger", 
            status_code=303
        )

@router.get("/media/download/{media_id}", response_class=Response)
async def admin_download_media(
    request: Request,
    media_id: str
):
    """Download a media file."""
    try:
        # Get the media file
        media_file, content = await media_service.get_media_content(media_id)
        
        if media_file and content:
            return Response(
                content=content,
                media_type=media_file.file_type,
                headers={
                    "Content-Disposition": f"attachment; filename={media_file.file_name}"
                }
            )
        else:
            return RedirectResponse(
                url=f"/admin/media?status_message=File+not+found&status_type=danger",
                status_code=303
            )
    except Exception as e:
        logger.error(f"Error downloading media: {str(e)}")
        error_message = f"Error downloading media: {str(e)}"
        return RedirectResponse(
            url=f"/admin/media?status_message={error_message}&status_type=danger",
            status_code=303
        )

@router.delete("/media/delete/{media_id}", response_class=JSONResponse)
async def admin_delete_media_via_api(
    request: Request,
    media_id: str,
    tenant_id: str = Form(...)
):
    """Delete a media file via API (DELETE request)."""
    try:
        # Delete the media file
        result = await media_service.delete_media(media_id)
        
        if result:
            return JSONResponse(
                content={"success": True, "message": "Media deleted successfully"},
                status_code=200
            )
        else:
            return JSONResponse(
                content={"success": False, "message": "Failed to delete media"},
                status_code=400
            )
    except Exception as e:
        logger.error(f"Error deleting media: {str(e)}")
        return JSONResponse(
            content={"success": False, "message": f"Error deleting media: {str(e)}"},
            status_code=500
        )

@router.get("/media/delete/{media_id}", response_class=RedirectResponse)
async def admin_delete_media(
    request: Request,
    media_id: str
):
    """Delete a media file via browser link (GET request)."""
    try:
        # Get tenant ID from session or query params if available
        selected_tenant_slug = None
        tenant_id = None
        
        if "selected_tenant" in request.session:
            selected_tenant_slug = request.session.get("selected_tenant")
        
        if selected_tenant_slug:
            try:
                selected_tenant = tenant_manager.get_by_slug(selected_tenant_slug)
                if selected_tenant and hasattr(selected_tenant, 'id'):
                    tenant_id = str(selected_tenant.id)
            except Exception as e:
                logger.warning(f"Could not get tenant with slug '{selected_tenant_slug}': {str(e)}")
        
        # Use the media service to delete the media
        result = await media_service.delete_media(media_id)
        if result:
            return RedirectResponse(
                url=f"/admin/media?tenant={tenant_id if tenant_id else ''}&status_message=Media+deleted+successfully&status_type=success", 
                status_code=303
            )
        else:
            error_message = "Deletion failed. Please try again."
            return RedirectResponse(
                url=f"/admin/media?tenant={tenant_id if tenant_id else ''}&status_message={error_message}&status_type=danger", 
                status_code=303
            )
    except Exception as e:
        logger.error(f"Error deleting media: {str(e)}")
        error_message = f"Error deleting media: {str(e)}"
        return RedirectResponse(
            url=f"/admin/media?status_message={error_message}&status_type=danger",
            status_code=303
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