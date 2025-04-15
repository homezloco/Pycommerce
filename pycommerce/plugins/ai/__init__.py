"""
AI Plugin package for PyCommerce.

This package provides AI text generation capabilities for the PyCommerce platform.
"""

import logging
from pycommerce.plugins.ai.config import load_ai_config, get_ai_providers
from pycommerce.plugins import register_plugin

logger = logging.getLogger(__name__)

def initialize():
    """Initialize AI plugin and register it with the system."""
    try:
        # Register the AI plugin
        register_plugin("ai_content", "AI Content Generation", "0.1.0")
        logger.info("Initialized AI content plugin")
        return True
    except Exception as e:
        logger.warning(f"Failed to initialize AI plugin: {str(e)}")
        return False