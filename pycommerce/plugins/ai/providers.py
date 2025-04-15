
"""
AI provider implementations for PyCommerce.

This module provides adapters for different AI service providers.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)

# Dictionary of registered AI providers
_providers = {}

def register_provider(name: str, provider_class: Any):
    """
    Register an AI provider.

    Args:
        name: Provider name/identifier
        provider_class: Provider class or factory
    """
    global _providers
    _providers[name] = provider_class
    logger.info(f"Registered AI provider: {name}")

def get_ai_provider(provider_name: str, config: Dict[str, Any] = None):
    """
    Get an AI provider by name.

    Args:
        provider_name: Provider name/identifier
        config: Provider configuration

    Returns:
        Provider instance
    """
    # Default to mock provider for testing and development
    if provider_name not in _providers:
        return MockAIProvider(config or {})
    
    provider_class = _providers.get(provider_name)
    return provider_class(config or {})

# Base class for AI providers
class BaseAIProvider:
    """Base class for AI service providers."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the provider.

        Args:
            config: Provider configuration
        """
        self.config = config

    def generate_text(self, prompt: str, options: Dict[str, Any] = None) -> str:
        """
        Generate text based on a prompt.

        Args:
            prompt: Text prompt for content generation
            options: Additional options for generation

        Returns:
            Generated text
        """
        raise NotImplementedError("Subclasses must implement generate_text")

    def enhance_text(self, text: str, instructions: str = None, options: Dict[str, Any] = None) -> str:
        """
        Enhance existing text based on instructions.

        Args:
            text: Text to enhance
            instructions: Enhancement instructions
            options: Additional options for enhancement

        Returns:
            Enhanced text
        """
        raise NotImplementedError("Subclasses must implement enhance_text")

# Mock AI provider for testing and development
class MockAIProvider(BaseAIProvider):
    """Mock AI provider for testing without external API dependencies."""

    def generate_text(self, prompt: str, options: Dict[str, Any] = None) -> str:
        """
        Generate mock text based on a prompt.

        Args:
            prompt: Text prompt for content generation
            options: Additional options for generation

        Returns:
            Generated mock text
        """
        options = options or {}
        
        # Return different responses based on the prompt
        if "product" in prompt.lower():
            return """<h2>Amazing Product</h2>
            <p>This premium product offers exceptional quality and durability. Designed with the user in mind, it provides:</p>
            <ul>
                <li>Outstanding performance</li>
                <li>Elegant design</li>
                <li>Long-lasting reliability</li>
            </ul>
            <p>Perfect for both professional and personal use, this product will exceed your expectations.</p>"""
            
        elif "blog" in prompt.lower():
            return """<h2>10 Tips for Success</h2>
            <p>Success doesn't come overnight. It requires dedication, perseverance, and smart strategies.</p>
            <p>Here are 10 proven tips to help you reach your goals:</p>
            <ol>
                <li>Set clear, measurable objectives</li>
                <li>Develop a consistent routine</li>
                <li>Learn from failures</li>
                <li>Network with industry professionals</li>
                <li>Stay updated with latest trends</li>
                <li>Maintain a positive mindset</li>
                <li>Prioritize self-care</li>
                <li>Seek feedback regularly</li>
                <li>Adapt to changing circumstances</li>
                <li>Celebrate small wins</li>
            </ol>
            <p>Implementing these strategies consistently will set you on the path to success.</p>"""
            
        else:
            return f"<p>Here's some generated content based on your prompt: {prompt[:100]}...</p><p>This is a mock response for testing purposes.</p>"

    def enhance_text(self, text: str, instructions: str = None, options: Dict[str, Any] = None) -> str:
        """
        Generate a mock enhancement of the provided text.

        Args:
            text: Text to enhance
            instructions: Enhancement instructions
            options: Additional options for enhancement

        Returns:
            Enhanced text
        """
        options = options or {}
        
        # Simple enhancement: add some formatting and a conclusion
        enhanced_text = f"<h2>Enhanced Content</h2>\n\n{text}\n\n"
        
        if instructions:
            if "seo" in instructions.lower():
                enhanced_text += "<h3>SEO Optimized</h3>\n<p>This content has been optimized for search engines.</p>\n"
            if "formal" in instructions.lower():
                enhanced_text += "<p><em>This content has been adjusted to use more formal language.</em></p>\n"
            if "casual" in instructions.lower():
                enhanced_text += "<p><em>This content has been adjusted to use more casual, conversational language.</em></p>\n"
        
        enhanced_text += "<p><strong>Conclusion:</strong> This enhanced text provides better structure and clarity.</p>"
        
        return enhanced_text

# Register the mock provider
register_provider('mock', MockAIProvider)

# Try to import and register the OpenAI provider if available
try:
    import openai
    
    class OpenAIProvider(BaseAIProvider):
        """OpenAI provider implementation."""
        
        def __init__(self, config: Dict[str, Any]):
            super().__init__(config)
            self.client = openai.OpenAI(api_key=config.get("api_key"))
            self.model = config.get("model", "gpt-3.5-turbo")
            self.temperature = float(config.get("temperature", 0.7))
            self.max_tokens = int(config.get("max_tokens", 500))
        
        def generate_text(self, prompt: str, options: Dict[str, Any] = None) -> str:
            """Generate text using OpenAI API."""
            options = options or {}
            
            try:
                response = self.client.chat.completions.create(
                    model=options.get("model", self.model),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=options.get("temperature", self.temperature),
                    max_tokens=options.get("max_tokens", self.max_tokens)
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                logger.error(f"OpenAI API error: {str(e)}")
                return f"Error generating content: {str(e)}"
        
        def enhance_text(self, text: str, instructions: str = None, options: Dict[str, Any] = None) -> str:
            """Enhance text using OpenAI API."""
            options = options or {}
            
            prompt = f"Please enhance the following text"
            if instructions:
                prompt += f" according to these instructions: {instructions}"
            prompt += f"\n\nText to enhance:\n{text}"
            
            return self.generate_text(prompt, options)
    
    # Register the OpenAI provider
    register_provider('openai', OpenAIProvider)
    
except ImportError:
    logger.warning("OpenAI package not installed, using mock provider instead")
