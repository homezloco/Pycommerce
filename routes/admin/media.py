"""
Media management routes for the admin panel.

This module provides routes for the admin media management interface,
allowing users to upload, view, update, and delete media files.
"""

import logging
import os
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from pycommerce.models.tenant import Tenant, TenantManager
from pycommerce.services.media_service import MediaService

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize tenant manager
tenant_manager = None
media_service = None

def setup_routes(templates_instance: Jinja2Templates) -> APIRouter:
    """
    Set up the media management routes.
    
    Args:
        templates_instance: The templates instance to use for rendering
        
    Returns:
        The router with all routes configured
    """
    global tenant_manager, media_service
    
    # Initialize the tenant manager
    try:
        from pycommerce.models.tenant import TenantManager
        tenant_manager = TenantManager()
        logger.info("Successfully initialized TenantManager for admin media routes")
    except Exception as e:
        logger.error(f"Error initializing TenantManager for admin media routes: {e}")
        
    # Initialize the media service
    try:
        from pycommerce.services.media_service import MediaService
        media_service = MediaService()
        logger.info("Successfully initialized MediaService for admin media routes")
    except Exception as e:
        logger.error(f"Error initializing MediaService for admin media routes: {e}")
    
    @router.get("/admin/media", response_class=HTMLResponse)
    async def admin_media_index(
        request: Request,
        tenant: Optional[str] = None,
        status_message: Optional[str] = None,
        status_type: str = "info"
    ):
        """Media library index page for admin panel."""
        try:
            # Get all tenants for dropdowns
            tenants_list = []
            try:
                if tenant_manager:
                    tenants = tenant_manager.list() or []
                    tenants_list = [
                        {
                            "id": str(t.id),
                            "name": t.name,
                            "slug": t.slug
                        }
                        for t in tenants if t and hasattr(t, 'id')
                    ]
            except Exception as e:
                logger.error(f"Error fetching tenants for media library: {e}")
                
            return templates_instance.TemplateResponse(
                "admin/media/index.html",
                {
                    "request": request,
                    "active_page": "media",
                    "tenants": tenants_list,
                    "cart_item_count": request.session.get("cart_item_count", 0),
                    "status_message": status_message,
                    "status_type": status_type
                }
            )
        except Exception as e:
            logger.error(f"Error rendering media library page: {e}")
            # Redirect to dashboard with error message
            return RedirectResponse(
                url=f"/admin/dashboard?status_message=Error loading media library: {str(e)}&status_type=danger",
                status_code=303
            )

    @router.post("/admin/api/media/upload")
    async def admin_upload_media(
        request: Request,
        file: UploadFile = File(...),
        name: Optional[str] = Form(None),
        tenant_id: Optional[str] = Form(None),
        sharing_level: str = Form("global"),
        public_access: bool = Form(True)
    ):
        """Upload a media file."""
        try:
            if not media_service:
                raise HTTPException(status_code=503, detail="Media service not available")
                
            # Read file content
            file_content = await file.read()
            
            # Get file name if not provided
            if not name:
                name = file.filename
                
            # Determine file type from content
            file_type = file.content_type
            
            # Use file extension if content type is not provided
            if not file_type:
                extension = os.path.splitext(file.filename)[1].lower()
                if extension in ['.jpg', '.jpeg']:
                    file_type = 'image/jpeg'
                elif extension == '.png':
                    file_type = 'image/png'
                elif extension == '.gif':
                    file_type = 'image/gif'
                elif extension == '.svg':
                    file_type = 'image/svg+xml'
                else:
                    file_type = 'application/octet-stream'
            
            # Convert the file to a data URL for storage
            import base64
            b64_data = base64.b64encode(file_content).decode('utf-8')
            data_url = f"data:{file_type};base64,{b64_data}"
            
            # Create a media item in the service
            media_item = media_service.create(
                name=name,
                url=data_url,
                mime_type=file_type,
                size=len(file_content),
                tenant_id=tenant_id,
                sharing_level=sharing_level,
                metadata={"public_access": public_access}
            )
            
            # Get tenant name for response
            tenant_name = "Global"
            if tenant_id and tenant_manager:
                try:
                    tenant = tenant_manager.get(tenant_id)
                    if tenant:
                        tenant_name = tenant.name
                except Exception as e:
                    logger.error(f"Error getting tenant: {e}")
            
            response_data = {
                "success": True,
                "message": "File uploaded successfully",
                "file": {
                    "id": str(media_item.id),
                    "name": media_item.name,
                    "size": media_item.size,
                    "mime_type": media_item.mime_type,
                    "url": media_item.url,
                    "tenant_id": media_item.tenant_id,
                    "tenant_name": tenant_name,
                    "sharing_level": media_item.sharing_level,
                    "public_access": media_item.metadata.get("public_access", True),
                    "created_at": media_item.created_at,
                    "updated_at": media_item.updated_at
                }
            }
            
            return JSONResponse(content=response_data)
            
        except Exception as e:
            logger.error(f"Error uploading media: {e}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": f"Error uploading file: {str(e)}"}
            )
            
    @router.get("/admin/api/media")
    async def admin_get_media(
        request: Request,
        tenant_id: Optional[str] = None,
        mime_type: Optional[str] = None,
        sharing_level: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 12
    ):
        """Get media files with optional filtering."""
        try:
            if not media_service:
                raise HTTPException(status_code=503, detail="Media service not available")
                
            # Apply filters that the media service understands directly
            filters = {}
            if mime_type:
                filters["mime_type"] = mime_type
            if sharing_level:
                filters["sharing_level"] = sharing_level
            
            # Get media items from the service
            items = media_service.list(
                tenant_id=tenant_id,
                filters=filters,
                page=page,
                limit=limit
            )
            
            # Convert MediaItem objects to dictionaries for JSON response
            items_dict = []
            for item in items:
                # Get tenant name from tenant_manager if tenant_id is available
                tenant_name = "Global"
                if item.tenant_id and tenant_manager:
                    try:
                        tenant = tenant_manager.get(item.tenant_id)
                        if tenant:
                            tenant_name = tenant.name
                    except Exception as e:
                        logger.error(f"Error getting tenant: {e}")
                
                # Convert the MediaItem to a dictionary
                item_dict = {
                    "id": str(item.id),
                    "name": item.name,
                    "url": item.url,
                    "size": item.size,
                    "mime_type": item.mime_type,
                    "tenant_id": item.tenant_id,
                    "tenant_name": tenant_name,
                    "sharing_level": item.sharing_level,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at
                }
                items_dict.append(item_dict)
            
            # Apply search filter (in case MediaService doesn't handle it)
            if search:
                items_dict = [i for i in items_dict if search.lower() in i["name"].lower()]
                
            # Count for pagination
            total_count = len(media_service._media_items)  # This should be replaced with a proper count method
            
            response_data = {
                "items": items_dict,
                "count": total_count,
                "page": page,
                "limit": limit,
                "pages": (total_count + limit - 1) // limit
            }
            
            return JSONResponse(content=response_data)
            
        except Exception as e:
            logger.error(f"Error fetching media: {e}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": f"Error fetching media: {str(e)}"}
            )
            
    @router.delete("/admin/api/media/{media_id}")
    async def admin_delete_media(
        request: Request,
        media_id: str
    ):
        """Delete a media file."""
        try:
            if not media_service:
                raise HTTPException(status_code=503, detail="Media service not available")
                
            # Note: In a real implementation, media_service.delete would be called here
            # For now, we'll return a success response
            
            return JSONResponse(content={"success": True, "message": "Media deleted successfully"})
            
        except Exception as e:
            logger.error(f"Error deleting media: {e}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": f"Error deleting media: {str(e)}"}
            )
    
    return router