"""
AI plugin for PyCommerce.

This module provides AI-powered content generation and analysis capabilities.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def init_ai_plugin():
    """Initialize the AI plugin."""
    try:
        from .config import get_ai_settings, is_ai_enabled
        settings = get_ai_settings()

        if not is_ai_enabled():
            logger.info("AI plugin is disabled in configuration")
            return False

        logger.info(f"Initializing AI plugin with provider: {settings.get('default_provider', 'none')}")

        # Initialize the appropriate provider
        from .providers import get_provider
        provider = get_provider(settings.get('default_provider', 'openai'))
        if provider is None:
            logger.warning(f"Provider {settings.get('default_provider')} is not available")
            return False

        return True
    except ImportError as e:
        logger.warning(f"Error initializing AI plugin: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error initializing AI plugin: {str(e)}")
        return False

# Initialize AI plugin
is_initialized = init_ai_plugin()