
"""
AI Plugin package for PyCommerce.

This package provides AI text generation capabilities for the PyCommerce platform.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    from pycommerce.plugins.ai.config import load_ai_config, get_ai_providers
    from pycommerce.plugins.ai.providers import get_ai_provider, AIProvider

    def get_ai_provider_instance(tenant_id: Optional[str] = None) -> Optional[AIProvider]:
        """
        Get an instance of the active AI provider.
        
        Args:
            tenant_id: Optional tenant ID for tenant-specific configuration
        
        Returns:
            An AIProvider instance or None if not configured
        """
        try:
            # Load configuration
            config = load_ai_config(tenant_id)
            active_provider = config.get("active_provider")
            provider_config = config.get("provider_config", {})
            
            # Check if we have an API key
            if not provider_config.get("api_key"):
                logger.warning(f"API key for {active_provider} is not configured")
                return None
            
            # Create provider instance
            return get_ai_provider(active_provider, provider_config)
        except Exception as e:
            logger.error(f"Error creating AI provider: {str(e)}")
            return None
            
    # Test the configuration on module load
    test_config = load_ai_config()
    if not test_config or not test_config.get("provider_config", {}).get("api_key"):
        logger.warning("AI configuration loaded but no API key is configured")
    else:
        logger.info(f"AI configuration loaded successfully with provider: {test_config.get('active_provider', 'unknown')}")
            
except ImportError as e:
    logger.error(f"Error importing AI module components: {str(e)}")
except Exception as e:
    logger.error(f"Error initializing AI plugin: {str(e)}")
