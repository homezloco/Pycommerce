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
from fastapi import FastAPI, APIRouter

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
