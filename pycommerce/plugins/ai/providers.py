"""
AI provider implementations for PyCommerce.

This module provides adapters for different AI service providers.
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)

# Dictionary of registered AI providers
_providers = {}

def register_provider(name: str, provider_class: Any):
    """
    Register an AI provider.

    Args:
        name: Provider name/identifier
        provider_class: Provider class or factory
    """
    global _providers
    _providers[name] = provider_class
    logger.info(f"Registered AI provider: {name}")

def get_provider(name: str) -> Optional[Any]:
    """
    Get an AI provider by name.

    Args:
        name: Provider name/identifier

    Returns:
        Provider instance or None if not found
    """
    if name not in _providers:
        try:
            # Import and register providers dynamically
            if name == 'openai':
                from .openai_provider import OpenAIProvider
                register_provider('openai', OpenAIProvider)
            elif name == 'mock':
                from .mock_provider import MockAIProvider
                register_provider('mock', MockAIProvider)
        except ImportError as e:
            logger.warning(f"Could not import provider {name}: {str(e)}")
            # Register a fallback mock provider if the real one isn't available
            register_provider(name, MockAIProvider)

    provider_class = _providers.get(name)
    if provider_class:
        # Get configuration for this provider
        from .config import get_ai_settings
        config = get_ai_settings().get(name, {})
        return provider_class(config)

    return None

# Base class for AI providers
class BaseAIProvider:
    """Base class for AI service providers."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the provider.

        Args:
            config: Provider configuration
        """
        self.config = config

    def generate_content(self, prompt: str, options: Dict[str, Any] = None) -> str:
        """
        Generate content based on a prompt.

        Args:
            prompt: Text prompt for content generation
            options: Additional options for generation

        Returns:
            Generated content
        """
        raise NotImplementedError("Subclasses must implement generate_content")

    def generate_completion(self, messages: List[Dict[str, str]], options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a completion based on a conversation.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            options: Additional options for generation

        Returns:
            Generated completion response
        """
        raise NotImplementedError("Subclasses must implement generate_completion")

# Mock AI provider for testing and development
class MockAIProvider(BaseAIProvider):
    """Mock AI provider for testing without external API dependencies."""

    def generate_content(self, prompt: str, options: Dict[str, Any] = None) -> str:
        """
        Generate mock content based on a prompt.

        Args:
            prompt: Text prompt for content generation
            options: Additional options for generation

        Returns:
            Generated mock content
        """
        options = options or {}

        if "product" in prompt.lower():
            return "This is a great product with excellent features."
        elif "description" in prompt.lower():
            return "This is a detailed description of the item showcasing its benefits and features."
        else:
            return f"Mock AI response to: {prompt[:50]}..."

    def generate_completion(self, messages: List[Dict[str, str]], options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a mock completion based on a conversation.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            options: Additional options for generation

        Returns:
            Generated mock completion response
        """
        options = options or {}

        # Extract the last user message
        last_message = next((m for m in reversed(messages) if m.get('role') == 'user'), None)

        if last_message:
            content = last_message.get('content', '')
            response = self.generate_content(content, options)
        else:
            response = "I don't have enough context to provide a helpful response."

        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": response
                    }
                }
            ]
        }

# Register the mock provider by default
register_provider('mock', MockAIProvider)