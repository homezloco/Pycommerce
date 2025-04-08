"""
Plugin configuration database model for PyCommerce.

This module imports the PluginConfig model from the centralized db_registry.
"""

import logging

# Import from the central registry to avoid duplicate model definitions
from pycommerce.models.db_registry import PluginConfig

logger = logging.getLogger(__name__)