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

def get_plugin_registry():
    """
    Get the global plugin registry.
    
    Returns:
        An object with methods to access different plugin types
    """
    from pycommerce import payment_plugins, shipping_plugins
    
    class PluginRegistry:
        def get_payment_plugin(self, name):
            """Get a payment plugin by name"""
            # Check for plugin by exact name
            plugin = payment_plugins._plugins.get(name)
            if plugin:
                return plugin
                
            # If not found, try to find a plugin whose name contains the provided name
            for plugin_name, plugin_instance in payment_plugins._plugins.items():
                if name.lower() in plugin_name.lower():
                    return plugin_instance
            
            return None
            
        def get_shipping_plugin(self, name):
            """Get a shipping plugin by name"""
            # Check for plugin by exact name
            plugin = shipping_plugins._plugins.get(name)
            if plugin:
                return plugin
                
            # Special case for 'standard' -> 'standard_shipping'
            if name == 'standard' and 'standard_shipping' in shipping_plugins._plugins:
                return shipping_plugins._plugins['standard_shipping']
                
            # If not found, try to find a plugin whose name contains the provided name
            for plugin_name, plugin_instance in shipping_plugins._plugins.items():
                if name.lower() in plugin_name.lower():
                    return plugin_instance
            
            return None
            
        def list_payment_plugins(self):
            """List all registered payment plugins"""
            return list(payment_plugins._plugins.values())
            
        def list_shipping_plugins(self):
            """List all registered shipping plugins"""
            return list(shipping_plugins._plugins.values())
    
    return PluginRegistry()