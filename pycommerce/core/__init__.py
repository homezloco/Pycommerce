
"""
Core functionality for the PyCommerce platform.

This package contains the core modules that power the PyCommerce platform,
including database configuration, plugin architecture, and base classes.
"""

from pycommerce.core.db import Base, init_db, get_db, close_db
from pycommerce.core.plugin import PluginManager, Plugin, PluginConfigManager
from pycommerce.core.exceptions import PyCommerceError

__all__ = [
    'Base',
    'init_db',
    'get_db',
    'close_db',
    'Plugin',
    'PluginManager',
    'PluginConfigManager',
    'PyCommerceError',
]
