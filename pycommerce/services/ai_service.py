"""
AI service for PyCommerce.

This module provides utilities for AI-powered content generation and other AI features.
"""

import os
import logging
import requests
import tempfile
import base64
from typing import Dict, Any, Optional, Tuple, Union, BinaryIO

from openai import OpenAI

# Configure logging
logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-powered features."""
    
    def __init__(self):
        """Initialize the AI service."""
        self.openai_key = os.environ.get('OPENAI_API_KEY')
        self.openai_client = None
        
        if self.openai_key:
            try:
                self.openai_client = OpenAI(api_key=self.openai_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing OpenAI client: {str(e)}")
        else:
            logger.warning("OPENAI_API_KEY not found in environment variables")
    
    def generate_content(self, prompt: str, style: str = "informative", tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate content using OpenAI.
        
        Args:
            prompt: The prompt text
            style: The style of content to generate (informative, persuasive, casual, formal, enthusiastic)
            tenant_id: Optional tenant ID for context
            
        Returns:
            Dictionary with generated content or error message
        """
        if not self.openai_client:
            logger.error("OpenAI client not initialized")
            return {"error": "AI service not configured. Contact the administrator."}
        
        try:
            # Add style guidance to the prompt
            style_guidance = {
                "informative": "Write an informative and educational piece with factual information.",
                "persuasive": "Write a persuasive piece that convinces the reader with strong arguments.",
                "casual": "Write in a casual, conversational tone, as if talking to a friend.",
                "formal": "Write in a formal and professional tone appropriate for business communications.",
                "enthusiastic": "Write with enthusiasm and excitement about the topic."
            }
            
            # Build the final prompt with style guidance
            system_prompt = f"You are a professional content writer. {style_guidance.get(style, style_guidance['informative'])}"
            
            # Add tenant context if available
            if tenant_id:
                system_prompt += f" This content is for the online store with ID: {tenant_id}."
            
            # Use GPT-4o for the highest quality responses
            # The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # Do not change this unless explicitly requested by the user
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # Latest model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=700,
                temperature=0.7,
            )
            
            # Extract and return the generated content
            content = response.choices[0].message.content
            
            return {
                "content": content,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error generating content with OpenAI: {str(e)}")
            return {
                "error": f"Failed to generate content: {str(e)}",
                "success": False
            }
    
    def generate_image(
        self, 
        prompt: str, 
        size: str = "1024x1024", 
        quality: str = "standard", 
        model: str = "dall-e-3"
    ) -> Dict[str, Any]:
        """
        Generate an image using DALL-E.
        
        Args:
            prompt: The text prompt to generate the image from
            size: Size of the image (1024x1024, 1024x1792, 1792x1024)
            quality: Image quality (standard, hd)
            model: DALL-E model version (dall-e-2, dall-e-3)
            
        Returns:
            Dictionary with image URL or error message
        """
        if not self.openai_client:
            logger.error("OpenAI client not initialized")
            return {
                "error": "AI service not configured. Contact the administrator.",
                "success": False
            }
        
        try:
            logger.info(f"Generating image with DALL-E using prompt: {prompt[:50]}...")
            logger.info(f"Parameters: size={size}, quality={quality}, model={model}")
            
            # Make the API call to generate the image
            response = self.openai_client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,
            )
            
            # Extract the image URL from the response
            image_url = response.data[0].url
            
            if not image_url:
                logger.error("No image URL returned from OpenAI")
                return {
                    "error": "Failed to generate image: No URL returned",
                    "success": False
                }
            
            logger.info("Successfully generated image with DALL-E")
            
            # Download the image as binary data
            image_data, mime_type, size_bytes = self._download_image(image_url)
            
            if not image_data:
                return {
                    "error": "Failed to download generated image",
                    "success": False
                }
            
            # Convert to base64 for easy embedding
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            return {
                "url": image_url,
                "data": image_data,
                "base64": image_base64,
                "mime_type": mime_type,
                "size": size_bytes,
                "success": True
            }
            
        except Exception as e:
            import traceback
            logger.error(f"Error generating image with DALL-E: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "error": f"Failed to generate image: {str(e)}",
                "success": False
            }
    
    def _download_image(self, url: str) -> Tuple[Optional[bytes], Optional[str], Optional[int]]:
        """
        Download an image from a URL.
        
        Args:
            url: URL of the image to download
            
        Returns:
            Tuple of (image_data, mime_type, size_in_bytes) or (None, None, None) if failed
        """
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get the mime type from the Content-Type header
            mime_type = response.headers.get('Content-Type', 'image/jpeg')
            
            # Get the content length
            content_length = int(response.headers.get('Content-Length', 0))
            
            # Read the image data
            image_data = response.content
            
            # Calculate the size if content_length is not available
            size_bytes = content_length or len(image_data)
            
            return image_data, mime_type, size_bytes
            
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            return None, None, None