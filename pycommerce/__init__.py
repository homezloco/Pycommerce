"""
PyCommerce - A modular Python ecommerce SDK with plugin architecture and FastAPI integration.

This package provides a flexible framework for building ecommerce applications with
support for extensibility through plugins and modern API development using FastAPI.
"""

__version__ = "0.1.0"

# Don't import modules directly at the top level to avoid circular imports
# These will be imported explicitly when needed

# Export main classes for easier imports
__all__ = [
    "PyCommerce",
    "Plugin",
    "PluginManager",
    "PyCommerceError",
]