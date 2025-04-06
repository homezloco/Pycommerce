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
            return payment_plugins._plugins.get(name)
            
        def get_shipping_plugin(self, name):
            """Get a shipping plugin by name"""
            return shipping_plugins._plugins.get(name)
            
        def list_payment_plugins(self):
            """List all registered payment plugins"""
            return list(payment_plugins._plugins.values())
            
        def list_shipping_plugins(self):
            """List all registered shipping plugins"""
            return list(shipping_plugins._plugins.values())
    
    return PluginRegistry()
