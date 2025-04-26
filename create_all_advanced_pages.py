#!/usr/bin/env python3
"""Script to create advanced pages for all remaining tenants.

This script creates blog, FAQ, services, and portfolio pages for all tenants 
that don't already have these pages, using the advanced templates.
"""

import logging
import sys
import uuid
from typing import Dict, Any, List, Optional

from pycommerce.core.db import SessionLocal
from pycommerce.models.page_builder import (
    PageManager, PageTemplateManager, PageSectionManager, ContentBlockManager, 
    Page, PageTemplate
)
from pycommerce.sdk import AppTenantManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_page_from_template(
    tenant_id: str,
    title: str,
    slug: str,
    template: PageTemplate,
    page_manager: PageManager,
    section_manager: PageSectionManager,
    block_manager: ContentBlockManager
) -> Optional[Page]:
    """Create a new page from a template."""
    session = SessionLocal()
    try:
        # Check if page with this slug already exists for this tenant
        existing_pages = page_manager.list_by_tenant(tenant_id, include_unpublished=True)
        for page in existing_pages:
            if page.slug == slug:
                logger.info(f"Page with slug '{slug}' already exists for tenant {tenant_id}")
                return None
        
        # Create the page
        page_data = {
            "tenant_id": tenant_id,
            "title": title,
            "slug": slug,
            "meta_title": title,
            "meta_description": f"{title} - {template.description}",
            "is_published": True,
            "layout_data": {}
        }
        page = page_manager.create(page_data)
        
        if not page:
            logger.error(f"Failed to create page '{title}' for tenant {tenant_id}")
            return None
        
        # Create sections and blocks from template
        sections = template.template_data.get("sections", [])
        for i, section_data in enumerate(sections):
            section_type = section_data.get("section_type", f"section_{i+1}")
            section = section_manager.create({
                "page_id": str(page.id),
                "section_type": section_type,
                "position": i + 1,
                "settings": section_data.get("settings", {})
            })
            
            if not section:
                logger.error(f"Failed to create section {section_data.get('name')} for page {page.id}")
                continue
        
        logger.info(f"Successfully created page '{title}' with slug '{slug}' for tenant {tenant_id}")
        return page
    except Exception as e:
        logger.error(f"Error creating page from template: {str(e)}")
        session.rollback()
        return None
    finally:
        session.close()


def create_tenant_pages(
    tenant_dict: Dict[str, Any],
    templates: Dict[str, PageTemplate],
    page_manager: PageManager,
    section_manager: PageSectionManager,
    block_manager: ContentBlockManager
) -> List[Page]:
    """Create a set of pages for a specific tenant using the advanced templates."""
    created_pages = []
    tenant_id = tenant_dict["id"]
    
    # Blog page
    if "Blog Page" in templates:
        page = create_page_from_template(
            tenant_id=tenant_id,
            title="Blog",
            slug="blog",
            template=templates["Blog Page"],
            page_manager=page_manager,
            section_manager=section_manager,
            block_manager=block_manager
        )
        if page:
            created_pages.append(page)
    
    # FAQ page
    if "FAQ Page" in templates:
        page = create_page_from_template(
            tenant_id=tenant_id,
            title="Frequently Asked Questions",
            slug="faq",
            template=templates["FAQ Page"],
            page_manager=page_manager,
            section_manager=section_manager,
            block_manager=block_manager
        )
        if page:
            created_pages.append(page)
    
    # Services page
    if "Services Page" in templates:
        page = create_page_from_template(
            tenant_id=tenant_id,
            title="Our Services",
            slug="services",
            template=templates["Services Page"],
            page_manager=page_manager,
            section_manager=section_manager,
            block_manager=block_manager
        )
        if page:
            created_pages.append(page)
    
    # Portfolio page
    if "Portfolio Page" in templates:
        page = create_page_from_template(
            tenant_id=tenant_id,
            title="Portfolio",
            slug="portfolio",
            template=templates["Portfolio Page"],
            page_manager=page_manager,
            section_manager=section_manager,
            block_manager=block_manager
        )
        if page:
            created_pages.append(page)
    
    logger.info(f"Created {len(created_pages)} pages for tenant '{tenant_dict['name']}'")
    return created_pages


def create_all_remaining_tenant_pages():
    """Create advanced pages for all tenants other than demo1."""
    session = SessionLocal()
    try:
        # Initialize managers
        tenant_manager = AppTenantManager()
        page_manager = PageManager(session)
        section_manager = PageSectionManager(session)
        block_manager = ContentBlockManager(session)
        template_manager = PageTemplateManager(session)
        
        # Get all templates
        all_templates = template_manager.list_templates()
        templates_by_name = {template.name: template for template in all_templates}
        
        # Check if we have the required templates
        required_templates = ["Blog Page", "FAQ Page", "Services Page", "Portfolio Page"]
        missing_templates = []
        
        for template_name in required_templates:
            if template_name not in templates_by_name:
                missing_templates.append(template_name)
        
        if missing_templates:
            logger.error(f"Missing templates: {', '.join(missing_templates)}")
            logger.error("Please run add_advanced_templates.py first to create the required templates")
            return
        
        # Get all tenants
        tenants = tenant_manager.get_all()
        if not tenants:
            logger.error("No tenants found")
            return
        
        # Convert tenant objects to dictionaries for consistent handling
        tenant_dicts = []
        for tenant in tenants:
            # Skip demo1 since we've already created pages for it
            if tenant.slug != "demo1":
                tenant_dicts.append({
                    "id": str(tenant.id),
                    "name": tenant.name,
                    "slug": tenant.slug
                })
        
        logger.info(f"Found {len(tenant_dicts)} tenants to process")
        
        total_pages_created = 0
        
        # Create pages for each tenant
        for tenant_dict in tenant_dicts:
            logger.info(f"Creating advanced pages for tenant: {tenant_dict['name']} (ID: {tenant_dict['id']})")
            pages = create_tenant_pages(
                tenant_dict=tenant_dict,
                templates=templates_by_name,
                page_manager=page_manager,
                section_manager=section_manager,
                block_manager=block_manager
            )
            total_pages_created += len(pages)
        
        logger.info(f"Total pages created: {total_pages_created}")
        
    except Exception as e:
        logger.error(f"Error creating advanced pages: {str(e)}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    logger.info("Creating advanced pages for remaining tenants...")
    create_all_remaining_tenant_pages()
    logger.info("Finished creating advanced pages")
    sys.exit(0)