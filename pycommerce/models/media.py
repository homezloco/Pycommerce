"""
Media management models for PyCommerce.

This module defines models for managing media files (images, videos, etc.)
in the PyCommerce platform.
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from pycommerce.core.db import Base, db_session
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship


class Media(Base):
    """Media model for storing information about uploaded files."""
    
    __tablename__ = "media"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True)
    name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_url = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False)  # image, video, document, etc.
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    width = Column(Integer, nullable=True)  # For images and videos
    height = Column(Integer, nullable=True)  # For images and videos
    alt_text = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    meta_data = Column(JSONB, nullable=True)  # For storing extra information
    is_ai_generated = Column(Boolean, default=False)
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="media_files")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the media object to a dictionary."""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "name": self.name,
            "file_path": self.file_path,
            "file_url": self.file_url,
            "file_type": self.file_type,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "width": self.width,
            "height": self.height,
            "alt_text": self.alt_text,
            "description": self.description,
            "meta_data": self.meta_data,
            "is_ai_generated": self.is_ai_generated,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


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
                
            if is_ai_generated is not None:
                query = query.filter(Media.is_ai_generated == is_ai_generated)
                
            if search_term:
                search_pattern = f"%{search_term}%"
                query = query.filter(
                    (Media.name.ilike(search_pattern)) | 
                    (Media.description.ilike(search_pattern))
                )
            
            # Order by most recent first
            query = query.order_by(Media.created_at.desc())
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            return query.all()
        except Exception as e:
            raise e