"""
Tenant model for PyCommerce SDK.

This module provides the tenant model and manager for the PyCommerce SDK.
"""

import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from pycommerce.core.db import db_session
from pycommerce.models.db_registry import Tenant

# Configure logging
logger = logging.getLogger("pycommerce.models.tenant")


class TenantDTO:
    """
    Data Transfer Object for Tenant.

    Represents a tenant in the multi-tenant PyCommerce platform.
    """

    def __init__(self, id: UUID, name: str, slug: str, domain: Optional[str] = None,
                 active: bool = True, settings: Optional[Dict[str, Any]] = None,
                 created_at: datetime = None, updated_at: datetime = None):
        """
        Initialize a new TenantDTO.

        Args:
            id: The tenant ID
            name: The tenant name
            slug: The tenant slug (used in URLs)
            domain: Optional custom domain for the tenant
            active: Whether the tenant is active
            settings: Optional tenant settings including theme configuration
            created_at: When the tenant was created
            updated_at: When the tenant was last updated
        """
        self.id = id
        self.name = name
        self.slug = slug
        self.domain = domain
        self.active = active
        self.settings = settings or {}
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    @classmethod
    def from_model(cls, model: Tenant) -> 'TenantDTO':
        """
        Create a TenantDTO from a Tenant model.

        Args:
            model: The Tenant model instance

        Returns:
            A TenantDTO instance
        """
        return cls(
            id=model.id,
            name=model.name,
            slug=model.slug,
            domain=model.domain,
            active=model.active,
            settings=model.settings,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the tenant to a dictionary.

        Returns:
            Dictionary representation of the tenant
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "domain": self.domain,
            "active": self.active,
            "settings": self.settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class TenantManager:
    """Manager for tenant operations."""

    def __init__(self):
        """Initialize a new TenantManager."""
        self.session = db_session

    def list(self) -> List[TenantDTO]:
        """
        List all tenants.

        Returns:
            List of all tenants
        """
        try:
            tenant_models = self.session.query(Tenant).all()
            return [TenantDTO.from_model(model) for model in tenant_models]
        except Exception as e:
            logger.error(f"Error listing tenants: {str(e)}")
            return []

    def get_all(self) -> List[TenantDTO]:
        """
        Get all tenants.

        This is an alias for the list() method.

        Returns:
            List of all tenants
        """
        return self.list()

    def get(self, tenant_id: UUID) -> Optional[TenantDTO]:
        """
        Get a tenant by ID.

        Args:
            tenant_id: The tenant ID

        Returns:
            The tenant, or None if not found
        """
        try:
            tenant_model = self.session.query(Tenant).filter(Tenant.id == tenant_id).first()
            return TenantDTO.from_model(tenant_model) if tenant_model else None
        except Exception as e:
            logger.error(f"Error getting tenant {tenant_id}: {str(e)}")
            return None

    def get_by_slug(self, slug: str) -> Optional[TenantDTO]:
        """
        Get a tenant by slug.

        Args:
            slug: The tenant slug

        Returns:
            The tenant, or None if not found
        """
        try:
            # Always create a fresh session to ensure we get the latest data
            with db_session() as fresh_session:
                tenant_model = fresh_session.query(Tenant).filter(Tenant.slug == slug).first()
                if tenant_model:
                    # Force refresh to make sure we have the latest data including settings
                    fresh_session.refresh(tenant_model)
                    logger.info(f"Retrieved tenant by slug {slug} with theme settings: {tenant_model.settings.get('theme', {}) if tenant_model.settings else {}}")
                    return TenantDTO.from_model(tenant_model)
                return None
        except Exception as e:
            logger.error(f"Error getting tenant by slug {slug}: {str(e)}")
            return None

    def get_tenant_by_slug(self, slug: str) -> Optional[TenantDTO]:
        """
        Get a tenant by slug (alias for get_by_slug).

        Args:
            slug: The tenant slug

        Returns:
            The tenant, or None if not found
        """
        return self.get_by_slug(slug)

    def get_by_domain(self, domain: str) -> Optional[TenantDTO]:
        """
        Get a tenant by domain.

        Args:
            domain: The tenant domain

        Returns:
            The tenant, or None if not found
        """
        try:
            tenant_model = self.session.query(Tenant).filter(Tenant.domain == domain).first()
            return TenantDTO.from_model(tenant_model) if tenant_model else None
        except Exception as e:
            logger.error(f"Error getting tenant by domain {domain}: {str(e)}")
            return None

    def create(self, name: str, slug: str, domain: Optional[str] = None, active: bool = True) -> Optional[TenantDTO]:
        """
        Create a new tenant.

        Args:
            name: The tenant name
            slug: The tenant slug
            domain: Optional custom domain for the tenant
            active: Whether the tenant is active

        Returns:
            The created tenant, or None if creation fails
        """
        try:
            # Validate slug (only lowercase letters, numbers, and hyphens)
            if not all(c.isalnum() or c == '-' for c in slug) or not slug[0].isalpha():
                raise ValueError("Slug must contain only letters, numbers, and hyphens, and must start with a letter")

            # Check if slug is already taken
            if self.session.query(Tenant).filter(Tenant.slug == slug).first():
                raise ValueError(f"Slug '{slug}' is already taken")

            # Check if domain is already taken
            if domain and self.session.query(Tenant).filter(Tenant.domain == domain).first():
                raise ValueError(f"Domain '{domain}' is already taken")

            # Create tenant
            tenant_model = Tenant(
                id=uuid.uuid4(),
                name=name,
                slug=slug,
                domain=domain,
                active=active
            )
            self.session.add(tenant_model)
            self.session.commit()

            logger.info(f"Created tenant: {name} ({slug})")
            return TenantDTO.from_model(tenant_model)
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating tenant: {str(e)}")
            raise

    def update(self, tenant_id: UUID, data: Dict[str, Any]) -> Optional[TenantDTO]:
        """
        Update a tenant.

        Args:
            tenant_id: The tenant ID
            data: Dictionary containing updated tenant data

        Returns:
            The updated tenant, or None if update fails
        """
        try:
            tenant_model = self.session.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant_model:
                raise ValueError(f"Tenant not found: {tenant_id}")

            # Update fields
            for key, value in data.items():
                if key in ["name", "slug", "domain", "active"]:
                    # Validate slug (only lowercase letters, numbers, and hyphens)
                    if key == "slug" and not all(c.isalnum() or c == '-' for c in value) or not value[0].isalpha():
                        raise ValueError("Slug must contain only letters, numbers, and hyphens, and must start with a letter")

                    # Check if slug is already taken
                    if key == "slug" and value != tenant_model.slug and self.session.query(Tenant).filter(Tenant.slug == value).first():
                        raise ValueError(f"Slug '{value}' is already taken")

                    # Check if domain is already taken
                    if key == "domain" and value != tenant_model.domain and self.session.query(Tenant).filter(Tenant.domain == value).first():
                        raise ValueError(f"Domain '{value}' is already taken")

                    setattr(tenant_model, key, value)
                elif key == "settings":
                    # Update settings field
                    tenant_model.settings = value

            # Update updated_at timestamp
            tenant_model.updated_at = datetime.utcnow()

            self.session.commit()

            logger.info(f"Updated tenant: {tenant_id}")
            return TenantDTO.from_model(tenant_model)
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating tenant {tenant_id}: {str(e)}")
            raise

    def update_settings(self, tenant_id: UUID, settings: Dict[str, Any]) -> Optional[TenantDTO]:
        """
        Update tenant settings including theme configuration.

        Args:
            tenant_id: The tenant ID
            settings: Dictionary containing tenant settings to update

        Returns:
            The updated tenant, or None if update fails
        """
        try:
            tenant_model = self.session.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant_model:
                raise ValueError(f"Tenant not found: {tenant_id}")

            # Initialize settings if not already present
            if tenant_model.settings is None:
                tenant_model.settings = {}

            # Update settings (merge with existing)
            tenant_model.settings.update(settings)

            # Update updated_at timestamp
            tenant_model.updated_at = datetime.utcnow()

            self.session.commit()

            logger.info(f"Updated settings for tenant: {tenant_id}")
            return TenantDTO.from_model(tenant_model)
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating settings for tenant {tenant_id}: {str(e)}")
            raise

    def update_theme(self, tenant_id: UUID, theme_config: Dict[str, Any]) -> Optional[TenantDTO]:
        """
        Update theme configuration for a tenant.

        Args:
            tenant_id: The tenant ID
            theme_config: Dictionary containing theme configuration

        Returns:
            The updated tenant, or None if update fails
        """
        try:
            # Add more detailed logging about the theme configuration being saved
            logger.info(f"Updating theme for tenant {tenant_id} with config: {theme_config}")

            # Check if logo_url is in the theme_config and log it
            if 'logo_url' in theme_config:
                logger.info(f"Logo URL from theme_config: {theme_config['logo_url']}")
            else:
                logger.warning(f"No logo_url found in theme_config: {list(theme_config.keys())}")

            tenant_model = self.session.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant_model:
                raise ValueError(f"Tenant not found: {tenant_id}")

            # Initialize settings if not already present
            if tenant_model.settings is None:
                tenant_model.settings = {}

            # Initialize theme settings if not already present
            if "theme" not in tenant_model.settings:
                tenant_model.settings["theme"] = {}

            # Log the current theme settings before update
            logger.info(f"Current theme settings before update: {tenant_model.settings.get('theme', {})}")

            # Update theme settings
            tenant_model.settings["theme"].update(theme_config)

            # Log the updated theme settings
            logger.info(f"Updated theme settings: {tenant_model.settings.get('theme', {})}")

            # Update updated_at timestamp
            tenant_model.updated_at = datetime.utcnow()

            self.session.commit()

            # Force a fresh query to verify changes were saved
            refreshed_tenant = self.session.query(Tenant).filter(Tenant.id == tenant_id).first()
            refreshed_theme = refreshed_tenant.settings.get('theme', {}) if refreshed_tenant.settings else {}
            logger.info(f"Theme settings after commit: {refreshed_theme}")

            # Specifically check if logo_url was saved
            if 'logo_url' in refreshed_theme:
                logger.info(f"Logo URL saved successfully: {refreshed_theme['logo_url']}")
            else:
                logger.warning("Logo URL not found in saved theme settings")

            logger.info(f"Updated theme for tenant: {tenant_id}")
            return TenantDTO.from_model(tenant_model)
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating theme for tenant {tenant_id}: {str(e)}")
            raise

    def delete(self, tenant_id: UUID) -> bool:
        """
        Delete a tenant.

        Args:
            tenant_id: The tenant ID

        Returns:
            True if successful, False otherwise
        """
        try:
            tenant_model = self.session.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant_model:
                raise ValueError(f"Tenant not found: {tenant_id}")

            self.session.delete(tenant_model)
            self.session.commit()

            logger.info(f"Deleted tenant: {tenant_id}")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting tenant {tenant_id}: {str(e)}")
            raise