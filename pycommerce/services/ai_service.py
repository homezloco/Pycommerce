"""
AI service for PyCommerce.

This module provides utilities for AI-powered content generation and other AI features.
"""

import os
import logging
from typing import Dict, Any, Optional

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