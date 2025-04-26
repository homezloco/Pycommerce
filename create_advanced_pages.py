"""Script to create advanced pages for all tenants using the new templates.

This script creates blog, FAQ, services, and portfolio pages for all tenants
using the advanced templates created by the add_advanced_templates.py script.
It ensures each tenant has a full set of pages based on the available templates.
"""

import logging
import sys
from typing import Dict, Any, List, Optional, Tuple

from app import app
from pycommerce.models.tenant import Tenant, TenantManager
from pycommerce.models.page_builder import (
    Page, PageManager, PageSection, PageSectionManager, 
    ContentBlock, ContentBlockManager, PageTemplateManager
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_tenant_by_slug(tenant_manager: TenantManager, slug: str) -> Optional[Tenant]:
    """Get a tenant by its slug."""
    tenants = tenant_manager.list_tenants()
    for tenant in tenants:
        if tenant.slug == slug:
            return tenant
    return None


def get_template_by_name(template_manager: PageTemplateManager, name: str) -> Optional[Any]:
    """Get a template by its name."""
    templates = template_manager.list_templates()
    for template in templates:
        if template.name == name:
            return template
    return None


def create_page_from_template(
    tenant_id: str,
    title: str,
    slug: str,
    template: Any,
    page_manager: PageManager,
    section_manager: PageSectionManager,
    block_manager: ContentBlockManager
) -> Optional[Page]:
    """Create a new page from a template."""
    # Check if page with this slug already exists for this tenant
    existing_pages = page_manager.list_pages_by_tenant(tenant_id)
    for page in existing_pages:
        if page.slug == slug:
            logger.info(f"Page with slug '{slug}' already exists for tenant {tenant_id}")
            return None
    
    # Create the page
    page = page_manager.create_page(
        tenant_id=tenant_id,
        title=title,
        slug=slug,
        published=True,
        meta_description=f"{title} - {template.description}"
    )
    
    if not page:
        logger.error(f"Failed to create page '{title}' for tenant {tenant_id}")
        return None
    
    # Create sections and blocks from template
    for section_data in template.sections:
        section = section_manager.create_section(
            page_id=page.id,
            name=section_data.get("name"),
            order=section_data.get("order"),
            settings=section_data.get("settings", {})
        )
        
        if not section:
            logger.error(f"Failed to create section {section_data.get('name')} for page {page.id}")
            continue
        
        # Create blocks for this section
        for block_data in section_data.get("blocks", []):
            block = block_manager.create_block(
                section_id=section.id,
                block_type=block_data.get("type"),
                content=block_data.get("content"),
                order=block_data.get("order"),
                settings=block_data.get("settings", {})
            )
            
            if not block:
                logger.error(f"Failed to create block {block_data.get('type')} for section {section.id}")
    
    logger.info(f"Successfully created page '{title}' with slug '{slug}' for tenant {tenant_id}")
    return page


def create_tenant_pages(
    tenant: Tenant,
    templates: Dict[str, Any],
    page_manager: PageManager,
    section_manager: PageSectionManager,
    block_manager: ContentBlockManager
) -> List[Page]:
    """Create a set of pages for a specific tenant using the advanced templates."""
    created_pages = []
    
    # Blog page
    if "Blog Page" in templates:
        page = create_page_from_template(
            tenant_id=tenant.id,
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
            tenant_id=tenant.id,
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
            tenant_id=tenant.id,
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
            tenant_id=tenant.id,
            title="Portfolio",
            slug="portfolio",
            template=templates["Portfolio Page"],
            page_manager=page_manager,
            section_manager=section_manager,
            block_manager=block_manager
        )
        if page:
            created_pages.append(page)
    
    logger.info(f"Created {len(created_pages)} pages for tenant '{tenant.name}'")
    return created_pages


def create_advanced_pages_for_all_tenants():
    """Create advanced pages for all tenants."""
    with app.app_context():
        # Initialize managers
        tenant_manager = TenantManager()
        page_manager = PageManager()
        section_manager = PageSectionManager()
        block_manager = ContentBlockManager()
        template_manager = PageTemplateManager()
        
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
        tenants = tenant_manager.list_tenants()
        if not tenants:
            logger.error("No tenants found")
            return
        
        total_pages_created = 0
        
        # Create pages for each tenant
        for tenant in tenants:
            logger.info(f"Creating advanced pages for tenant: {tenant.name} (ID: {tenant.id})")
            pages = create_tenant_pages(
                tenant=tenant,
                templates=templates_by_name,
                page_manager=page_manager,
                section_manager=section_manager,
                block_manager=block_manager
            )
            total_pages_created += len(pages)
        
        logger.info(f"Total pages created: {total_pages_created}")


if __name__ == "__main__":
    logger.info("Creating advanced pages for all tenants...")
    create_advanced_pages_for_all_tenants()
    logger.info("Finished creating advanced pages")
    sys.exit(0)