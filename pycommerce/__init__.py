"""
PyCommerce - A modular Python ecommerce SDK with plugin architecture and FastAPI integration.

This package provides a flexible framework for building ecommerce applications with
support for extensibility through plugins and modern API development using FastAPI.
"""

__version__ = "0.1.0"

from pycommerce.core.base import PyCommerce
from pycommerce.core.plugin import Plugin, PluginManager
from pycommerce.core.exceptions import (
    PyCommerceError,
    ProductError,
    CartError,
    OrderError,
    PaymentError,
    ShippingError,
    PluginError,
)

# Export main classes for easier imports
__all__ = [
    "PyCommerce",
    "Plugin",
    "PluginManager",
    "PyCommerceError",
    "ProductError",
    "CartError",
    "OrderError",
    "PaymentError",
    "ShippingError",
    "PluginError",
]
