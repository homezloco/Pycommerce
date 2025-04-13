
"""
Test script for page builder functionality.
"""
import logging
import sys
from sqlalchemy import inspect, MetaData, Table
from pycommerce.models.page_builder import (
    Page, PageSection, ContentBlock, PageTemplate,
    PageManager, PageSectionManager, ContentBlockManager, PageTemplateManager
)
from pycommerce.models.tenant import Tenant, TenantManager
from pycommerce.core.db import SessionLocal, engine

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_tables():
    """Check if page builder tables exist in the database."""
    logger.info("Checking if page builder tables exist...")
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    logger.info(f"Found tables: {existing_tables}")
    
    required_tables = ['pages', 'page_sections', 'content_blocks', 'page_templates']
    missing_tables = [table for table in required_tables if table not in existing_tables]
    
    if missing_tables:
        logger.warning(f"Missing tables: {missing_tables}")
        return False
    else:
        logger.info("All required tables exist.")
        return True

def create_test_pages():
    """Create test pages for each tenant."""
    logger.info("Creating test pages...")
    
    # Get all tenants
    tenant_manager = TenantManager()
    page_manager = PageManager()
    section_manager = PageSectionManager()
    block_manager = ContentBlockManager()
    
    tenants = tenant_manager.get_all()
    logger.info(f"Found {len(tenants)} tenants")
    
    for tenant in tenants:
        # Check if tenant already has pages
        existing_pages = page_manager.list_by_tenant(str(tenant.id), include_unpublished=True)
        if existing_pages:
            logger.info(f"Tenant {tenant.name} already has {len(existing_pages)} pages")
            continue
        
        # Create a test page
        logger.info(f"Creating test page for tenant {tenant.name}")
        page_data = {
            "tenant_id": str(tenant.id),
            "title": f"Welcome to {tenant.name}",
            "slug": "welcome",
            "meta_title": f"Welcome to {tenant.name} - Home Page",
            "meta_description": f"Welcome to {tenant.name}, your one-stop shop for all your needs.",
            "is_published": True,
            "layout_data": {
                "type": "page",
                "sections": []
            }
        }
        
        try:
            page = page_manager.create(page_data)
            logger.info(f"Created page: {page.title} (ID: {page.id})")
            
            # Create a main content section
            section_data = {
                "page_id": str(page.id),
                "section_type": "content",
                "position": 0,
                "settings": {
                    "padding": "medium",
                    "background": "white"
                }
            }
            
            section = section_manager.create(section_data)
            logger.info(f"Created section: {section.section_type} (ID: {section.id})")
            
            # Create a text block with content
            block_data = {
                "section_id": str(section.id),
                "block_type": "text",
                "position": 0,
                "content": {
                    "html": f"<h1>Welcome to {tenant.name}</h1><p>This is a test page created by the page builder system.</p>"
                },
                "settings": {
                    "width": "normal"
                }
            }
            
            block = block_manager.create(block_data)
            logger.info(f"Created block: {block.block_type} (ID: {block.id})")
            
        except Exception as e:
            logger.error(f"Error creating test page: {str(e)}")

def main():
    """Main function to test page builder functionality."""
    try:
        # Check if tables exist
        tables_exist = check_tables()
        
        if not tables_exist:
            logger.error("Missing required tables. Please run page builder migration first.")
            sys.exit(1)
        
        # Create test pages
        create_test_pages()
        
        logger.info("Page builder test completed successfully.")
    except Exception as e:
        logger.error(f"Error during page builder test: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
