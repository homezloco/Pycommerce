"""
AI providers configuration helper functions.

This module provides functions to load and save AI provider configurations,
as well as define available AI providers.
"""

import os
import logging
from typing import Dict, Any, List, Optional

from pycommerce.models.plugin_config import PluginConfigManager

logger = logging.getLogger(__name__)

# Default OpenAI API key from environment (for development)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Define available AI providers
def get_ai_providers() -> List[Dict[str, Any]]:
    """
    Get a list of available AI providers with their configuration fields.
    
    Returns:
        List of provider configuration objects
    """
    return [
        {
            "id": "openai",
            "name": "OpenAI",
            "description": "AI models from OpenAI including GPT-3.5 and GPT-4",
            "icon": "openai-icon.png",
            "fields": [
                {
                    "id": "api_key",
                    "name": "API Key",
                    "type": "password",
                    "required": True,
                    "description": "Your OpenAI API key"
                },
                {
                    "id": "model",
                    "name": "Model",
                    "type": "select",
                    "options": [
                        {"value": "gpt-3.5-turbo", "label": "GPT-3.5 Turbo"},
                        {"value": "gpt-4", "label": "GPT-4"}
                    ],
                    "default": "gpt-3.5-turbo",
                    "required": True,
                    "description": "The OpenAI model to use"
                },
                {
                    "id": "temperature",
                    "name": "Temperature",
                    "type": "number",
                    "min": 0,
                    "max": 1,
                    "step": 0.1,
                    "default": 0.7,
                    "required": False,
                    "description": "Controls randomness (0 = deterministic, 1 = creative)"
                }
            ]
        },
        {
            "id": "gemini",
            "name": "Google Gemini",
            "description": "Google's Gemini AI models",
            "icon": "gemini-icon.png",
            "fields": [
                {
                    "id": "api_key",
                    "name": "API Key",
                    "type": "password",
                    "required": True,
                    "description": "Your Google Gemini API key"
                },
                {
                    "id": "model",
                    "name": "Model",
                    "type": "select",
                    "options": [
                        {"value": "gemini-pro", "label": "Gemini Pro"}
                    ],
                    "default": "gemini-pro",
                    "required": True,
                    "description": "The Gemini model to use"
                }
            ]
        },
        {
            "id": "deepseek",
            "name": "DeepSeek",
            "description": "DeepSeek AI large language models",
            "icon": "deepseek-icon.png",
            "fields": [
                {
                    "id": "api_key",
                    "name": "API Key", 
                    "type": "password",
                    "required": True,
                    "description": "Your DeepSeek API key"
                },
                {
                    "id": "model",
                    "name": "Model",
                    "type": "select",
                    "options": [
                        {"value": "deepseek-chat", "label": "DeepSeek Chat"}
                    ],
                    "default": "deepseek-chat",
                    "required": True,
                    "description": "The DeepSeek model to use"
                }
            ]
        },
        {
            "id": "openrouter",
            "name": "OpenRouter",
            "description": "Access to multiple AI models through a single API",
            "icon": "openrouter-icon.png",
            "fields": [
                {
                    "id": "api_key",
                    "name": "API Key",
                    "type": "password",
                    "required": True,
                    "description": "Your OpenRouter API key"
                },
                {
                    "id": "model",
                    "name": "Model",
                    "type": "select",
                    "options": [
                        {"value": "openai/gpt-3.5-turbo", "label": "OpenAI GPT-3.5 Turbo"},
                        {"value": "openai/gpt-4", "label": "OpenAI GPT-4"},
                        {"value": "anthropic/claude-3-opus", "label": "Anthropic Claude 3 Opus"},
                        {"value": "anthropic/claude-3-sonnet", "label": "Anthropic Claude 3 Sonnet"},
                        {"value": "mistralai/mistral-large", "label": "Mistral Large"},
                        {"value": "meta-llama/llama-3-70b-instruct", "label": "Llama 3 70B Instruct"}
                    ],
                    "default": "openai/gpt-3.5-turbo",
                    "required": True,
                    "description": "The AI model to use through OpenRouter"
                }
            ]
        }
    ]

def load_ai_config(tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Load AI configuration for a tenant or globally.
    
    Args:
        tenant_id: Optional tenant ID for tenant-specific configuration
    
    Returns:
        AI configuration dictionary
    """
    config_manager = PluginConfigManager()
    
    # Get active provider
    active_provider_config = {}
    try:
        active_provider_config = config_manager.get_config("ai_active_provider", tenant_id) or {}
    except Exception as e:
        logger.warning(f"Error loading active AI provider config: {str(e)}")
    
    # Default to OpenAI if no active provider is set
    active_provider = active_provider_config.get("provider", "openai") 
    
    # Get provider configuration
    provider_config = {}
    try:
        provider_config = config_manager.get_config(f"ai_{active_provider}", tenant_id) or {}
    except Exception as e:
        logger.warning(f"Error loading AI provider config: {str(e)}")
    
    # If no API key is configured and we're using OpenAI, use the environment variable
    if active_provider == "openai" and not provider_config.get("api_key") and OPENAI_API_KEY:
        provider_config["api_key"] = OPENAI_API_KEY
        logger.info("Using OpenAI API key from environment")
    
    return {
        "active_provider": active_provider,
        "provider_config": provider_config
    }

def get_ai_provider_instance(tenant_id: Optional[str] = None):
    """
    Get an instance of the active AI provider.
    
    Args:
        tenant_id: Optional tenant ID for tenant-specific configuration
    
    Returns:
        An AIProvider instance
        
    Raises:
        ValueError: If the provider configuration is incomplete
    """
    from pycommerce.plugins.ai.providers import get_ai_provider
    
    # Load configuration
    config = load_ai_config(tenant_id)
    active_provider = config["active_provider"]
    provider_config = config["provider_config"]
    
    # Check if we have an API key
    if not provider_config.get("api_key"):
        raise ValueError(f"API key for {active_provider} is not configured")
    
    # Create provider instance
    try:
        return get_ai_provider(active_provider, provider_config)
    except Exception as e:
        logger.error(f"Error creating AI provider: {str(e)}")
        raise ValueError(f"Failed to initialize AI provider: {str(e)}")