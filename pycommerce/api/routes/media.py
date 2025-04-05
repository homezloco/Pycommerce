"""
Media API routes for PyCommerce.

This module provides API endpoints for managing media files.
"""

import io
import os
import uuid
import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from pycommerce.models.media import Media
from pycommerce.services.media_service import MediaService
from pycommerce.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/media", tags=["Media"])

# Create media service instance
media_service = MediaService()


class MediaResponse(BaseModel):
    """Media response model."""
    
    id: str
    tenant_id: Optional[str] = None
    name: str
    file_url: str
    file_type: str
    mime_type: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    alt_text: Optional[str] = None
    description: Optional[str] = None
    is_ai_generated: bool
    is_public: bool
    created_at: str
    updated_at: str
    
    class Config:
        """Pydantic configuration."""
        orm_mode = True
        
        
class MediaListResponse(BaseModel):
    """Media list response model."""
    
    media: List[MediaResponse]
    count: int
    total: int
    
    
class DALLEGenerationRequest(BaseModel):
    """DALL-E image generation request model."""
    
    prompt: str
    tenant_id: Optional[str] = None
    size: str = "1024x1024"
    quality: str = "standard"
    alt_text: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.get("", response_model=MediaListResponse)
async def list_media(
    tenant_id: Optional[str] = None,
    file_type: Optional[str] = None,
    is_ai_generated: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = Query(100, gt=0, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    List media files with optional filtering.
    
    Args:
        tenant_id: Optional tenant ID to filter by
        file_type: Optional file type to filter by (image, video, audio, etc.)
        is_ai_generated: Optional filter for AI-generated media
        search: Optional search term for name and description
        limit: Maximum number of items to return
        offset: Offset for pagination
        
    Returns:
        MediaListResponse with list of media and pagination info
    """
    try:
        media_list = media_service.list_media(
            tenant_id=tenant_id,
            file_type=file_type,
            is_ai_generated=is_ai_generated,
            search_term=search,
            limit=limit,
            offset=offset
        )
        
        # Calculate total (without pagination)
        total = len(media_service.list_media(
            tenant_id=tenant_id,
            file_type=file_type,
            is_ai_generated=is_ai_generated,
            search_term=search
        ))
        
        return MediaListResponse(
            media=[MediaResponse(
                id=str(media.id),
                tenant_id=str(media.tenant_id) if media.tenant_id else None,
                name=media.name,
                file_url=media.file_url,
                file_type=media.file_type,
                mime_type=media.mime_type,
                file_size=media.file_size,
                width=media.width,
                height=media.height,
                alt_text=media.alt_text,
                description=media.description,
                is_ai_generated=media.is_ai_generated,
                is_public=media.is_public,
                created_at=media.created_at.isoformat() if media.created_at else None,
                updated_at=media.updated_at.isoformat() if media.updated_at else None
            ) for media in media_list],
            count=len(media_list),
            total=total
        )
    except Exception as e:
        logger.error(f"Error listing media: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing media: {str(e)}")
        

@router.get("/{media_id}", response_model=MediaResponse)
async def get_media(media_id: str):
    """
    Get a media file by ID.
    
    Args:
        media_id: The ID of the media to retrieve
        
    Returns:
        MediaResponse with media details
    """
    try:
        media = media_service.get_media(media_id)
        if not media:
            raise HTTPException(status_code=404, detail=f"Media not found: {media_id}")
            
        return MediaResponse(
            id=str(media.id),
            tenant_id=str(media.tenant_id) if media.tenant_id else None,
            name=media.name,
            file_url=media.file_url,
            file_type=media.file_type,
            mime_type=media.mime_type,
            file_size=media.file_size,
            width=media.width,
            height=media.height,
            alt_text=media.alt_text,
            description=media.description,
            is_ai_generated=media.is_ai_generated,
            is_public=media.is_public,
            created_at=media.created_at.isoformat() if media.created_at else None,
            updated_at=media.updated_at.isoformat() if media.updated_at else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting media: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting media: {str(e)}")
        

@router.post("/upload", response_model=MediaResponse)
async def upload_media(
    file: UploadFile = File(...),
    tenant_id: Optional[str] = Form(None),
    alt_text: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """
    Upload a media file.
    
    Args:
        file: The file to upload
        tenant_id: Optional tenant ID
        alt_text: Optional alt text for the file
        description: Optional description for the file
        
    Returns:
        MediaResponse with the uploaded media details
    """
    try:
        # Validate file extension
        _, file_ext = os.path.splitext(file.filename)
        file_ext = file_ext.lstrip(".").lower()
        
        if file_ext not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File extension not allowed: {file_ext}. Allowed extensions: {', '.join(settings.allowed_extensions)}"
            )
            
        # Read file content
        content = await file.read()
        
        # Check file size
        if len(content) > settings.max_upload_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {len(content)} bytes. Maximum size: {settings.max_upload_size} bytes"
            )
            
        # Reset file pointer to the beginning
        file_obj = io.BytesIO(content)
        
        # Upload the file
        media = media_service.upload_file(
            file=file_obj,
            filename=file.filename,
            tenant_id=tenant_id,
            alt_text=alt_text,
            description=description
        )
        
        return MediaResponse(
            id=str(media.id),
            tenant_id=str(media.tenant_id) if media.tenant_id else None,
            name=media.name,
            file_url=media.file_url,
            file_type=media.file_type,
            mime_type=media.mime_type,
            file_size=media.file_size,
            width=media.width,
            height=media.height,
            alt_text=media.alt_text,
            description=media.description,
            is_ai_generated=media.is_ai_generated,
            is_public=media.is_public,
            created_at=media.created_at.isoformat() if media.created_at else None,
            updated_at=media.updated_at.isoformat() if media.updated_at else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")
        

@router.post("/generate", response_model=MediaResponse)
async def generate_image(request: DALLEGenerationRequest):
    """
    Generate an image using DALL-E.
    
    Args:
        request: DALL-E generation request with prompt and options
        
    Returns:
        MediaResponse with the generated image details
    """
    try:
        # Check for OpenAI API Key
        if not settings.openai_api_key:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable."
            )
            
        # Generate the image
        media = media_service.generate_image_with_dalle(
            prompt=request.prompt,
            tenant_id=request.tenant_id,
            size=request.size,
            quality=request.quality,
            alt_text=request.alt_text,
            description=request.description,
            metadata=request.metadata
        )
        
        if not media:
            raise HTTPException(status_code=500, detail="Failed to generate image")
            
        return MediaResponse(
            id=str(media.id),
            tenant_id=str(media.tenant_id) if media.tenant_id else None,
            name=media.name,
            file_url=media.file_url,
            file_type=media.file_type,
            mime_type=media.mime_type,
            file_size=media.file_size,
            width=media.width,
            height=media.height,
            alt_text=media.alt_text,
            description=media.description,
            is_ai_generated=media.is_ai_generated,
            is_public=media.is_public,
            created_at=media.created_at.isoformat() if media.created_at else None,
            updated_at=media.updated_at.isoformat() if media.updated_at else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")
        

@router.delete("/{media_id}")
async def delete_media(media_id: str):
    """
    Delete a media file.
    
    Args:
        media_id: The ID of the media to delete
        
    Returns:
        JSON response with success status
    """
    try:
        success = media_service.delete_media(media_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Media not found: {media_id}")
            
        return JSONResponse(content={"success": True, "message": f"Media deleted: {media_id}"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting media: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting media: {str(e)}")
        

@router.post("/{media_id}/resize", response_model=MediaResponse)
async def resize_image(
    media_id: str,
    width: int = Query(..., gt=0, le=10000),
    height: int = Query(..., gt=0, le=10000)
):
    """
    Resize an image.
    
    Args:
        media_id: The ID of the image to resize
        width: New width (1-10000)
        height: New height (1-10000)
        
    Returns:
        MediaResponse with the resized image details
    """
    try:
        media = media_service.resize_image(media_id, width, height)
        if not media:
            raise HTTPException(status_code=404, detail=f"Media not found or not an image: {media_id}")
            
        return MediaResponse(
            id=str(media.id),
            tenant_id=str(media.tenant_id) if media.tenant_id else None,
            name=media.name,
            file_url=media.file_url,
            file_type=media.file_type,
            mime_type=media.mime_type,
            file_size=media.file_size,
            width=media.width,
            height=media.height,
            alt_text=media.alt_text,
            description=media.description,
            is_ai_generated=media.is_ai_generated,
            is_public=media.is_public,
            created_at=media.created_at.isoformat() if media.created_at else None,
            updated_at=media.updated_at.isoformat() if media.updated_at else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resizing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error resizing image: {str(e)}")
        

@router.post("/{media_id}/crop", response_model=MediaResponse)
async def crop_image(
    media_id: str,
    left: int = Query(..., ge=0),
    top: int = Query(..., ge=0),
    right: int = Query(..., gt=0),
    bottom: int = Query(..., gt=0)
):
    """
    Crop an image.
    
    Args:
        media_id: The ID of the image to crop
        left: Left coordinate of crop box
        top: Top coordinate of crop box
        right: Right coordinate of crop box
        bottom: Bottom coordinate of crop box
        
    Returns:
        MediaResponse with the cropped image details
    """
    try:
        # Validate coordinates
        if left >= right or top >= bottom:
            raise HTTPException(status_code=400, detail="Invalid crop coordinates: left must be less than right and top must be less than bottom")
            
        media = media_service.crop_image(media_id, left, top, right, bottom)
        if not media:
            raise HTTPException(status_code=404, detail=f"Media not found or not an image: {media_id}")
            
        return MediaResponse(
            id=str(media.id),
            tenant_id=str(media.tenant_id) if media.tenant_id else None,
            name=media.name,
            file_url=media.file_url,
            file_type=media.file_type,
            mime_type=media.mime_type,
            file_size=media.file_size,
            width=media.width,
            height=media.height,
            alt_text=media.alt_text,
            description=media.description,
            is_ai_generated=media.is_ai_generated,
            is_public=media.is_public,
            created_at=media.created_at.isoformat() if media.created_at else None,
            updated_at=media.updated_at.isoformat() if media.updated_at else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cropping image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error cropping image: {str(e)}")