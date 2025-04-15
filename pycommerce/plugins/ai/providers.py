"""
AI provider implementations.

This module contains implementations for different AI text generation providers.
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Base class for AI providers."""
    
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text based on a prompt.
        
        Args:
            prompt: The text prompt to use for generation
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text content
        """
        pass
    
    @abstractmethod
    def enhance_text(self, text: str, instructions: Optional[str] = None, **kwargs) -> str:
        """
        Enhance existing text based on instructions.
        
        Args:
            text: The text to enhance
            instructions: Optional instructions for enhancement
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Enhanced text content
        """
        pass


class OpenAIProvider(AIProvider):
    """OpenAI text generation provider."""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", temperature: float = 0.7):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model to use for generation (default: gpt-3.5-turbo)
            temperature: Temperature setting (default: 0.7)
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        
        # Import here to avoid loading the module if OpenAI is not used
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using OpenAI.
        
        Args:
            prompt: The text prompt to use for generation
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            Generated text content
        """
        try:
            # Override defaults with kwargs if provided
            model = kwargs.get("model", self.model)
            temperature = kwargs.get("temperature", self.temperature)
            
            # Create completion
            completion = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that specializes in creating e-commerce product descriptions, marketing copy, and SEO content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=temperature
            )
            
            # Extract content from response
            content = completion.choices[0].message.content
            return content
            
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {str(e)}")
            raise
    
    def enhance_text(self, text: str, instructions: Optional[str] = None, **kwargs) -> str:
        """
        Enhance text using OpenAI.
        
        Args:
            text: The text to enhance
            instructions: Optional instructions for enhancement
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            Enhanced text content
        """
        try:
            # Override defaults with kwargs if provided
            model = kwargs.get("model", self.model)
            temperature = kwargs.get("temperature", self.temperature)
            
            # Default instructions if none provided
            if not instructions:
                instructions = "Enhance this text to be more engaging and persuasive for e-commerce customers."
            
            # Create completion
            completion = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that specializes in creating e-commerce product descriptions, marketing copy, and SEO content."},
                    {"role": "user", "content": f"Please enhance the following text. {instructions}\n\nOriginal text:\n{text}"}
                ],
                max_tokens=1500,
                temperature=temperature
            )
            
            # Extract content from response
            content = completion.choices[0].message.content
            return content
            
        except Exception as e:
            logger.error(f"Error enhancing text with OpenAI: {str(e)}")
            raise


class GeminiProvider(AIProvider):
    """Google Gemini AI text generation provider."""
    
    def __init__(self, api_key: str, model: str = "gemini-pro"):
        """
        Initialize Gemini provider.
        
        Args:
            api_key: Google Gemini API key
            model: Model to use for generation (default: gemini-pro)
        """
        self.api_key = api_key
        self.model = model
        
        # Import here to avoid loading the module if Gemini is not used
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.genai = genai
        except ImportError:
            logger.warning("Google Generative AI package not installed. Install with: pip install google-generativeai")
            raise
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Google Gemini.
        
        Args:
            prompt: The text prompt to use for generation
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            Generated text content
        """
        try:
            # Override defaults with kwargs if provided
            model = kwargs.get("model", self.model)
            
            # Create system prompt
            system_prompt = "You are a helpful assistant that specializes in creating e-commerce product descriptions, marketing copy, and SEO content."
            
            # Create model and generate content
            model = self.genai.GenerativeModel(model)
            response = model.generate_content(
                f"{system_prompt}\n\n{prompt}"
            )
            
            # Extract content from response
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating text with Gemini: {str(e)}")
            raise
    
    def enhance_text(self, text: str, instructions: Optional[str] = None, **kwargs) -> str:
        """
        Enhance text using Google Gemini.
        
        Args:
            text: The text to enhance
            instructions: Optional instructions for enhancement
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            Enhanced text content
        """
        try:
            # Override defaults with kwargs if provided
            model_name = kwargs.get("model", self.model)
            
            # Default instructions if none provided
            if not instructions:
                instructions = "Enhance this text to be more engaging and persuasive for e-commerce customers."
            
            # Create system prompt
            system_prompt = "You are a helpful assistant that specializes in creating e-commerce product descriptions, marketing copy, and SEO content."
            
            # Create model and generate content
            model = self.genai.GenerativeModel(model_name)
            response = model.generate_content(
                f"{system_prompt}\n\nPlease enhance the following text. {instructions}\n\nOriginal text:\n{text}"
            )
            
            # Extract content from response
            return response.text
            
        except Exception as e:
            logger.error(f"Error enhancing text with Gemini: {str(e)}")
            raise


class DeepSeekProvider(AIProvider):
    """DeepSeek AI text generation provider."""
    
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        """
        Initialize DeepSeek provider.
        
        Args:
            api_key: DeepSeek API key
            model: Model to use for generation (default: deepseek-chat)
        """
        self.api_key = api_key
        self.model = model
        
        # Import here to avoid loading the module if DeepSeek is not used
        from openai import OpenAI
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"  # DeepSeek API uses OpenAI-compatible endpoint
        )
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using DeepSeek.
        
        Args:
            prompt: The text prompt to use for generation
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            Generated text content
        """
        try:
            # Override defaults with kwargs if provided
            model = kwargs.get("model", self.model)
            
            # Create completion
            completion = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that specializes in creating e-commerce product descriptions, marketing copy, and SEO content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            # Extract content from response
            content = completion.choices[0].message.content
            return content
            
        except Exception as e:
            logger.error(f"Error generating text with DeepSeek: {str(e)}")
            raise
    
    def enhance_text(self, text: str, instructions: Optional[str] = None, **kwargs) -> str:
        """
        Enhance text using DeepSeek.
        
        Args:
            text: The text to enhance
            instructions: Optional instructions for enhancement
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            Enhanced text content
        """
        try:
            # Override defaults with kwargs if provided
            model = kwargs.get("model", self.model)
            
            # Default instructions if none provided
            if not instructions:
                instructions = "Enhance this text to be more engaging and persuasive for e-commerce customers."
            
            # Create completion
            completion = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that specializes in creating e-commerce product descriptions, marketing copy, and SEO content."},
                    {"role": "user", "content": f"Please enhance the following text. {instructions}\n\nOriginal text:\n{text}"}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            # Extract content from response
            content = completion.choices[0].message.content
            return content
            
        except Exception as e:
            logger.error(f"Error enhancing text with DeepSeek: {str(e)}")
            raise


class OpenRouterProvider(AIProvider):
    """OpenRouter text generation provider, enabling access to multiple AI models."""
    
    def __init__(self, api_key: str, model: str = "openai/gpt-3.5-turbo"):
        """
        Initialize OpenRouter provider.
        
        Args:
            api_key: OpenRouter API key
            model: Model to use for generation (default: openai/gpt-3.5-turbo)
        """
        self.api_key = api_key
        self.model = model
        
        # Import here to avoid loading the module if OpenRouter is not used
        from openai import OpenAI
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using OpenRouter.
        
        Args:
            prompt: The text prompt to use for generation
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            Generated text content
        """
        try:
            # Override defaults with kwargs if provided
            model = kwargs.get("model", self.model)
            
            # Create completion
            completion = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that specializes in creating e-commerce product descriptions, marketing copy, and SEO content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7,
                headers={
                    "HTTP-Referer": "https://pycommerce.app",  # Replace with your site
                    "X-Title": "PyCommerce AI Editor"
                }
            )
            
            # Extract content from response
            content = completion.choices[0].message.content
            return content
            
        except Exception as e:
            logger.error(f"Error generating text with OpenRouter: {str(e)}")
            raise
    
    def enhance_text(self, text: str, instructions: Optional[str] = None, **kwargs) -> str:
        """
        Enhance text using OpenRouter.
        
        Args:
            text: The text to enhance
            instructions: Optional instructions for enhancement
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            Enhanced text content
        """
        try:
            # Override defaults with kwargs if provided
            model = kwargs.get("model", self.model)
            
            # Default instructions if none provided
            if not instructions:
                instructions = "Enhance this text to be more engaging and persuasive for e-commerce customers."
            
            # Create completion
            completion = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that specializes in creating e-commerce product descriptions, marketing copy, and SEO content."},
                    {"role": "user", "content": f"Please enhance the following text. {instructions}\n\nOriginal text:\n{text}"}
                ],
                max_tokens=1500,
                temperature=0.7,
                headers={
                    "HTTP-Referer": "https://pycommerce.app",  # Replace with your site
                    "X-Title": "PyCommerce AI Editor"
                }
            )
            
            # Extract content from response
            content = completion.choices[0].message.content
            return content
            
        except Exception as e:
            logger.error(f"Error enhancing text with OpenRouter: {str(e)}")
            raise


def get_ai_provider(provider_id: str, config: Dict[str, Any]) -> AIProvider:
    """
    Get an AI provider instance based on provider ID and configuration.
    
    Args:
        provider_id: The AI provider ID
        config: Configuration for the provider
        
    Returns:
        An AIProvider instance
        
    Raises:
        ValueError: If the provider ID is invalid or the configuration is incomplete
    """
    if provider_id == "openai":
        api_key = config.get("api_key")
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        model = config.get("model", "gpt-3.5-turbo")
        temperature = float(config.get("temperature", 0.7))
        
        return OpenAIProvider(api_key, model, temperature)
        
    elif provider_id == "gemini":
        api_key = config.get("api_key")
        if not api_key:
            raise ValueError("Gemini API key is required")
        
        model = config.get("model", "gemini-pro")
        
        return GeminiProvider(api_key, model)
        
    elif provider_id == "deepseek":
        api_key = config.get("api_key")
        if not api_key:
            raise ValueError("DeepSeek API key is required")
        
        model = config.get("model", "deepseek-chat")
        
        return DeepSeekProvider(api_key, model)
        
    elif provider_id == "openrouter":
        api_key = config.get("api_key")
        if not api_key:
            raise ValueError("OpenRouter API key is required")
        
        model = config.get("model", "openai/gpt-3.5-turbo")
        
        return OpenRouterProvider(api_key, model)
        
    else:
        raise ValueError(f"Invalid AI provider: {provider_id}")
"""
AI provider implementations for PyCommerce.

This module contains the implementations for different AI providers.
"""
import logging
import json
import os
from typing import Dict, List, Optional, Any
import requests

from .config import get_ai_config_service

logger = logging.getLogger(__name__)

class AIProvider:
    """Base class for AI providers."""
    
    def __init__(self):
        """Initialize the AI provider."""
        self.config_service = get_ai_config_service()
        
    def is_configured(self) -> bool:
        """Check if the provider is properly configured."""
        return bool(self.config_service.get_api_key())
    
    def generate_text(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
        """Generate text based on a prompt."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def analyze_text(self, text: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze text and return structured data."""
        raise NotImplementedError("Subclasses must implement this method")

class OpenAIProvider(AIProvider):
    """OpenAI provider implementation."""
    
    def generate_text(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
        """Generate text using OpenAI."""
        if not self.is_configured():
            logger.warning("OpenAI API key not configured")
            return "AI generation unavailable (API key not configured)"
        
        options = options or {}
        
        try:
            api_key = self.config_service.get_api_key()
            model = options.get("model", self.config_service.get_model())
            temperature = options.get("temperature", self.config_service.config.get("temperature", 0.7))
            max_tokens = options.get("max_tokens", self.config_service.config.get("max_tokens", 1024))
            
            # Make API request to OpenAI
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return f"Error generating text: API returned status {response.status_code}"
                
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {str(e)}")
            return f"Error generating text: {str(e)}"
    
    def analyze_text(self, text: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze text using OpenAI."""
        if not self.is_configured():
            logger.warning("OpenAI API key not configured")
            return {"error": "API key not configured"}
        
        options = options or {}
        
        try:
            api_key = self.config_service.get_api_key()
            model = options.get("model", self.config_service.get_model())
            
            # Create a system prompt that requests structured data
            system_prompt = options.get("system_prompt", "Analyze the following text and provide structured data as JSON.")
            
            # Make API request to OpenAI
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                "response_format": {"type": "json_object"}
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                # Parse the JSON response
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return {"error": "Failed to parse JSON response", "raw_content": content}
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return {"error": f"API returned status {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error analyzing text with OpenAI: {str(e)}")
            return {"error": str(e)}

# Factory function to get the appropriate provider
def get_ai_provider(provider_name: Optional[str] = None) -> AIProvider:
    """Get an AI provider instance based on configuration."""
    config_service = get_ai_config_service()
    provider_name = provider_name or config_service.config.get("provider", "openai")
    
    if provider_name == "openai":
        return OpenAIProvider()
    else:
        logger.warning(f"Unknown AI provider: {provider_name}, falling back to OpenAI")
        return OpenAIProvider()
