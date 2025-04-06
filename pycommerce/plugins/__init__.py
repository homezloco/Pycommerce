"""
Plugin packages for PyCommerce SDK.

This package contains built-in plugins for the PyCommerce SDK,
organized by functionality type.
"""

# Import built-in plugins for easier access
from pycommerce.plugins.payment.stripe import StripePaymentPlugin
from pycommerce.plugins.shipping.standard import StandardShippingPlugin

# Import plugin manager
from pycommerce import payment_plugins, shipping_plugins

__all__ = [
    "StripePaymentPlugin",
    "StandardShippingPlugin",
    "get_plugin_registry",
]

# Plugin registry access function
def get_plugin_registry():
    """
    Get the global plugin registry.
    
    Returns:
        An object with methods to access different plugin types
    """
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
