"""
Plugin system for PyCommerce SDK.

This module provides the base Plugin class and PluginManager for
extending the SDK's functionality through plugins.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type, Any, Callable
import importlib
import inspect
import os
from fastapi import FastAPI, APIRouter
import json

logger = logging.getLogger("pycommerce.plugins")

class Plugin(ABC):
    """
    Base class for all PyCommerce plugins.
    
    All plugins must inherit from this class and implement the required methods.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the plugin."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Return the version of the plugin."""
        pass
    
    @property
    def description(self) -> str:
        """Return the description of the plugin."""
        return "No description provided"
    
    def initialize(self) -> None:
        """
        Initialize the plugin.
        
        Called when the plugin is registered with the PluginManager.
        Override this method to perform any initialization.
        """
        pass
    
    def get_router(self) -> Optional[APIRouter]:
        """
        Get the FastAPI router for this plugin.
        
        Override this method to provide a FastAPI router with
        custom endpoints for this plugin.
        
        Returns:
            An APIRouter instance or None if the plugin doesn't provide API endpoints
        """
        return None
    
    def __str__(self) -> str:
        return f"{self.name} v{self.version}"


class PluginManager:
    """
    Manages the loading and registration of plugins for PyCommerce.
    """
    
    def __init__(self, plugin_type=None):
        """
        Initialize a new PluginManager.
        
        Args:
            plugin_type: Optional type of plugins this manager handles (e.g., 'payment', 'shipping')
        """
        self._plugins: Dict[str, Plugin] = {}
        self.plugin_type = plugin_type
    
    def register(self, plugin: Plugin) -> None:
        """
        Register a plugin with the manager.
        
        Args:
            plugin: The plugin instance to register
            
        Raises:
            PluginError: If a plugin with the same name is already registered
        """
        from pycommerce.core.exceptions import PluginError
        
        if plugin.name in self._plugins:
            raise PluginError(f"Plugin '{plugin.name}' is already registered")
        
        logger.info(f"Registering plugin: {plugin}")
        self._plugins[plugin.name] = plugin
        plugin.initialize()
    
    def unregister(self, name: str) -> None:
        """
        Unregister a plugin by name.
        
        Args:
            name: The name of the plugin to unregister
            
        Raises:
            PluginError: If the plugin is not registered
        """
        from pycommerce.core.exceptions import PluginError
        
        if name not in self._plugins:
            raise PluginError(f"Plugin '{name}' is not registered")
        
        logger.info(f"Unregistering plugin: {name}")
        del self._plugins[name]
    
    def get(self, name: str) -> Plugin:
        """
        Get a plugin by name.
        
        Args:
            name: The name of the plugin to get
            
        Returns:
            The plugin instance
            
        Raises:
            PluginError: If the plugin is not registered
        """
        from pycommerce.core.exceptions import PluginError
        
        if name not in self._plugins:
            raise PluginError(f"Plugin '{name}' is not registered")
        
        return self._plugins[name]
    
    def list_plugins(self) -> List[Dict[str, str]]:
        """
        List all registered plugins.
        
        Returns:
            A list of dictionaries containing plugin information
        """
        return [
            {
                "name": plugin.name,
                "version": plugin.version,
                "description": plugin.description
            }
            for plugin in self._plugins.values()
        ]
    
    def load_plugin_from_module(self, module_name: str) -> None:
        """
        Load plugins from a Python module.
        
        This method will look for classes that extend Plugin in the
        specified module and register them.
        
        Args:
            module_name: The name of the module to load plugins from
            
        Raises:
            ImportError: If the module cannot be imported
            PluginError: If no plugins are found in the module
        """
        from pycommerce.core.exceptions import PluginError
        
        try:
            module = importlib.import_module(module_name)
        except ImportError as e:
            logger.error(f"Failed to import module {module_name}: {e}")
            raise
        
        plugins_registered = 0
        
        # Look for plugin classes in the module
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, Plugin) and obj != Plugin:
                # Instantiate and register the plugin
                try:
                    plugin = obj()
                    self.register(plugin)
                    plugins_registered += 1
                except Exception as e:
                    logger.error(f"Failed to instantiate plugin {name}: {e}")
        
        if plugins_registered == 0:
            raise PluginError(f"No plugins found in module {module_name}")
        
        logger.info(f"Loaded {plugins_registered} plugins from module {module_name}")
    
    def register_routes(self, app: FastAPI) -> None:
        """
        Register API routes from all plugins.
        
        Args:
            app: The FastAPI application to register routes with
        """
        for name, plugin in self._plugins.items():
            router = plugin.get_router()
            if router:
                prefix = f"/api/plugins/{name}"
                app.include_router(router, prefix=prefix, tags=[f"plugin:{name}"])
                logger.debug(f"Registered API routes for plugin {name} at {prefix}")


# ----- Plugin Discovery Functions -----

class PluginConfigManager:
    """
    Manages plugin configuration storage and retrieval.
    
    This class provides methods to save and retrieve plugin configurations,
    which can be tenant-specific or global.
    """
    
    def __init__(self, config_dir=None):
        """
        Initialize the plugin configuration manager.
        
        Args:
            config_dir: Directory to store configuration files (optional)
        """
        self.config_dir = config_dir
        if not self.config_dir:
            # Use a memory-based configuration store for now
            self._config_store = {}
    
    def save_config(self, plugin_id: str, tenant_id: str, config: Dict[str, Any]) -> None:
        """
        Save plugin configuration.
        
        Args:
            plugin_id: ID of the plugin
            tenant_id: ID of the tenant (or None for global config)
            config: Configuration dictionary to save
        """
        key = f"{plugin_id}:{tenant_id}" if tenant_id else plugin_id
        
        if self.config_dir:
            # File-based storage (not implemented yet)
            logger.warning("File-based configuration storage not implemented yet")
            
        # Memory-based storage
        self._config_store[key] = config
        logger.debug(f"Saved configuration for plugin {plugin_id}, tenant {tenant_id}")
    
    def get_config(self, plugin_id: str, tenant_id: str = None) -> Dict[str, Any]:
        """
        Get plugin configuration.
        
        Args:
            plugin_id: ID of the plugin
            tenant_id: ID of the tenant (or None for global config)
            
        Returns:
            Configuration dictionary, or empty dict if not found
        """
        key = f"{plugin_id}:{tenant_id}" if tenant_id else plugin_id
        
        if self.config_dir:
            # File-based storage (not implemented yet)
            logger.warning("File-based configuration storage not implemented yet")
            return {}
            
        # Memory-based storage
        return self._config_store.get(key, {})
    
    def delete_config(self, plugin_id: str, tenant_id: str = None) -> None:
        """
        Delete plugin configuration.
        
        Args:
            plugin_id: ID of the plugin
            tenant_id: ID of the tenant (or None for global config)
        """
        key = f"{plugin_id}:{tenant_id}" if tenant_id else plugin_id
        
        if self.config_dir:
            # File-based storage (not implemented yet)
            logger.warning("File-based configuration storage not implemented yet")
            
        # Memory-based storage
        if key in self._config_store:
            del self._config_store[key]
            logger.debug(f"Deleted configuration for plugin {plugin_id}, tenant {tenant_id}")


def get_available_plugins() -> List[Dict[str, Any]]:
    """
    Get a list of all available plugins in the system.
    
    This function provides information about both installed plugins and built-in plugins.
    
    Returns:
        A list of dictionaries containing plugin information:
        - id: Plugin identifier (used in URLs and configurations)
        - name: Display name of the plugin
        - description: Plugin description
        - type: Plugin type (payment, shipping, etc.)
        - version: Plugin version string
        - enabled: Whether the plugin is currently enabled
        - configured: Whether the plugin is properly configured
        - icon: Optional Bootstrap icon class for the plugin
    """
    from pycommerce.plugins.payment.config import STRIPE_API_KEY, STRIPE_ENABLED
    from pycommerce.plugins.payment.config import PAYPAL_CLIENT_ID, PAYPAL_ENABLED
    
    # Here we manually define our available plugins
    # In a more sophisticated implementation, this would be discovered dynamically
    plugins = [
        {
            "id": "stripe",
            "name": "Stripe Payments",
            "description": "Process credit card payments with Stripe",
            "type": "payment",
            "version": "1.0.0",
            "enabled": STRIPE_ENABLED,
            "configured": bool(STRIPE_API_KEY),
            "author": "PyCommerce Team",
            "icon": "bi-credit-card"
        },
        {
            "id": "paypal",
            "name": "PayPal Payments",
            "description": "Accept payments via PayPal",
            "type": "payment",
            "version": "1.0.0",
            "enabled": PAYPAL_ENABLED,
            "configured": bool(PAYPAL_CLIENT_ID),
            "author": "PyCommerce Team",
            "icon": "bi-paypal"
        },
        {
            "id": "standard-shipping",
            "name": "Standard Shipping",
            "description": "Basic shipping rate calculations",
            "type": "shipping",
            "version": "1.0.0",
            "enabled": True,
            "configured": True,
            "author": "PyCommerce Team",
            "icon": "bi-truck"
        }
    ]
    
    return plugins
