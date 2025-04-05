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
"""
Core functionality for PyCommerce.

This package provides the foundational components of the PyCommerce SDK.
"""

# Import key components to make them available at the package level
from .db import Base, engine, SessionLocal, get_db
from .exceptions import PyCommerceError
