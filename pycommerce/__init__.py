"""
PyCommerce: A Python-based e-commerce platform.

This package provides a flexible and extensible e-commerce platform
built on Python, with support for multiple tenants and plugins.
"""

import os
import logging
from importlib import import_module

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import core modules
from pycommerce.core.db import Base, init_db
from pycommerce.core.plugin import PluginManager

# Import models to register them with Base
# We'll do this inside init_db() to avoid circular imports

# Create plugin managers
payment_plugins = PluginManager()
payment_plugins.plugin_type = "payment"
shipping_plugins = PluginManager()
shipping_plugins.plugin_type = "shipping"

# Initialize plugins from environment variables
def initialize_plugins():
    """Initialize plugins based on environment variables."""
    # Get enabled payment plugins
    payment_plugin_list = os.getenv("ENABLED_PAYMENT_PLUGINS", "stripe,paypal").split(",")
    for plugin_name in payment_plugin_list:
        plugin_name = plugin_name.strip()
        if not plugin_name:
            continue

        try:
            # Import the plugin module
            plugin_module = import_module(f"pycommerce.plugins.payment.{plugin_name}")
            # Get the plugin class - corrected to handle capitalization
            plugin_class = getattr(plugin_module, f"{plugin_name.capitalize()}PaymentPlugin")
            # Register the plugin
            payment_plugins.register(plugin_class())
            logger.info(f"Registered payment plugin: {plugin_name}")
        except (ImportError, AttributeError) as e:
            logger.warning(f"Failed to load payment plugin '{plugin_name}': {e}")

    # Get enabled shipping plugins
    shipping_plugin_list = os.getenv("ENABLED_SHIPPING_PLUGINS", "standard").split(",")
    for plugin_name in shipping_plugin_list:
        plugin_name = plugin_name.strip()
        if not plugin_name:
            continue

        try:
            # Import the plugin module
            plugin_module = import_module(f"pycommerce.plugins.shipping.{plugin_name}")
            # Get the plugin class
            plugin_class = getattr(plugin_module, f"{plugin_name.title()}ShippingPlugin")
            # Register the plugin
            shipping_plugins.register(plugin_class())
            logger.info(f"Registered shipping plugin: {plugin_name}")
        except (ImportError, AttributeError) as e:
            logger.warning(f"Failed to load shipping plugin '{plugin_name}': {e}")

# Initialize plugins
initialize_plugins()

__all__ = [
    'Base',
    'init_db',
    'payment_plugins',
    'shipping_plugins',
]