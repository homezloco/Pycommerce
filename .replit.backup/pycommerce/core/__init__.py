"""
Core functionality for the PyCommerce SDK.

This package contains the fundamental components and base classes
that power the PyCommerce SDK, including the main PyCommerce class,
plugin infrastructure, and core exceptions.
"""

from pycommerce.core.base import PyCommerce
from pycommerce.core.plugin import Plugin, PluginManager
from pycommerce.core.exceptions import PyCommerceError

__all__ = ["PyCommerce", "Plugin", "PluginManager", "PyCommerceError"]
