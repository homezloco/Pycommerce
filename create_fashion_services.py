#!/usr/bin/env python3
"""Script to create a Services page for Fashion Boutique.

This script creates a services page for Fashion Boutique using the Services Page template.
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


def create_fashion_services_page():
    """Create a Services page for Fashion Boutique."""
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
        
        # Check if we have the Services Page template
        if "Services Page" not in templates_by_name:
            logger.error("Services Page template not found")
            logger.error("Please run add_advanced_templates.py first to create the required templates")
            return
        
        # Get the fashion tenant
        tenant = tenant_manager.get_by_slug("fashion")
        if not tenant:
            logger.error("Fashion Boutique tenant not found")
            return
        
        tenant_id = str(tenant.id)
        
        # Check if services page already exists
        existing_pages = page_manager.list_by_tenant(tenant_id, include_unpublished=True)
        for page in existing_pages:
            if page.slug == "services":
                logger.info(f"Services page already exists for Fashion Boutique")
                return
        
        # Create the page
        page_data = {
            "tenant_id": tenant_id,
            "title": "Our Services",
            "slug": "services",
            "meta_title": "Our Services",
            "meta_description": f"Our Services - {templates_by_name['Services Page'].description}",
            "is_published": True,
            "layout_data": {}
        }
        page = page_manager.create(page_data)
        
        if not page:
            logger.error(f"Failed to create Services page for Fashion Boutique")
            return
        
        # Create sections and blocks from template
        sections = templates_by_name["Services Page"].template_data.get("sections", [])
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
        
        logger.info(f"Successfully created Services page for Fashion Boutique")
            
    except Exception as e:
        logger.error(f"Error creating Services page: {str(e)}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    logger.info("Creating Services page for Fashion Boutique...")
    create_fashion_services_page()
    logger.info("Finished creating Services page")
    sys.exit(0)