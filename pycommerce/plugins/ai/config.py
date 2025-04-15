"""
Configuration for AI services.
"""
import logging
import os
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

# Default AI configuration
DEFAULT_AI_CONFIG = {
    "provider": "mock",  # Use 'mock' as default for testing
    "mock": {
        "enabled": True,
    },
    "openai": {
        "enabled": False,
        "api_key": "",
        "model": "gpt-3.5-turbo",
    }
}

# Global AI configuration
_ai_config = None

def init_ai_config() -> Dict[str, Any]:
    """Initialize AI configuration from environment or defaults."""
    global _ai_config

    if _ai_config is not None:
        return _ai_config

    config = DEFAULT_AI_CONFIG.copy()

    # Override with environment variables if present
    if os.environ.get("AI_PROVIDER"):
        config["provider"] = os.environ.get("AI_PROVIDER")

    if os.environ.get("OPENAI_API_KEY"):
        config["openai"]["api_key"] = os.environ.get("OPENAI_API_KEY")
        config["openai"]["enabled"] = True
        # If we have an OpenAI key, set it as the provider
        if config["provider"] == "mock":
            config["provider"] = "openai"

    _ai_config = config
    logger.info(f"AI configuration initialized with provider: {config['provider']}")
    return config

def get_ai_config() -> Dict[str, Any]:
    """Get the current AI configuration."""
    global _ai_config

    if _ai_config is None:
        return init_ai_config()

    return _ai_config

def update_ai_config(new_config: Dict[str, Any]) -> Dict[str, Any]:
    """Update the AI configuration."""
    global _ai_config

    if _ai_config is None:
        _ai_config = DEFAULT_AI_CONFIG.copy()

    # Update configuration
    _ai_config.update(new_config)

    logger.info(f"AI configuration updated with provider: {_ai_config['provider']}")
    return _ai_config

def get_provider_config(provider_name: str) -> Optional[Dict[str, Any]]:
    """Get configuration for a specific provider."""
    config = get_ai_config()

    if provider_name in config:
        return config[provider_name]

    return None