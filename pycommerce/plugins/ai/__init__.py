
"""
AI Plugin package for PyCommerce.

This package provides AI text generation capabilities for the PyCommerce platform.
"""

# Import core configuration functions
from pycommerce.plugins.ai.config import load_ai_config, save_ai_config, get_ai_providers
from pycommerce.plugins.ai.providers import get_ai_provider

# Make key functions available at the package level
__all__ = [
    "load_ai_config",
    "save_ai_config",
    "get_ai_providers",
    "get_ai_provider"
]
