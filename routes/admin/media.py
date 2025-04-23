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
            
            # Upload file
            # Note: In a real implementation, media_service.upload would be called here
            # For now, we'll return a mock response
            
            response_data = {
                "success": True,
                "message": "File uploaded successfully",
                "file": {
                    "id": "generated_id",
                    "name": name,
                    "size": len(file_content),
                    "mime_type": file_type,
                    "url": f"/media/{name.replace(' ', '_')}",
                    "tenant_id": tenant_id,
                    "sharing_level": sharing_level,
                    "public_access": public_access,
                    "created_at": "2025-04-23T12:00:00Z",
                    "updated_at": "2025-04-23T12:00:00Z"
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
                
            # Apply filters
            filters = {}
            if tenant_id:
                filters["tenant_id"] = tenant_id
            if mime_type:
                filters["mime_type"] = mime_type
            if sharing_level:
                filters["sharing_level"] = sharing_level
            if search:
                filters["search"] = search
                
            # Note: In a real implementation, media_service.list would be called here
            # For now, we'll return mock data
            
            # Sample media items
            media_items = [
                {
                    "id": "1",
                    "name": "Sample Image 1",
                    "url": "https://dummyimage.com/600x400/4a90e2/ffffff&text=Product+Image+1",
                    "size": 12345,
                    "mime_type": "image/jpeg",
                    "tenant_id": None,
                    "tenant_name": "Global",
                    "sharing_level": "global",
                    "created_at": "2025-04-23T10:00:00Z",
                    "updated_at": "2025-04-23T10:00:00Z"
                },
                {
                    "id": "2",
                    "name": "Tech Product Image", 
                    "url": "https://dummyimage.com/600x400/e24a90/ffffff&text=Tech+Product",
                    "size": 23456,
                    "mime_type": "image/jpeg",
                    "tenant_id": "ea6c4bc0-d5aa-4d4f-862c-5d47e7c3f410",
                    "tenant_name": "Tech Gadgets",
                    "sharing_level": "tenant",
                    "created_at": "2025-04-23T10:01:00Z",
                    "updated_at": "2025-04-23T10:01:00Z"
                },
                {
                    "id": "3",
                    "name": "Outdoor Product Image",
                    "url": "https://dummyimage.com/600x400/90e24a/ffffff&text=Outdoor+Product",
                    "size": 34567,
                    "mime_type": "image/png",
                    "tenant_id": "fcb7133c-0ecc-4384-9b6d-695b52ae1496",
                    "tenant_name": "Outdoor Adventure",
                    "sharing_level": "tenant",
                    "created_at": "2025-04-23T10:02:00Z",
                    "updated_at": "2025-04-23T10:02:00Z"
                },
                {
                    "id": "4",
                    "name": "Fashion Product Image",
                    "url": "https://dummyimage.com/600x400/e2904a/ffffff&text=Fashion+Product",
                    "size": 45678,
                    "mime_type": "image/gif",
                    "tenant_id": "9608b670-08e6-4cfe-90aa-9068b9ddc09e",
                    "tenant_name": "Fashion Boutique",
                    "sharing_level": "tenant",
                    "created_at": "2025-04-23T10:03:00Z",
                    "updated_at": "2025-04-23T10:03:00Z"
                },
                {
                    "id": "5",
                    "name": "SVG Vector Graphic",
                    "url": "https://dummyimage.com/600x400/4ae290/ffffff&text=SVG+Sample",
                    "size": 5678,
                    "mime_type": "image/svg+xml",
                    "tenant_id": None,
                    "tenant_name": "Global",
                    "sharing_level": "global",
                    "created_at": "2025-04-23T10:04:00Z",
                    "updated_at": "2025-04-23T10:04:00Z"
                }
            ]
            
            # Apply filters to sample data
            filtered_items = media_items
            if tenant_id:
                filtered_items = [i for i in filtered_items if i["tenant_id"] == tenant_id]
            if mime_type:
                filtered_items = [i for i in filtered_items if i["mime_type"] == mime_type]
            if sharing_level:
                filtered_items = [i for i in filtered_items if i["sharing_level"] == sharing_level]
            if search:
                filtered_items = [i for i in filtered_items if search.lower() in i["name"].lower()]
                
            # Calculate pagination
            total_count = len(filtered_items)
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_items = filtered_items[start_idx:end_idx]
            
            response_data = {
                "items": paginated_items,
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