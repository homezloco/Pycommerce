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
"""
AI configuration module for PyCommerce.

This module manages the configuration for AI services used by the platform.
"""
import logging
from typing import Dict, Optional, Any, List
import os
import json

from pycommerce.core.db import SessionLocal
from pycommerce.models.plugin_config import PluginConfigManager

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "enabled": False,
    "provider": "openai",
    "api_key": "",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 1024,
    "services": {
        "content_generation": True,
        "product_description": True,
        "customer_support": False,
        "recommendations": True
    }
}

class AIConfigService:
    """Service for managing AI configuration."""
    
    def __init__(self):
        """Initialize the AI configuration service."""
        self.session = SessionLocal()
        self.config_manager = PluginConfigManager()
        self.config_loaded = False
        self.config = DEFAULT_CONFIG.copy()
        self._load_config()
        
    def _load_config(self):
        """Load AI configuration from the database."""
        try:
            # Try to get AI config from database
            plugin_config = self.config_manager.get_config("ai")
            
            if plugin_config:
                self.config = plugin_config
                self.config_loaded = True
                logger.info("AI configuration loaded successfully")
            else:
                # If no config exists, create a default one
                logger.warning("No AI configuration found, using defaults")
                self.config_manager.save_config("ai", DEFAULT_CONFIG)
                self.config = DEFAULT_CONFIG.copy()
                self.config_loaded = True
        except Exception as e:
            logger.error(f"Error loading AI configuration: {str(e)}")
            # Fall back to default config
            self.config = DEFAULT_CONFIG.copy()
            
    def get_config(self) -> Dict[str, Any]:
        """Get the current AI configuration."""
        if not self.config_loaded:
            self._load_config()
        return self.config
    
    def update_config(self, config_data: Dict[str, Any]) -> bool:
        """Update the AI configuration."""
        try:
            # Merge with existing config
            updated_config = {**self.config, **config_data}
            # Save to database
            self.config_manager.save_plugin_config("ai", updated_config)
            # Update local config
            self.config = updated_config
            return True
        except Exception as e:
            logger.error(f"Error updating AI configuration: {str(e)}")
            return False
    
    def is_enabled(self) -> bool:
        """Check if AI features are enabled."""
        return self.config.get("enabled", False)
    
    def get_api_key(self) -> str:
        """Get the API key for the AI provider."""
        # First check for environment variable
        env_key = os.environ.get("AI_API_KEY", "")
        if env_key:
            return env_key
        # Fall back to stored key
        return self.config.get("api_key", "")
    
    def get_model(self) -> str:
        """Get the AI model to use."""
        return self.config.get("model", DEFAULT_CONFIG["model"])
    
    def is_service_enabled(self, service_name: str) -> bool:
        """Check if a specific AI service is enabled."""
        services = self.config.get("services", {})
        return services.get(service_name, False)

# Create a singleton instance
ai_config_service = AIConfigService()

def get_ai_config_service() -> AIConfigService:
    """Get the AI configuration service instance."""
    return ai_config_service
