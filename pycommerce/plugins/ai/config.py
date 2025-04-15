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

# Initialize the plugin config manager
plugin_config_manager = PluginConfigManager()

def get_active_provider() -> Optional[str]:
    """Get the currently active AI provider.

    Returns:
        The name of the active provider or None if not configured
    """
    try:
        config = plugin_config_manager.get_config("ai_active_provider")
        if config and isinstance(config, dict) and "provider" in config:
            return config["provider"]
    except Exception as e:
        logger.warning(f"Error loading active AI provider config: {str(e)}")

    return "openai"  # Default provider

def get_provider_config(provider_name: str) -> Dict[str, Any]:
    """Get configuration for a specific AI provider.

    Args:
        provider_name: The name of the provider

    Returns:
        Provider configuration dictionary
    """
    try:
        config = plugin_config_manager.get_config(f"ai_provider_{provider_name}")
        if config and isinstance(config, dict):
            return config
    except Exception as e:
        logger.warning(f"Error loading AI provider config for {provider_name}: {str(e)}")

    return {"api_key": "", "model": "gpt-3.5-turbo"}

def save_provider_config(provider_name: str, config: Dict[str, Any]) -> bool:
    """Save configuration for a specific AI provider.

    Args:
        provider_name: The name of the provider
        config: Provider configuration dictionary

    Returns:
        True if successful, False otherwise
    """
    try:
        return plugin_config_manager.save_config(f"ai_provider_{provider_name}", config)
    except Exception as e:
        logger.error(f"Error saving AI provider config for {provider_name}: {str(e)}")
        return False

def set_active_provider(provider_name: str) -> bool:
    """Set the active AI provider.

    Args:
        provider_name: The name of the provider to make active

    Returns:
        True if successful, False otherwise
    """
    try:
        return plugin_config_manager.save_config("ai_active_provider", {"provider": provider_name})
    except Exception as e:
        logger.error(f"Error setting active AI provider: {str(e)}")
        return False

def load_ai_config(tenant_id: Optional[str] = None) -> Dict[str, Any]:
    active_provider = get_active_provider()
    provider_config = get_provider_config(active_provider)

    # If no API key is configured and we're using OpenAI, use the environment variable
    if active_provider == "openai" and not provider_config.get("api_key") and OPENAI_API_KEY:
        provider_config["api_key"] = OPENAI_API_KEY
        logger.info("Using OpenAI API key from environment")

    return {
        "active_provider": active_provider,
        "provider_config": provider_config
    }

def get_ai_provider_instance(tenant_id: Optional[str] = None):
    from pycommerce.plugins.ai.providers import get_ai_provider

    config = load_ai_config(tenant_id)
    active_provider = config["active_provider"]
    provider_config = config["provider_config"]

    if not provider_config.get("api_key"):
        raise ValueError(f"API key for {active_provider} is not configured")

    try:
        return get_ai_provider(active_provider, provider_config)
    except Exception as e:
        logger.error(f"Error creating AI provider: {str(e)}")
        raise ValueError(f"Failed to initialize AI provider: {str(e)}")