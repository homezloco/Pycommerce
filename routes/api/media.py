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

@router.get("/api/media", response_model=MediaListResponse)
async def get_media_list(
    request: Request,
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    sharing_level: Optional[str] = Query(None, description="Filter by sharing level"),
    page: int = Query(1, description="Page number"),
    limit: int = Query(100, description="Items per page")
):
    """
    Get a list of media items.
    
    Args:
        tenant_id: Optional tenant ID to filter by
        sharing_level: Optional sharing level to filter by
        page: Page number (default: 1)
        limit: Items per page (default: 100)
        
    Returns:
        List of media items
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

@router.get("/api/media/{id}")
async def get_media_item(request: Request, id: str):
    """
    Get a media item by ID.
    
    Args:
        id: The ID of the media item
        
    Returns:
        The media item
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