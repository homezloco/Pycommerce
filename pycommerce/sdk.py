"""
SDK for PyCommerce.

This module provides an SDK for integrating PyCommerce into other applications.
It serves as a compatibility layer and API facade.
"""

import logging
from typing import List, Optional, Dict, Any, Union
from uuid import UUID

from pycommerce.models.tenant import TenantManager, TenantDTO
from pycommerce.models.product import ProductManager
from pycommerce.core.db import SessionLocal

# Configure logging
logger = logging.getLogger(__name__)

class AppTenantManager:
    """
    Application-level tenant manager.
    
    This class provides a robust tenant manager with enhanced error handling
    and fallback mechanisms for the application layer.
    """
    
    def __init__(self):
        """Initialize a new AppTenantManager."""
        self.manager = TenantManager()
        
    def get_all(self) -> List[TenantDTO]:
        """
        Get all tenants with enhanced error handling.
        
        Returns:
            List of tenant DTOs, empty list if none found or error occurs
        """
        try:
            return self.manager.list()
        except Exception as e:
            logger.error(f"Error getting all tenants: {str(e)}")
            return []
            
    def get(self, tenant_id: str) -> Optional[TenantDTO]:
        """
        Get a tenant by ID with enhanced error handling.
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            Tenant DTO if found, None otherwise
        """
        try:
            return self.manager.get(tenant_id)
        except Exception as e:
            logger.error(f"Error getting tenant with ID {tenant_id}: {str(e)}")
            # Try to get by slug as fallback
            try:
                return self.get_by_slug(tenant_id)
            except:
                pass
            return None
            
    def get_by_slug(self, slug: str) -> Optional[TenantDTO]:
        """
        Get a tenant by slug with enhanced error handling.
        
        Args:
            slug: The tenant slug
            
        Returns:
            Tenant DTO if found, None otherwise
        """
        try:
            return self.manager.get_by_slug(slug)
        except Exception as e:
            logger.error(f"Error getting tenant with slug {slug}: {str(e)}")
            # Try to find by slug in all tenants
            try:
                tenants = self.get_all()
                for tenant in tenants:
                    if tenant.slug == slug:
                        return tenant
            except:
                pass
            return None
            
    def get_or_default(self, tenant_id_or_slug: str) -> Optional[TenantDTO]:
        """
        Get a tenant by ID or slug, falling back to first available tenant.
        
        Args:
            tenant_id_or_slug: The tenant ID or slug
            
        Returns:
            Tenant DTO if found, first available tenant if not, None if no tenants
        """
        # Try to get by ID
        tenant = self.get(tenant_id_or_slug)
        
        # If not found, try to get by slug
        if not tenant:
            tenant = self.get_by_slug(tenant_id_or_slug)
            
        # If still not found, get the first available tenant
        if not tenant:
            tenants = self.get_all()
            if tenants:
                tenant = tenants[0]
                logger.info(f"Using first available tenant as fallback: {tenant.name} ({tenant.slug})")
                
        return tenant

class AppProductManager:
    """
    Application-level product manager.
    
    This class provides a robust product manager with enhanced error handling
    for the application layer.
    """
    
    def __init__(self, session=None):
        """Initialize a new AppProductManager."""
        self.session = session or SessionLocal()
        self.manager = ProductManager()
        
    def list_by_tenant(self, tenant_id: str) -> List[Any]:
        """
        Get products for a tenant with enhanced error handling.
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            List of products, empty list if error occurs
        """
        try:
            return self.manager.list_by_tenant(tenant_id)
        except Exception as e:
            logger.error(f"Error getting products for tenant {tenant_id}: {str(e)}")
            return []