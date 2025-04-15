
"""
AI content generation plugin for PyCommerce.

This module provides functionality for generating content using AI services.
"""
import logging

logger = logging.getLogger(__name__)

# Import configuration with error handling
try:
    from . import config as ai_config
    from . import providers
    HAS_CONFIG = True
except ImportError as e:
    logger.warning(f"AI configuration module not available: {str(e)}")
    HAS_CONFIG = False

def get_ai_provider(provider_name=None, api_key=None):
    """Get an AI provider instance.
    
    Args:
        provider_name: The name of the provider to use
        api_key: Optional API key to override the configured key
        
    Returns:
        An AI provider instance
    """
    if not HAS_CONFIG:
        return MockAIProvider()
    
    try:
        return providers.get_ai_provider(provider_name, api_key)
    except Exception as e:
        logger.error(f"Error getting AI provider: {str(e)}")
        return MockAIProvider()

class MockAIProvider:
    """Mock AI provider for fallback when actual AI module is not available."""
    def generate_content(self, prompt, **kwargs):
        """Generate content based on the given prompt."""
        return {
            "content": f"AI-generated content placeholder (prompt: {prompt[:30]}...)",
            "success": True
        }
