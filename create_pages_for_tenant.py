#!/usr/bin/env python3
"""
Script to create store pages from templates for a specific tenant.

This script creates pages for a specific tenant using available templates.
"""

import logging
import uuid
import argparse
from typing import Dict, List, Optional, Any

from pycommerce.core.db import SessionLocal
from pycommerce.models.page_builder import (
    PageManager, PageTemplateManager, PageSectionManager, ContentBlockManager,
    Page, PageSection, ContentBlock
)
from pycommerce.models.tenant import TenantManager, Tenant

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_tenant_by_slug(tenant_manager: TenantManager, slug: str) -> Optional[Tenant]:
    """Get a tenant by its slug."""
    return tenant_manager.get_by_slug(slug)

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
    try:
        # Create the page
        page_data = {
            "tenant_id": tenant_id,
            "title": title,
            "slug": slug,
            "meta_title": title,
            "meta_description": f"Welcome to our {title} page.",
            "is_published": True,
            "layout_data": {}
        }
        
        page = page_manager.create(page_data)
        logger.info(f"Created page: {page.title} (ID: {page.id})")
        
        # Get template sections
        sections = template.template_data.get("sections", [])
        logger.info(f"Template has {len(sections)} sections")
        
        # Create sections from template
        position = 0
        for section_data in sections:
            section_type = section_data.get("section_type")
            settings = section_data.get("settings", {})
            
            # Create the section
            section = section_manager.create({
                "page_id": str(page.id),
                "section_type": section_type,
                "position": position,
                "settings": settings
            })
            logger.info(f"Created section: {section_type} (ID: {section.id}, position: {position})")
            
            # Add default content blocks based on section type
            if section_type == "hero_banner" or section_type == "hero":
                block_manager.create({
                    "section_id": str(section.id),
                    "block_type": "heading",
                    "position": 0,
                    "content": {"html": f"<h1>Welcome to {title}</h1>"},
                    "settings": {"size": "large", "alignment": "center"}
                })
                block_manager.create({
                    "section_id": str(section.id),
                    "block_type": "text",
                    "position": 1,
                    "content": {"html": "<p>Discover our amazing products and services.</p>"},
                    "settings": {"size": "medium", "alignment": "center"}
                })
                block_manager.create({
                    "section_id": str(section.id),
                    "block_type": "button",
                    "position": 2,
                    "content": {"text": "Shop Now", "url": "/products"},
                    "settings": {"style": "primary", "size": "large"}
                })
            
            elif section_type == "content" or section_type == "company_intro":
                block_manager.create({
                    "section_id": str(section.id),
                    "block_type": "heading",
                    "position": 0,
                    "content": {"html": f"<h2>About {title}</h2>"},
                    "settings": {"size": "medium", "alignment": "left"}
                })
                block_manager.create({
                    "section_id": str(section.id),
                    "block_type": "text",
                    "position": 1,
                    "content": {"html": "<p>We provide top-quality products with exceptional customer service. Our team is dedicated to offering the best shopping experience.</p>"},
                    "settings": {"size": "medium", "alignment": "left"}
                })
            
            elif section_type == "featured_products":
                block_manager.create({
                    "section_id": str(section.id),
                    "block_type": "product_list",
                    "position": 0,
                    "content": {"product_ids": [], "count": 4, "source": "featured"},
                    "settings": {"layout": "grid", "columns": 4}
                })
            
            elif section_type == "testimonials":
                block_manager.create({
                    "section_id": str(section.id),
                    "block_type": "testimonial",
                    "position": 0,
                    "content": {
                        "quote": "This store has amazing products! I'm a loyal customer now.",
                        "author": "Sarah Johnson",
                        "role": "Customer"
                    },
                    "settings": {"style": "card"}
                })
                block_manager.create({
                    "section_id": str(section.id),
                    "block_type": "testimonial",
                    "position": 1,
                    "content": {
                        "quote": "Great quality and fast shipping every time.",
                        "author": "Michael Brown",
                        "role": "Customer"
                    },
                    "settings": {"style": "card"}
                })
            
            elif section_type == "newsletter":
                block_manager.create({
                    "section_id": str(section.id),
                    "block_type": "form",
                    "position": 0,
                    "content": {
                        "title": "Subscribe to our newsletter",
                        "description": "Get the latest updates and special offers",
                        "button_text": "Subscribe"
                    },
                    "settings": {"style": "inline"}
                })
            
            elif section_type == "cta":
                block_manager.create({
                    "section_id": str(section.id),
                    "block_type": "heading",
                    "position": 0,
                    "content": {"html": "<h2>Ready to Shop?</h2>"},
                    "settings": {"size": "medium", "alignment": "center"}
                })
                block_manager.create({
                    "section_id": str(section.id),
                    "block_type": "text",
                    "position": 1,
                    "content": {"html": "<p>Browse our collection today and find great deals.</p>"},
                    "settings": {"size": "medium", "alignment": "center"}
                })
                block_manager.create({
                    "section_id": str(section.id),
                    "block_type": "button",
                    "position": 2,
                    "content": {"text": "View Products", "url": "/products"},
                    "settings": {"style": "primary", "size": "medium"}
                })
            
            position += 1
        
        return page
    
    except Exception as e:
        logger.error(f"Error creating page from template: {str(e)}")
        return None

def create_pages_for_tenant(tenant_slug: str):
    """Create a set of pages for a specific tenant."""
    session = SessionLocal()
    try:
        # Initialize managers
        tenant_manager = TenantManager()
        tenant_manager.session = session
        
        page_manager = PageManager(session)
        section_manager = PageSectionManager(session)
        block_manager = ContentBlockManager(session)
        template_manager = PageTemplateManager(session)
        
        # Get all templates and organize by name
        all_templates = template_manager.list_templates()
        templates = {t.name: t for t in all_templates}
        logger.info(f"Found {len(templates)} templates: {list(templates.keys())}")
        
        # Get the tenant
        tenant = get_tenant_by_slug(tenant_manager, tenant_slug)
        if not tenant:
            logger.error(f"Tenant with slug '{tenant_slug}' not found")
            return
            
        logger.info(f"Creating pages for tenant: {tenant.name} (slug: {tenant.slug})")
        
        tenant_id = str(tenant.id)
        tenant_name = tenant.name
        created_pages = []
        
        # Check if tenant already has pages other than the welcome page
        existing_pages = page_manager.list_by_tenant(tenant_id, include_unpublished=True)
        existing_slugs = [p.slug for p in existing_pages]
        logger.info(f"Existing page slugs: {existing_slugs}")
        
        # Create homepage using E-commerce Homepage template if it doesn't exist
        if "home" not in existing_slugs and "E-commerce Homepage" in templates:
            home_page = create_page_from_template(
                tenant_id=tenant_id,
                title="Home",
                slug="home",
                template=templates["E-commerce Homepage"],
                page_manager=page_manager,
                section_manager=section_manager,
                block_manager=block_manager
            )
            if home_page:
                created_pages.append(home_page)
        
        # Create about page using About Us Page template if it doesn't exist
        if "about" not in existing_slugs and "About Us Page" in templates:
            about_page = create_page_from_template(
                tenant_id=tenant_id,
                title="About Us",
                slug="about",
                template=templates["About Us Page"],
                page_manager=page_manager,
                section_manager=section_manager,
                block_manager=block_manager
            )
            if about_page:
                created_pages.append(about_page)
        
        # Create categories page using Product Category Page template if it doesn't exist
        if "categories" not in existing_slugs and "Product Category Page" in templates:
            categories_page = create_page_from_template(
                tenant_id=tenant_id,
                title="Categories",
                slug="categories",
                template=templates["Product Category Page"],
                page_manager=page_manager,
                section_manager=section_manager,
                block_manager=block_manager
            )
            if categories_page:
                created_pages.append(categories_page)
        
        # Create contact page using Contact Page template if it doesn't exist
        if "contact" not in existing_slugs and "Contact Page" in templates:
            contact_page = create_page_from_template(
                tenant_id=tenant_id,
                title="Contact Us",
                slug="contact",
                template=templates["Contact Page"],
                page_manager=page_manager,
                section_manager=section_manager,
                block_manager=block_manager
            )
            if contact_page:
                created_pages.append(contact_page)
        
        logger.info(f"Created {len(created_pages)} pages for tenant {tenant.name}")
        
    except Exception as e:
        logger.error(f"Error creating pages: {str(e)}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create pages from templates for a specific tenant")
    parser.add_argument("tenant_slug", help="The slug of the tenant to create pages for")
    args = parser.parse_args()
    create_pages_for_tenant(args.tenant_slug)