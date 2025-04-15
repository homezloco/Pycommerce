
"""
AI Plugin package for PyCommerce.

This package provides AI text generation capabilities for the PyCommerce platform.
"""

import logging

logger = logging.getLogger(__name__)

# Import core configuration functions 
from pycommerce.plugins.ai.config import load_ai_config, get_ai_providers
from pycommerce.plugins.ai.providers import get_ai_provider, AIProvider

# Register the plugin
def register_plugin():
    """Register the AI plugin with the system."""
    from pycommerce.plugins import register_plugin
    try:
        register_plugin("ai_assistant", "0.1.0", "AI Assistant")
        logger.info("AI plugin registered successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to register AI plugin: {str(e)}")
        return False
