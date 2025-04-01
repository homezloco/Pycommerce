"""
API routes for AI-powered content generation.

This module provides API endpoints for generating and enhancing content using OpenAI.
"""

import os
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from openai import OpenAI

# Configure logging
logger = logging.getLogger(__name__)

# Create a router for AI routes
router = APIRouter()

# Configure OpenAI client
openai_api_key = os.environ.get("OPENAI_API_KEY")
if not openai_api_key:
    logger.warning("OpenAI API key not configured. AI features will not work.")
else:
    # Initialize OpenAI client
    client = OpenAI(api_key=openai_api_key)


class GenerateContentRequest(BaseModel):
    prompt: str


class EnhanceContentRequest(BaseModel):
    text: str
    instructions: Optional[str] = None


class AIContentResponse(BaseModel):
    content: str


@router.post("/generate", response_model=AIContentResponse)
async def generate_content(request: GenerateContentRequest):
    """
    Generate content using OpenAI GPT.
    
    Args:
        request: Contains the prompt for generating content
    
    Returns:
        Generated content
    """
    if not openai_api_key:
        raise HTTPException(
            status_code=503, 
            detail="OpenAI API key not configured. Please configure the OPENAI_API_KEY environment variable."
        )
    
    try:
        # Create completion
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that specializes in creating e-commerce product descriptions, marketing copy, and SEO content."},
                {"role": "user", "content": request.prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        # Extract content from response
        content = completion.choices[0].message.content
        
        return AIContentResponse(content=content)
    
    except Exception as e:
        logger.error(f"Error generating content with OpenAI: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating content: {str(e)}")


@router.post("/enhance", response_model=AIContentResponse)
async def enhance_content(request: EnhanceContentRequest):
    """
    Enhance existing content using OpenAI GPT.
    
    Args:
        request: Contains the text to enhance and optional instructions
    
    Returns:
        Enhanced content
    """
    if not openai_api_key:
        raise HTTPException(
            status_code=503, 
            detail="OpenAI API key not configured. Please configure the OPENAI_API_KEY environment variable."
        )
    
    try:
        # Default instructions if none provided
        instructions = request.instructions or "Enhance this text to be more engaging and persuasive for e-commerce customers."
        
        # Create completion
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that specializes in creating e-commerce product descriptions, marketing copy, and SEO content."},
                {"role": "user", "content": f"Please enhance the following text. {instructions}\n\nOriginal text:\n{request.text}"}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        # Extract content from response
        content = completion.choices[0].message.content
        
        return AIContentResponse(content=content)
    
    except Exception as e:
        logger.error(f"Error enhancing content with OpenAI: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error enhancing content: {str(e)}")