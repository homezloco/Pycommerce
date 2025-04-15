
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

        logger.info(f"AI configuration initialized with provider: {settings.get('default_provider', 'openai')}")

        # Initialize the appropriate provider
        try:
            from .providers import get_ai_provider
            provider = get_ai_provider(settings.get('default_provider', 'openai'))
            if provider:
                logger.info(f"Successfully initialized AI provider: {settings.get('default_provider', 'openai')}")
                return True
            else:
                logger.warning(f"Provider {settings.get('default_provider')} could not be initialized")
                return False
        except Exception as e:
            logger.warning(f"Error initializing AI provider: {str(e)}")
            return False
            
    except ImportError as e:
        logger.warning(f"Error importing AI plugin modules: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error initializing AI plugin: {str(e)}")
        return False

# Initialize AI plugin
try:
    is_initialized = init_ai_plugin()
except Exception as e:
    logger.error(f"Failed to initialize AI plugin: {str(e)}")
    is_initialized = False
