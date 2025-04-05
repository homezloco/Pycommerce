"""
Plugin configuration model for PyCommerce.

This module provides functionality for storing and retrieving
plugin configuration data in the database, with support for
tenant-specific configurations.
"""

import json
import logging
from typing import Dict, Any, Optional, List, Union
from uuid import UUID

from sqlalchemy import Column, String, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from pycommerce.core.db import Base, SessionLocal
from pycommerce.core.exceptions import ConfigError

logger = logging.getLogger(__name__)


class PluginConfig(Base):
    """
    Database model for storing plugin configurations.
    
    This model allows for both global configurations and
    tenant-specific configurations for plugins.
    """
    __tablename__ = "plugin_configs"
    
    id = Column(String(36), primary_key=True)
    plugin_id = Column(String(50), nullable=False, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    enabled = Column(Boolean, default=True)
    config_data = Column(JSONB, nullable=True)
    created_at = Column(Text, nullable=True)
    updated_at = Column(Text, nullable=True)
    
    # Define a unique constraint for plugin_id and tenant_id to prevent duplicates
    __table_args__ = (
        UniqueConstraint('plugin_id', 'tenant_id', name='uix_plugin_tenant'),
    )
    
    # Relationship with tenant (optional)
    tenant = relationship("Tenant", back_populates="plugin_configs")
    
    def __repr__(self):
        return f"<PluginConfig(plugin_id='{self.plugin_id}', tenant_id='{self.tenant_id}')>"


class PluginConfigManager:
    """
    Manager for plugin configurations.
    
    This class provides methods for storing, retrieving, and
    managing plugin configurations across all tenants.
    """
    
    def get_config(self, plugin_id: str, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration for a plugin.
        
        If tenant_id is specified, it returns the tenant-specific configuration.
        Otherwise, it returns the global configuration.
        
        Args:
            plugin_id: The ID of the plugin
            tenant_id: Optional tenant ID for tenant-specific configurations
            
        Returns:
            Dictionary containing configuration values
            
        Raises:
            ConfigError: If the configuration could not be retrieved
        """
        try:
            with SessionLocal() as session:
                query = session.query(PluginConfig).filter(
                    PluginConfig.plugin_id == plugin_id
                )
                
                if tenant_id:
                    # Get tenant-specific configuration
                    query = query.filter(PluginConfig.tenant_id == str(tenant_id))
                else:
                    # Get global configuration
                    query = query.filter(PluginConfig.tenant_id.is_(None))
                
                config = query.first()
                
                if config and config.config_data:
                    return config.config_data
                
                # If no configuration is found, return an empty dict
                return {}
                
        except Exception as e:
            logger.error(f"Error retrieving configuration for plugin {plugin_id}: {str(e)}")
            raise ConfigError(f"Failed to retrieve plugin configuration: {str(e)}")
    
    def save_config(self, plugin_id: str, config_data: Dict[str, Any], tenant_id: Optional[str] = None) -> bool:
        """
        Save configuration for a plugin.
        
        If tenant_id is specified, it saves as a tenant-specific configuration.
        Otherwise, it saves as the global configuration.
        
        Args:
            plugin_id: The ID of the plugin
            config_data: Dictionary containing configuration values
            tenant_id: Optional tenant ID for tenant-specific configurations
            
        Returns:
            True if the configuration was saved successfully, False otherwise
            
        Raises:
            ConfigError: If the configuration could not be saved
        """
        try:
            with SessionLocal() as session:
                # Look for an existing configuration
                query = session.query(PluginConfig).filter(
                    PluginConfig.plugin_id == plugin_id
                )
                
                if tenant_id:
                    # Get tenant-specific configuration
                    query = query.filter(PluginConfig.tenant_id == str(tenant_id))
                else:
                    # Get global configuration
                    query = query.filter(PluginConfig.tenant_id.is_(None))
                
                config = query.first()
                
                if config:
                    # Update existing configuration
                    config.config_data = config_data
                    config.updated_at = "now()"
                else:
                    # Create new configuration
                    import uuid
                    config = PluginConfig(
                        id=str(uuid.uuid4()),
                        plugin_id=plugin_id,
                        tenant_id=str(tenant_id) if tenant_id else None,
                        config_data=config_data,
                        created_at="now()",
                        updated_at="now()"
                    )
                    session.add(config)
                
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving configuration for plugin {plugin_id}: {str(e)}")
            raise ConfigError(f"Failed to save plugin configuration: {str(e)}")
    
    def set_enabled(self, plugin_id: str, enabled: bool, tenant_id: Optional[str] = None) -> bool:
        """
        Enable or disable a plugin for a specific tenant or globally.
        
        Args:
            plugin_id: The ID of the plugin
            enabled: Whether the plugin should be enabled
            tenant_id: Optional tenant ID for tenant-specific configuration
            
        Returns:
            True if the operation was successful, False otherwise
            
        Raises:
            ConfigError: If the operation failed
        """
        try:
            with SessionLocal() as session:
                # Look for an existing configuration
                query = session.query(PluginConfig).filter(
                    PluginConfig.plugin_id == plugin_id
                )
                
                if tenant_id:
                    # Get tenant-specific configuration
                    query = query.filter(PluginConfig.tenant_id == str(tenant_id))
                else:
                    # Get global configuration
                    query = query.filter(PluginConfig.tenant_id.is_(None))
                
                config = query.first()
                
                if config:
                    # Update existing configuration
                    config.enabled = enabled
                    config.updated_at = "now()"
                else:
                    # Create new configuration with just the enabled flag
                    import uuid
                    config = PluginConfig(
                        id=str(uuid.uuid4()),
                        plugin_id=plugin_id,
                        tenant_id=str(tenant_id) if tenant_id else None,
                        enabled=enabled,
                        created_at="now()",
                        updated_at="now()"
                    )
                    session.add(config)
                
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error setting enabled status for plugin {plugin_id}: {str(e)}")
            raise ConfigError(f"Failed to update plugin status: {str(e)}")
    
    def is_enabled(self, plugin_id: str, tenant_id: Optional[str] = None) -> bool:
        """
        Check if a plugin is enabled for a specific tenant or globally.
        
        Args:
            plugin_id: The ID of the plugin
            tenant_id: Optional tenant ID for tenant-specific configuration
            
        Returns:
            True if the plugin is enabled, False otherwise
            
        Raises:
            ConfigError: If the check failed
        """
        try:
            with SessionLocal() as session:
                query = session.query(PluginConfig).filter(
                    PluginConfig.plugin_id == plugin_id
                )
                
                if tenant_id:
                    # Get tenant-specific configuration
                    query = query.filter(PluginConfig.tenant_id == str(tenant_id))
                else:
                    # Get global configuration
                    query = query.filter(PluginConfig.tenant_id.is_(None))
                
                config = query.first()
                
                if config:
                    return config.enabled
                
                # If no configuration is found, assume the plugin is enabled
                return True
                
        except Exception as e:
            logger.error(f"Error checking enabled status for plugin {plugin_id}: {str(e)}")
            raise ConfigError(f"Failed to check plugin status: {str(e)}")
    
    def list_configs(self, plugin_id: Optional[str] = None, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all configurations, optionally filtered by plugin_id or tenant_id.
        
        Args:
            plugin_id: Optional plugin ID to filter by
            tenant_id: Optional tenant ID to filter by
            
        Returns:
            List of dictionaries containing configuration information
            
        Raises:
            ConfigError: If the operation failed
        """
        try:
            with SessionLocal() as session:
                query = session.query(PluginConfig)
                
                if plugin_id:
                    query = query.filter(PluginConfig.plugin_id == plugin_id)
                
                if tenant_id:
                    query = query.filter(PluginConfig.tenant_id == str(tenant_id))
                
                configs = query.all()
                
                result = []
                for config in configs:
                    result.append({
                        "plugin_id": config.plugin_id,
                        "tenant_id": config.tenant_id,
                        "enabled": config.enabled,
                        "config_data": config.config_data or {}
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Error listing plugin configurations: {str(e)}")
            raise ConfigError(f"Failed to list plugin configurations: {str(e)}")
    
    def delete_config(self, plugin_id: str, tenant_id: Optional[str] = None) -> bool:
        """
        Delete configuration for a plugin.
        
        Args:
            plugin_id: The ID of the plugin
            tenant_id: Optional tenant ID for tenant-specific configurations
            
        Returns:
            True if the configuration was deleted successfully, False otherwise
            
        Raises:
            ConfigError: If the configuration could not be deleted
        """
        try:
            with SessionLocal() as session:
                query = session.query(PluginConfig).filter(
                    PluginConfig.plugin_id == plugin_id
                )
                
                if tenant_id:
                    # Delete tenant-specific configuration
                    query = query.filter(PluginConfig.tenant_id == str(tenant_id))
                else:
                    # Delete global configuration
                    query = query.filter(PluginConfig.tenant_id.is_(None))
                
                count = query.delete()
                session.commit()
                
                return count > 0
                
        except Exception as e:
            logger.error(f"Error deleting configuration for plugin {plugin_id}: {str(e)}")
            raise ConfigError(f"Failed to delete plugin configuration: {str(e)}")