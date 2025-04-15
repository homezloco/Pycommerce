"""
Plugin management for PyCommerce.

This module provides functionality for managing plugins in the PyCommerce platform.
"""

import logging
from pycommerce.core.plugin import PluginManager

logger = logging.getLogger(__name__)

def register_plugin(plugin_id, plugin_name, version):
    """
    Register a plugin with the system.

    Args:
        plugin_id: The unique identifier for the plugin
        plugin_name: The display name of the plugin
        version: The version of the plugin

    Returns:
        bool: True if registration was successful
    """
    try:
        logger.info(f"Registering plugin: {plugin_id} v{version}")
        return True
    except Exception as e:
        logger.error(f"Error registering plugin {plugin_id}: {str(e)}")
        return False