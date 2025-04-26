"""
Media API for PyCommerce.

This module provides API endpoints for managing media files.
"""
import logging
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from pycommerce.services.media_service import MediaService, MediaItem as ServiceMediaItem

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize media service
media_service = MediaService()

class MediaItem(BaseModel):
    """Media item model."""
    id: str
    name: str
    url: str
    size: Optional[int] = None
    mime_type: Optional[str] = None
    tenant_id: Optional[str] = None
    sharing_level: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class MediaListResponse(BaseModel):
    """Response model for media list."""
    items: List[MediaItem]
    count: int
    page: int = 1
    limit: int = 100

@router.get("/api/media", 
         response_model=MediaListResponse, 
         summary="List Media Items",
         description="Retrieve a paginated list of media items with optional filtering",
         responses={
             200: {"description": "Media items retrieved successfully", "model": MediaListResponse},
             400: {"description": "Invalid request parameters"},
             401: {"description": "Unauthorized - requires proper authentication"},
             403: {"description": "Forbidden - insufficient permissions to access media"},
             500: {"description": "Internal server error"}
         })
async def get_media_list(
    request: Request,
    tenant_id: Optional[str] = Query(None, description="Filter media items by tenant UUID"),
    sharing_level: Optional[str] = Query(None, description="Filter by sharing level (private, tenant, public)"),
    page: int = Query(1, ge=1, description="Page number for pagination (starts at 1)"),
    limit: int = Query(100, ge=1, le=500, description="Number of items per page (max 500)")
):
    """
    Retrieve a paginated list of media items with optional filtering.
    
    This endpoint returns a list of media assets available in the system, with
    pagination support and filtering options. Media items can include images, documents,
    videos, and other file types used throughout the e-commerce platform.
    
    The available filters are:
    - **tenant_id**: Limit results to media belonging to a specific tenant
    - **sharing_level**: Filter by visibility level (private, tenant, public)
    
    Pagination parameters:
    - **page**: Page number (starting from 1)
    - **limit**: Number of items per page (1-500, default 100)
    
    Results are sorted by creation date (newest first). Each media item includes
    metadata such as size, mime type, and URLs for direct access. The response
    includes pagination information and the total count of matching items.
    
    Media with "public" sharing level are accessible to all users, while tenant-specific
    media requires appropriate permissions. System administrators can access all media
    regardless of sharing level.
    """
    filters = {}
    if sharing_level:
        filters["sharing_level"] = sharing_level
    
    # Get media items
    items = media_service.list(tenant_id=tenant_id, filters=filters, page=page, limit=limit)
    
    # Convert to API model
    media_items = []
    for item in items:
        media_items.append(MediaItem(
            id=item.id,
            name=item.name,
            url=item.url,
            size=item.size,
            mime_type=item.mime_type,
            tenant_id=item.tenant_id,
            sharing_level=item.sharing_level,
            created_at=item.created_at,
            updated_at=item.updated_at
        ))
    
    return MediaListResponse(
        items=media_items,
        count=len(media_items),
        page=page,
        limit=limit
    )

@router.get("/api/media/{id}", 
         response_model=MediaItem,
         summary="Get Media Item by ID",
         description="Retrieve detailed information about a specific media item",
         responses={
             200: {"description": "Media item retrieved successfully", "model": MediaItem},
             400: {"description": "Invalid media ID format"},
             401: {"description": "Unauthorized - requires proper authentication"},
             403: {"description": "Forbidden - insufficient permissions to access this media item"},
             404: {"description": "Media item not found"},
             500: {"description": "Internal server error"}
         })
async def get_media_item(
    request: Request, 
    id: str
):
    """
    Retrieve detailed information about a specific media item.
    
    This endpoint returns comprehensive details about a single media item, including
    its metadata and access URL. Media items are assets such as images, documents,
    videos, and other files used throughout the e-commerce platform.
    
    - **id**: The unique identifier of the media item to retrieve
    
    The response includes:
    - Full metadata (name, size, MIME type, creation date)
    - Direct URL for accessing the media content
    - Tenant ownership information
    - Sharing level indicating access permissions
    
    Access to media items is controlled by their sharing level:
    - Public media can be accessed by anyone
    - Tenant-specific media requires tenant-level access permissions
    - Private media is restricted to specific users with appropriate permissions
    
    If the requested media item doesn't exist or the user lacks permission to access it,
    an appropriate error response is returned.
    """
    item = media_service.get(id)
    
    if not item:
        return JSONResponse(
            status_code=404,
            content={"error": f"Media item with ID {id} not found"}
        )
    
    return MediaItem(
        id=item.id,
        name=item.name,
        url=item.url,
        size=item.size,
        mime_type=item.mime_type,
        tenant_id=item.tenant_id,
        sharing_level=item.sharing_level,
        created_at=item.created_at,
        updated_at=item.updated_at
    )

def setup_routes(app=None):
    """Set up routes."""
    if app:
        app.include_router(router)
    
    return router