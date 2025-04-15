"""
AI Plugin package for PyCommerce.

This package provides AI text generation capabilities for the PyCommerce platform.
"""

from pycommerce.plugins.ai.config import load_ai_config
"""
AI plugin for PyCommerce.

This module provides AI-powered features for the platform.
"""

from .config import get_ai_config_service, AIConfigService
from .providers import get_ai_provider, AIProvider, OpenAIProvider

__all__ = [
    'get_ai_config_service',
    'AIConfigService',
    'get_ai_provider',
    'AIProvider',
    'OpenAIProvider'
]
