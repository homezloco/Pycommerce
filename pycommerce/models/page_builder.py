"""
Page builder models for the PyCommerce platform.

This module defines the models for the page builder system, including pages,
sections, blocks, and their relationships.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Session
from sqlalchemy.orm.attributes import QueryableAttribute

from pycommerce.core.db import Base, SessionLocal
from pycommerce.models.tenant import Tenant

logger = logging.getLogger(__name__)


class Page(Base):
    """A page in the store."""

    __tablename__ = "pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    is_published = Column(Boolean, default=False)
    layout_data = Column(JSON, nullable=True)  # Stores the page layout structure
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="pages")
    sections = relationship("PageSection", back_populates="page", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Page {self.id}: {self.title}>"


class PageSection(Base):
    """A section within a page."""

    __tablename__ = "page_sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id = Column(UUID(as_uuid=True), ForeignKey("pages.id", ondelete="CASCADE"), nullable=False)
    section_type = Column(String(50), nullable=False)  # e.g., "hero", "product-grid", "text-block"
    position = Column(Integer, nullable=False, default=0)
    settings = Column(JSON, nullable=True)  # Section-specific settings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    page = relationship("Page", back_populates="sections")
    blocks = relationship("ContentBlock", back_populates="section", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PageSection {self.id}: {self.section_type}>"


class ContentBlock(Base):
    """A content block within a section."""

    __tablename__ = "content_blocks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id = Column(UUID(as_uuid=True), ForeignKey("page_sections.id", ondelete="CASCADE"), nullable=False)
    block_type = Column(String(50), nullable=False)  # e.g., "text", "image", "product", "video"
    position = Column(Integer, nullable=False, default=0)
    content = Column(JSON, nullable=True)  # Block content data
    settings = Column(JSON, nullable=True)  # Block-specific settings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    section = relationship("PageSection", back_populates="blocks")

    def __repr__(self):
        return f"<ContentBlock {self.id}: {self.block_type}>"


class PageTemplate(Base):
    """A reusable page template."""

    __tablename__ = "page_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    thumbnail_url = Column(String(255), nullable=True)
    is_system = Column(Boolean, default=False)  # Whether this is a system-provided template
    template_data = Column(JSON, nullable=False)  # Template structure and defaults
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PageTemplate {self.id}: {self.name}>"


# Add to Tenant model - check both for attribute and mapper property to prevent SQLAlchemy warnings
if not hasattr(Tenant, 'pages') or not isinstance(getattr(Tenant, 'pages', None), QueryableAttribute):
    Tenant.pages = relationship("Page", back_populates="tenant", cascade="all, delete-orphan")


# ----- Manager Classes -----

class PageManager:
    """Manager for page operations."""

    def __init__(self, session=None):
        """Initialize with optional session."""
        self.session = session

    def _get_session(self):
        """Get the current session or create a new one."""
        if self.session:
            return self.session
        return SessionLocal()

    def create(self, page_data: Dict[str, Any]) -> Page:
        """
        Create a new page.

        Args:
            page_data: Dictionary containing page data

        Returns:
            The created page
        """
        session = self._get_session()
        try:
            page = Page(**page_data)
            session.add(page)
            session.commit()
            return page
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating page: {str(e)}")
            raise
        finally:
            if not self.session:
                session.close()

    def get(self, page_id: str) -> Optional[Page]:
        """
        Get a page by ID.

        Args:
            page_id: The ID of the page to retrieve

        Returns:
            The page if found, None otherwise
        """
        session = self._get_session()
        try:
            return session.query(Page).filter(Page.id == page_id).first()
        except Exception as e:
            logger.error(f"Error getting page: {str(e)}")
            return None
        finally:
            if not self.session:
                session.close()

    def get_by_slug(self, tenant_id: str, slug: str) -> Optional[Page]:
        """
        Get a page by tenant ID and slug.

        Args:
            tenant_id: The ID of the tenant
            slug: The page slug

        Returns:
            The page if found, None otherwise
        """
        session = self._get_session()
        try:
            return session.query(Page).filter(
                Page.tenant_id == tenant_id,
                Page.slug == slug
            ).first()
        except Exception as e:
            logger.error(f"Error getting page by slug: {str(e)}")
            return None
        finally:
            if not self.session:
                session.close()

    def list_by_tenant(self, tenant_id: str, include_unpublished: bool = False) -> List[Page]:
        """
        List pages for a tenant.

        Args:
            tenant_id: The ID of the tenant
            include_unpublished: Whether to include unpublished pages

        Returns:
            List of pages
        """
        session = self._get_session()
        try:
            query = session.query(Page).filter(Page.tenant_id == tenant_id)
            if not include_unpublished:
                query = query.filter(Page.is_published == True)
            return query.all()
        except Exception as e:
            logger.error(f"Error listing pages: {str(e)}")
            return []
        finally:
            if not self.session:
                session.close()

    def update(self, page_id: str, page_data: Dict[str, Any]) -> Optional[Page]:
        """
        Update a page.

        Args:
            page_id: The ID of the page to update
            page_data: Dictionary containing updated page data

        Returns:
            The updated page if found, None otherwise
        """
        session = self._get_session()
        try:
            page = session.query(Page).filter(Page.id == page_id).first()
            if not page:
                return None

            for key, value in page_data.items():
                if hasattr(page, key):
                    setattr(page, key, value)

            session.commit()
            return page
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating page: {str(e)}")
            return None
        finally:
            if not self.session:
                session.close()

    def delete(self, page_id: str) -> bool:
        """
        Delete a page.

        Args:
            page_id: The ID of the page to delete

        Returns:
            True if deleted, False otherwise
        """
        session = self._get_session()
        try:
            page = session.query(Page).filter(Page.id == page_id).first()
            if not page:
                return False

            session.delete(page)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting page: {str(e)}")
            return False
        finally:
            if not self.session:
                session.close()


class PageSectionManager:
    """Manager for page section operations."""

    def __init__(self, session=None):
        """Initialize with optional session."""
        self.session = session

    def _get_session(self):
        """Get the current session or create a new one."""
        if self.session:
            return self.session
        return SessionLocal()

    def create(self, section_data: Dict[str, Any]) -> PageSection:
        """
        Create a new page section.

        Args:
            section_data: Dictionary containing section data

        Returns:
            The created section
        """
        session = self._get_session()
        try:
            section = PageSection(**section_data)
            session.add(section)
            session.commit()
            return section
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating section: {str(e)}")
            raise
        finally:
            if not self.session:
                session.close()

    def get(self, section_id: str) -> Optional[PageSection]:
        """
        Get a section by ID.

        Args:
            section_id: The ID of the section to retrieve

        Returns:
            The section if found, None otherwise
        """
        session = self._get_session()
        try:
            return session.query(PageSection).filter(PageSection.id == section_id).first()
        except Exception as e:
            logger.error(f"Error getting section: {str(e)}")
            return None
        finally:
            if not self.session:
                session.close()

    def list_by_page(self, page_id: str) -> List[PageSection]:
        """
        List sections for a page.

        Args:
            page_id: The ID of the page

        Returns:
            List of sections
        """
        session = self._get_session()
        try:
            return session.query(PageSection).filter(
                PageSection.page_id == page_id
            ).order_by(PageSection.position).all()
        except Exception as e:
            logger.error(f"Error listing sections: {str(e)}")
            return []
        finally:
            if not self.session:
                session.close()

    def update(self, section_id: str, section_data: Dict[str, Any]) -> Optional[PageSection]:
        """
        Update a section.

        Args:
            section_id: The ID of the section to update
            section_data: Dictionary containing updated section data

        Returns:
            The updated section if found, None otherwise
        """
        session = self._get_session()
        try:
            section = session.query(PageSection).filter(PageSection.id == section_id).first()
            if not section:
                return None

            for key, value in section_data.items():
                if hasattr(section, key):
                    setattr(section, key, value)

            session.commit()
            return section
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating section: {str(e)}")
            return None
        finally:
            if not self.session:
                session.close()

    def delete(self, section_id: str) -> bool:
        """
        Delete a section.

        Args:
            section_id: The ID of the section to delete

        Returns:
            True if deleted, False otherwise
        """
        session = self._get_session()
        try:
            section = session.query(PageSection).filter(PageSection.id == section_id).first()
            if not section:
                return False

            session.delete(section)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting section: {str(e)}")
            return False
        finally:
            if not self.session:
                session.close()


class ContentBlockManager:
    """Manager for content block operations."""

    def __init__(self, session=None):
        """Initialize with optional session."""
        self.session = session

    def _get_session(self):
        """Get the current session or create a new one."""
        if self.session:
            return self.session
        return SessionLocal()

    def create(self, block_data: Dict[str, Any]) -> ContentBlock:
        """
        Create a new content block.

        Args:
            block_data: Dictionary containing block data

        Returns:
            The created block
        """
        session = self._get_session()
        try:
            block = ContentBlock(**block_data)
            session.add(block)
            session.commit()
            return block
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating block: {str(e)}")
            raise
        finally:
            if not self.session:
                session.close()

    def get(self, block_id: str) -> Optional[ContentBlock]:
        """
        Get a block by ID.

        Args:
            block_id: The ID of the block to retrieve

        Returns:
            The block if found, None otherwise
        """
        session = self._get_session()
        try:
            return session.query(ContentBlock).filter(ContentBlock.id == block_id).first()
        except Exception as e:
            logger.error(f"Error getting block: {str(e)}")
            return None
        finally:
            if not self.session:
                session.close()

    def list_by_section(self, section_id: str) -> List[ContentBlock]:
        """
        List blocks for a section.

        Args:
            section_id: The ID of the section

        Returns:
            List of blocks
        """
        session = self._get_session()
        try:
            return session.query(ContentBlock).filter(
                ContentBlock.section_id == section_id
            ).order_by(ContentBlock.position).all()
        except Exception as e:
            logger.error(f"Error listing blocks: {str(e)}")
            return []
        finally:
            if not self.session:
                session.close()

    def update(self, block_id: str, block_data: Dict[str, Any]) -> Optional[ContentBlock]:
        """
        Update a block.

        Args:
            block_id: The ID of the block to update
            block_data: Dictionary containing updated block data

        Returns:
            The updated block if found, None otherwise
        """
        session = self._get_session()
        try:
            block = session.query(ContentBlock).filter(ContentBlock.id == block_id).first()
            if not block:
                return None

            for key, value in block_data.items():
                if hasattr(block, key):
                    setattr(block, key, value)

            session.commit()
            return block
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating block: {str(e)}")
            return None
        finally:
            if not self.session:
                session.close()

    def delete(self, block_id: str) -> bool:
        """
        Delete a block.

        Args:
            block_id: The ID of the block to delete

        Returns:
            True if deleted, False otherwise
        """
        session = self._get_session()
        try:
            block = session.query(ContentBlock).filter(ContentBlock.id == block_id).first()
            if not block:
                return False

            session.delete(block)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting block: {str(e)}")
            return False
        finally:
            if not self.session:
                session.close()


class PageTemplateManager:
    """Manager for page template operations."""

    def __init__(self, session=None):
        """Initialize with optional session."""
        self.session = session

    def _get_session(self):
        """Get the current session or create a new one."""
        if self.session:
            return self.session
        return SessionLocal()

    def create(self, template_data: Dict[str, Any]) -> PageTemplate:
        """
        Create a new page template.

        Args:
            template_data: Dictionary containing template data

        Returns:
            The created template
        """
        session = self._get_session()
        try:
            template = PageTemplate(**template_data)
            session.add(template)
            session.commit()
            return template
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating template: {str(e)}")
            raise
        finally:
            if not self.session:
                session.close()

    def get(self, template_id: str) -> Optional[PageTemplate]:
        """
        Get a template by ID.

        Args:
            template_id: The ID of the template to retrieve

        Returns:
            The template if found, None otherwise
        """
        session = self._get_session()
        try:
            return session.query(PageTemplate).filter(PageTemplate.id == template_id).first()
        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            return None
        finally:
            if not self.session:
                session.close()

    def list_templates(self, include_system: bool = True) -> List[PageTemplate]:
        """
        List all templates.

        Args:
            include_system: Whether to include system templates

        Returns:
            List of templates
        """
        session = self._get_session()
        try:
            query = session.query(PageTemplate)
            if not include_system:
                query = query.filter(PageTemplate.is_system == False)
            return query.all()
        except Exception as e:
            logger.error(f"Error listing templates: {str(e)}")
            return []
        finally:
            if not self.session:
                session.close()

    def update(self, template_id: str, template_data: Dict[str, Any]) -> Optional[PageTemplate]:
        """
        Update a template.

        Args:
            template_id: The ID of the template to update
            template_data: Dictionary containing updated template data

        Returns:
            The updated template if found, None otherwise
        """
        session = self._get_session()
        try:
            template = session.query(PageTemplate).filter(PageTemplate.id == template_id).first()
            if not template:
                return None

            for key, value in template_data.items():
                if hasattr(template, key):
                    setattr(template, key, value)

            session.commit()
            return template
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating template: {str(e)}")
            return None
        finally:
            if not self.session:
                session.close()

    def delete(self, template_id: str) -> bool:
        """
        Delete a template.

        Args:
            template_id: The ID of the template to delete

        Returns:
            True if deleted, False otherwise
        """
        session = self._get_session()
        try:
            template = session.query(PageTemplate).filter(PageTemplate.id == template_id).first()
            if not template:
                return False

            session.delete(template)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting template: {str(e)}")
            return False
        finally:
            if not self.session:
                session.close()