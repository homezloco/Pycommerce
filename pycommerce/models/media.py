"""
Media management models for PyCommerce.

This module uses the MediaFile model from the central registry to avoid
duplicate model definitions and circular imports.
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from pycommerce.core.db import db_session
from pycommerce.models.db_registry import MediaFile as Media  # Alias as Media for compatibility

# Import needed SQLAlchemy components for the manager
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB


# Add to_dict method to the Media model
def to_dict_method(self) -> Dict[str, Any]:
    """Convert the media object to a dictionary."""
    return {
        "id": str(self.id),
        "tenant_id": str(self.tenant_id) if self.tenant_id else None,
        "name": self.filename if hasattr(self, 'filename') else getattr(self, 'name', 'Unknown'),
        "file_path": self.file_path,
        "file_type": self.file_type,
        "file_size": self.file_size,
        "description": self.description,
        "created_at": self.created_at.isoformat() if self.created_at else None,
        "updated_at": self.updated_at.isoformat() if self.updated_at else None
    }

# Add the method to the Media class
Media.to_dict = to_dict_method


class MediaManager:
    """Manager for media operations."""
    
    def __init__(self):
        """Initialize the media manager."""
        self.session = db_session
    
    def create(self, data: Dict[str, Any]) -> Media:
        """
        Create a new media record.
        
        Args:
            data: Media data including file path, type, etc.
            
        Returns:
            The created media object
        """
        try:
            media = Media(**data)
            self.session.add(media)
            self.session.commit()
            return media
        except Exception as e:
            self.session.rollback()
            raise e
    
    def get(self, media_id: Union[str, uuid.UUID]) -> Optional[Media]:
        """
        Get a media by ID.
        
        Args:
            media_id: The ID of the media to retrieve
            
        Returns:
            The media object if found, None otherwise
        """
        try:
            # Convert string ID to UUID if necessary
            if isinstance(media_id, str):
                media_id = uuid.UUID(media_id)
                
            return self.session.query(Media).filter(Media.id == media_id).first()
        except Exception as e:
            raise e
    
    def update(self, media_id: Union[str, uuid.UUID], **kwargs) -> Optional[Media]:
        """
        Update an existing media record.
        
        Args:
            media_id: The ID of the media to update
            **kwargs: The fields to update
            
        Returns:
            The updated media object if found, None otherwise
        """
        try:
            # Convert string ID to UUID if necessary
            if isinstance(media_id, str):
                media_id = uuid.UUID(media_id)
                
            media = self.session.query(Media).filter(Media.id == media_id).first()
            if not media:
                return None
                
            for key, value in kwargs.items():
                if hasattr(media, key):
                    setattr(media, key, value)
            
            media.updated_at = datetime.utcnow()
            self.session.commit()
            return media
        except Exception as e:
            self.session.rollback()
            raise e
    
    def delete(self, media_id: Union[str, uuid.UUID]) -> bool:
        """
        Delete a media by ID.
        
        Args:
            media_id: The ID of the media to delete
            
        Returns:
            True if the media was deleted, False otherwise
        """
        try:
            # Convert string ID to UUID if necessary
            if isinstance(media_id, str):
                media_id = uuid.UUID(media_id)
                
            media = self.session.query(Media).filter(Media.id == media_id).first()
            if not media:
                return False
                
            # Delete the file from storage
            if os.path.exists(media.file_path):
                os.remove(media.file_path)
                
            self.session.delete(media)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise e
    
    def list(
        self, 
        tenant_id: Optional[Union[str, uuid.UUID]] = None,
        file_type: Optional[str] = None,
        is_ai_generated: Optional[bool] = None,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Media]:
        """
        List media with optional filtering.
        
        Args:
            tenant_id: Filter by tenant ID
            file_type: Filter by file type (image, video, etc.)
            is_ai_generated: Filter by AI generation status
            search_term: Search in name and description
            limit: Maximum number of items to return
            offset: Offset for pagination
            
        Returns:
            List of media objects matching the criteria
        """
        try:
            query = self.session.query(Media)
            
            # Apply filters
            if tenant_id:
                query = query.filter(Media.tenant_id == tenant_id)
                
            if file_type:
                query = query.filter(Media.file_type == file_type)
                
            # Skip is_ai_generated filter if it's not in the model
            if is_ai_generated is not None and hasattr(Media, 'is_ai_generated'):
                query = query.filter(Media.is_ai_generated == is_ai_generated)
                
            if search_term:
                search_pattern = f"%{search_term}%"
                # Search in filename instead of name if present
                if hasattr(Media, 'filename'):
                    query = query.filter(
                        (Media.filename.ilike(search_pattern)) | 
                        (Media.description.ilike(search_pattern))
                    )
                else:
                    # Fallback to original query
                    query = query.filter(
                        (Media.filename.ilike(search_pattern)) | 
                        (Media.description.ilike(search_pattern))
                    )
            
            # Order by most recent first
            query = query.order_by(Media.created_at.desc())
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            return query.all()
        except Exception as e:
            raise e