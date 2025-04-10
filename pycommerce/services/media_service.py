"""
Media service for PyCommerce.

This module provides utilities for managing media files including uploads and AI-generated images.
"""

import os
import uuid
import logging
import mimetypes
from typing import Optional, Dict, Any, List, Union, BinaryIO
from datetime import datetime
from pathlib import Path

import requests
from PIL import Image, ImageOps

from pycommerce.models.media import Media, MediaManager
from pycommerce.core.config import settings

# Configure logging
logger = logging.getLogger("pycommerce.services.media")

# Configure base directory for media uploads
MEDIA_DIR = "static/media"
GENERATED_MEDIA_DIR = f"{MEDIA_DIR}/generated"
UPLOADS_DIR = f"{MEDIA_DIR}/uploads"

# Ensure directories exist
os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(GENERATED_MEDIA_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)


class MediaService:
    """Service for handling media operations."""
    
    def __init__(self):
        """Initialize the media service."""
        self.media_manager = MediaManager()
        
    def has_openai_api_key(self) -> bool:
        """Check if the OpenAI API key is available in the environment.
        
        Returns:
            bool: True if the API key is available, False otherwise
        """
        try:
            api_key = os.environ.get("OPENAI_API_KEY")
            return bool(api_key)
        except Exception as e:
            logger.warning(f"Error checking for OpenAI API key: {str(e)}")
            return False
        
    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        tenant_id: Optional[str] = None,
        alt_text: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_public: bool = False
    ) -> Media:
        """
        Upload a file and create a media record.
        
        Args:
            file: The file object to upload
            filename: The original filename
            tenant_id: Optional tenant ID
            alt_text: Optional alt text for the file
            description: Optional description for the file
            metadata: Optional metadata for the file
            
        Returns:
            The created media object
        """
        try:
            # Generate a unique filename
            file_ext = os.path.splitext(filename)[1].lower()
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            
            # Determine file type based on extension
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = "application/octet-stream"
                
            file_type = mime_type.split('/')[0]  # image, video, audio, etc.
            
            # Create file path
            file_path = os.path.join(UPLOADS_DIR, unique_filename)
            
            # Save the file
            with open(file_path, "wb") as f:
                content = await file.read() if hasattr(file, "read") and callable(file.read) else file
                f.write(content)
                
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Get dimensions if it's an image
            width = None
            height = None
            if file_type == "image":
                try:
                    with Image.open(file_path) as img:
                        width, height = img.size
                except Exception as e:
                    logger.warning(f"Could not determine image dimensions: {str(e)}")
            
            # Create the media record
            media_data = {
                "tenant_id": uuid.UUID(tenant_id) if tenant_id else None,
                "name": os.path.splitext(filename)[0],
                "file_path": file_path,
                "file_url": f"/static/media/uploads/{unique_filename}",  # URL relative to the application root
                "file_type": file_type,
                "mime_type": mime_type,
                "file_size": file_size,
                "width": width,
                "height": height,
                "alt_text": alt_text,
                "description": description,
                "meta_data": metadata or {},
                "is_ai_generated": False,
                "is_public": is_public
            }
            
            media = self.media_manager.create(media_data)
            logger.info(f"Uploaded file: {filename} -> {file_path}")
            return media
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            raise
            
    async def generate_image_with_dalle(
        self,
        prompt: str,
        tenant_id: Optional[str] = None,
        size: str = "1024x1024",
        quality: str = "standard",
        alt_text: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_public: bool = False
    ) -> Optional[Media]:
        """
        Generate an image using OpenAI's DALL-E and create a media record.
        
        Args:
            prompt: The text prompt for image generation
            tenant_id: Optional tenant ID
            size: Image size (1024x1024, 1024x1792, 1792x1024)
            quality: Image quality (standard, hd)
            alt_text: Optional alt text for the image
            description: Optional description for the image
            metadata: Optional metadata for the image
            
        Returns:
            The created media object if successful, None otherwise
        """
        try:
            import openai
            
            # Check if the API key is available
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                logger.error("OpenAI API key not found. Set the OPENAI_API_KEY environment variable.")
                raise ValueError("OpenAI API key not found")
                
            client = openai.OpenAI(api_key=api_key)
            
            # Generate the image
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,
            )
            
            # Get the image URL
            image_url = response.data[0].url
            
            # Download the image
            image_response = requests.get(image_url, timeout=10)
            if image_response.status_code != 200:
                logger.error(f"Failed to download generated image: {image_response.status_code}")
                return None
                
            # Generate a unique filename
            unique_filename = f"{uuid.uuid4()}.png"
            file_path = os.path.join(GENERATED_MEDIA_DIR, unique_filename)
            
            # Save the image
            with open(file_path, "wb") as f:
                f.write(image_response.content)
                
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Get dimensions
            width = None
            height = None
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
            except Exception as e:
                logger.warning(f"Could not determine image dimensions: {str(e)}")
            
            # Create the media record
            media_data = {
                "tenant_id": uuid.UUID(tenant_id) if tenant_id else None,
                "name": f"DALL-E: {prompt[:50]}{'...' if len(prompt) > 50 else ''}",
                "file_path": file_path,
                "file_url": f"/static/media/generated/{unique_filename}",  # URL relative to the application root
                "file_type": "image",
                "mime_type": "image/png",
                "file_size": file_size,
                "width": width,
                "height": height,
                "alt_text": alt_text or prompt,
                "description": description or prompt,
                "meta_data": {
                    "prompt": prompt,
                    "model": "dall-e-3",
                    "size": size,
                    "quality": quality,
                    **(metadata or {})
                },
                "is_ai_generated": True,
                "is_public": is_public
            }
            
            media = self.media_manager.create(media_data)
            logger.info(f"Generated image with DALL-E: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
            return media
        except ImportError:
            logger.error("OpenAI package not installed. Install it with 'pip install openai'.")
            raise
        except Exception as e:
            logger.error(f"Error generating image with DALL-E: {str(e)}")
            raise
            
    def get_media(self, media_id: str) -> Optional[Media]:
        """
        Get a media by ID.
        
        Args:
            media_id: The ID of the media to retrieve
            
        Returns:
            The media object if found, None otherwise
        """
        return self.media_manager.get(media_id)
        
    def list_media(
        self,
        tenant_id: Optional[str] = None,
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
        return self.media_manager.list(
            tenant_id=tenant_id,
            file_type=file_type,
            is_ai_generated=is_ai_generated,
            search_term=search_term,
            limit=limit,
            offset=offset
        )
        
    async def delete_media(self, media_id: str) -> bool:
        """
        Delete a media by ID.
        
        Args:
            media_id: The ID of the media to delete
            
        Returns:
            True if the media was deleted, False otherwise
        """
        return self.media_manager.delete(media_id)
        
    def update_media(self, media_id: str, **kwargs) -> Optional[Media]:
        """
        Update a media by ID.
        
        Args:
            media_id: The ID of the media to update
            **kwargs: The fields to update
            
        Returns:
            The updated media object if found, None otherwise
        """
        return self.media_manager.update(media_id, **kwargs)
        
    async def get_media_content(self, media_id: str) -> tuple[Optional[Media], Optional[bytes]]:
        """
        Get a media's content by ID.
        
        Args:
            media_id: The ID of the media to retrieve
            
        Returns:
            Tuple of (Media object, file content as bytes) if found, (None, None) otherwise
        """
        try:
            media = self.media_manager.get(media_id)
            if not media or not os.path.exists(media.file_path):
                return None, None
                
            with open(media.file_path, "rb") as f:
                content = f.read()
                
            return media, content
        except Exception as e:
            logger.error(f"Error getting media content: {str(e)}")
            return None, None
            
    async def generate_image(self, **kwargs) -> Optional[Media]:
        """
        Generate an image using OpenAI's DALL-E and create a media record.
        This is a wrapper around generate_image_with_dalle.
        
        Args:
            **kwargs: Arguments to pass to generate_image_with_dalle
            
        Returns:
            The created media object if successful, None otherwise
        """
        try:
            return await self.generate_image_with_dalle(**kwargs)
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            return None
        
    def resize_image(self, media_id: str, width: int, height: int) -> Optional[Media]:
        """
        Resize an image and create a new media record.
        
        Args:
            media_id: The ID of the image to resize
            width: The new width
            height: The new height
            
        Returns:
            The created media object if successful, None otherwise
        """
        try:
            media = self.media_manager.get(media_id)
            if not media or media.file_type != "image":
                return None
                
            # Generate a unique filename
            file_ext = os.path.splitext(media.file_path)[1].lower()
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            
            # Create file path
            file_path = os.path.join(UPLOADS_DIR, unique_filename)
            
            # Resize the image
            try:
                with Image.open(media.file_path) as img:
                    resized_img = img.resize((width, height), Image.LANCZOS)
                    resized_img.save(file_path)
            except Exception as e:
                logger.error(f"Error resizing image: {str(e)}")
                return None
                
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Create the media record
            media_data = {
                "tenant_id": media.tenant_id,
                "name": f"{media.name} (Resized to {width}x{height})",
                "file_path": file_path,
                "file_url": f"/static/media/uploads/{unique_filename}",  # URL relative to the application root
                "file_type": "image",
                "mime_type": media.mime_type,
                "file_size": file_size,
                "width": width,
                "height": height,
                "alt_text": media.alt_text,
                "description": media.description,
                "meta_data": {
                    "original_media_id": str(media.id),
                    "original_width": media.width,
                    "original_height": media.height,
                    "resize_operation": "resize",
                    **(media.meta_data or {})
                },
                "is_ai_generated": media.is_ai_generated,
                "is_public": media.is_public
            }
            
            new_media = self.media_manager.create(media_data)
            logger.info(f"Resized image: {media.id} -> {new_media.id} ({width}x{height})")
            return new_media
        except Exception as e:
            logger.error(f"Error resizing image: {str(e)}")
            raise
            
    def crop_image(
        self, 
        media_id: str, 
        left: int, 
        top: int, 
        right: int, 
        bottom: int
    ) -> Optional[Media]:
        """
        Crop an image and create a new media record.
        
        Args:
            media_id: The ID of the image to crop
            left: The left coordinate of the crop box
            top: The top coordinate of the crop box
            right: The right coordinate of the crop box
            bottom: The bottom coordinate of the crop box
            
        Returns:
            The created media object if successful, None otherwise
        """
        try:
            media = self.media_manager.get(media_id)
            if not media or media.file_type != "image":
                return None
                
            # Generate a unique filename
            file_ext = os.path.splitext(media.file_path)[1].lower()
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            
            # Create file path
            file_path = os.path.join(UPLOADS_DIR, unique_filename)
            
            # Crop the image
            try:
                with Image.open(media.file_path) as img:
                    cropped_img = img.crop((left, top, right, bottom))
                    cropped_img.save(file_path)
            except Exception as e:
                logger.error(f"Error cropping image: {str(e)}")
                return None
                
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Get dimensions
            width = right - left
            height = bottom - top
            
            # Create the media record
            media_data = {
                "tenant_id": media.tenant_id,
                "name": f"{media.name} (Cropped)",
                "file_path": file_path,
                "file_url": f"/static/media/uploads/{unique_filename}",  # URL relative to the application root
                "file_type": "image",
                "mime_type": media.mime_type,
                "file_size": file_size,
                "width": width,
                "height": height,
                "alt_text": media.alt_text,
                "description": media.description,
                "meta_data": {
                    "original_media_id": str(media.id),
                    "original_width": media.width,
                    "original_height": media.height,
                    "crop_operation": "crop",
                    "crop_box": {
                        "left": left,
                        "top": top,
                        "right": right,
                        "bottom": bottom
                    },
                    **(media.meta_data or {})
                },
                "is_ai_generated": media.is_ai_generated,
                "is_public": media.is_public
            }
            
            new_media = self.media_manager.create(media_data)
            logger.info(f"Cropped image: {media.id} -> {new_media.id}")
            return new_media
        except Exception as e:
            logger.error(f"Error cropping image: {str(e)}")
            raise