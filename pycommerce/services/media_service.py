"""
Media service for PyCommerce.

This module provides a service for managing media files in the PyCommerce platform.
"""
import logging
import os
import uuid
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class MediaItem:
    """Media item class."""
    def __init__(
        self,
        id: str,
        name: str,
        url: str,
        mime_type: Optional[str] = None,
        size: Optional[int] = None,
        tenant_id: Optional[str] = None,
        sharing_level: Optional[str] = "tenant",
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize a media item."""
        self.id = id
        self.name = name
        self.url = url
        self.mime_type = mime_type
        self.size = size
        self.tenant_id = tenant_id
        self.sharing_level = sharing_level
        self.created_at = created_at
        self.updated_at = updated_at
        self.metadata = metadata or {}


class MediaService:
    """Media service for PyCommerce."""
    
    def __init__(self):
        """Initialize the media service."""
        logger.info("Initializing MediaService")
        self._media_items = []
        
        # Add some sample media items
        self._add_sample_media()
    
    def _add_sample_media(self):
        """Add sample media items for testing."""
        sample_items = [
            {
                "id": str(uuid.uuid4()),
                "name": "Product Image (Blue)",
                "url": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2MDAiIGhlaWdodD0iNDAwIiB2aWV3Qm94PSIwIDAgNjAwIDQwMCI+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0iIzRhOTBlMiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMzYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IiNmZmZmZmYiPlByb2R1Y3QgSW1hZ2U8L3RleHQ+PC9zdmc+",
                "mime_type": "image/svg+xml",
                "size": 12345,
                "tenant_id": None,  # Global
                "sharing_level": "global"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Tech Product Image",
                "url": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2MDAiIGhlaWdodD0iNDAwIiB2aWV3Qm94PSIwIDAgNjAwIDQwMCI+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0iI2UyNGE5MCIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMzYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IiNmZmZmZmYiPlRlY2ggUHJvZHVjdDwvdGV4dD48L3N2Zz4=",
                "mime_type": "image/svg+xml",
                "size": 23456,
                "tenant_id": "tech",  # Tech tenant
                "sharing_level": "tenant"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Outdoor Product Image",
                "url": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2MDAiIGhlaWdodD0iNDAwIiB2aWV3Qm94PSIwIDAgNjAwIDQwMCI+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0iIzkwZTI0YSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMzYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IiNmZmZmZmYiPk91dGRvb3IgUHJvZHVjdDwvdGV4dD48L3N2Zz4=",
                "mime_type": "image/svg+xml",
                "size": 34567,
                "tenant_id": "outdoor",  # Outdoor tenant
                "sharing_level": "tenant"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Fashion Product Image",
                "url": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2MDAiIGhlaWdodD0iNDAwIiB2aWV3Qm94PSIwIDAgNjAwIDQwMCI+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0iI2UyOTA0YSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMzYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IiNmZmZmZmYiPkZhc2hpb24gUHJvZHVjdDwvdGV4dD48L3N2Zz4=",
                "mime_type": "image/svg+xml",
                "size": 45678,
                "tenant_id": "fashion",  # Fashion tenant
                "sharing_level": "tenant"
            }
        ]
        
        for item in sample_items:
            self._media_items.append(MediaItem(**item))
    
    def list(
        self,
        tenant_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        limit: int = 100
    ) -> List[MediaItem]:
        """
        List media items.
        
        Args:
            tenant_id: Optional tenant ID to filter by
            filters: Optional filters to apply
            page: Page number (default: 1)
            limit: Items per page (default: 100)
            
        Returns:
            List of media items
        """
        filters = filters or {}
        filtered_items = []
        
        for item in self._media_items:
            # Include global items for everyone
            is_global = item.sharing_level == "global"
            
            # Include tenant-specific items if tenant_id matches
            is_tenant_match = tenant_id and item.tenant_id == tenant_id
            
            if is_global or is_tenant_match:
                match = True
                
                # Apply additional filters
                for k, v in filters.items():
                    if hasattr(item, k) and getattr(item, k) != v:
                        match = False
                        break
                
                if match:
                    filtered_items.append(item)
        
        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        return filtered_items[start_idx:end_idx]
    
    def get(self, id: str) -> Optional[MediaItem]:
        """
        Get a media item by ID.
        
        Args:
            id: The ID of the media item
            
        Returns:
            The media item or None if not found
        """
        for item in self._media_items:
            if str(item.id) == id:
                return item
        
        return None
    
    def create(
        self,
        name: str,
        url: str,
        mime_type: Optional[str] = None,
        size: Optional[int] = None,
        tenant_id: Optional[str] = None,
        sharing_level: Optional[str] = "tenant",
        metadata: Optional[Dict[str, Any]] = None
    ) -> MediaItem:
        """
        Create a new media item.
        
        Args:
            name: The name of the media item
            url: The URL of the media item
            mime_type: The MIME type of the media item
            size: The size of the media item in bytes
            tenant_id: The ID of the tenant the media item belongs to
            sharing_level: The sharing level of the media item
            metadata: Additional metadata for the media item
            
        Returns:
            The created media item
        """
        item = MediaItem(
            id=str(uuid.uuid4()),
            name=name,
            url=url,
            mime_type=mime_type,
            size=size,
            tenant_id=tenant_id,
            sharing_level=sharing_level,
            metadata=metadata
        )
        
        self._media_items.append(item)
        
        return item
    
    def update(
        self,
        id: str,
        name: Optional[str] = None,
        url: Optional[str] = None,
        mime_type: Optional[str] = None,
        size: Optional[int] = None,
        tenant_id: Optional[str] = None,
        sharing_level: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[MediaItem]:
        """
        Update a media item.
        
        Args:
            id: The ID of the media item to update
            name: The new name of the media item
            url: The new URL of the media item
            mime_type: The new MIME type of the media item
            size: The new size of the media item in bytes
            tenant_id: The new tenant ID of the media item
            sharing_level: The new sharing level of the media item
            metadata: The new metadata for the media item
            
        Returns:
            The updated media item or None if not found
        """
        item = self.get(id)
        
        if not item:
            return None
        
        if name is not None:
            item.name = name
        
        if url is not None:
            item.url = url
        
        if mime_type is not None:
            item.mime_type = mime_type
        
        if size is not None:
            item.size = size
        
        if tenant_id is not None:
            item.tenant_id = tenant_id
        
        if sharing_level is not None:
            item.sharing_level = sharing_level
        
        if metadata is not None:
            item.metadata = metadata
        
        return item
    
    def delete(self, id: str) -> bool:
        """
        Delete a media item.
        
        Args:
            id: The ID of the media item to delete
            
        Returns:
            True if the item was deleted, False otherwise
        """
        for i, item in enumerate(self._media_items):
            if str(item.id) == id:
                del self._media_items[i]
                return True
        
        return False