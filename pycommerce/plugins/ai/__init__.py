
"""
AI Plugin for PyCommerce platform.
"""
import logging
from typing import Optional

from .config import init_ai_config, get_ai_config
from .providers import MockAIProvider, OpenAIProvider, AIProvider

logger = logging.getLogger(__name__)

# Initialize AI configuration
init_ai_config()

def get_ai_provider() -> Optional[AIProvider]:
    """
    Get the configured AI provider.
    Returns a provider instance or None if no provider is available.
    """
    config = get_ai_config()
    provider_name = config.get("provider", "mock")
    
    if provider_name == "openai" and config.get("openai", {}).get("enabled", False):
        try:
            api_key = config.get("openai", {}).get("api_key")
            model = config.get("openai", {}).get("model", "gpt-3.5-turbo")
            
            if not api_key:
                logger.warning("OpenAI provider selected but no API key provided")
                return MockAIProvider()
                
            return OpenAIProvider(api_key=api_key, model=model)
        except Exception as e:
            logger.error(f"Error initializing OpenAI provider: {str(e)}")
            # Fall back to mock provider
            return MockAIProvider()
    
    # Default to mock provider
    logger.info("Using mock AI provider")
    return MockAIProvider()
