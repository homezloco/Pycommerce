
import sys
import logging
import uuid
from datetime import datetime

from pycommerce.core.db import SessionLocal
from pycommerce.models.page_builder import (
    PageManager, PageSectionManager, ContentBlockManager
)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("main")

def add_default_sections():
    """Add default sections and content blocks to pages that don't have any."""
    session = SessionLocal()
    try:
        logger.info("Starting to add default sections to pages without content")
        
        # Initialize managers
        page_manager = PageManager(session)
        section_manager = PageSectionManager(session)
        block_manager = ContentBlockManager(session)
        
        # Get all tenants and their pages
        from pycommerce.models.tenant import TenantManager
        tenant_manager = TenantManager()
        tenant_manager.session = session
        tenants = tenant_manager.get_all()
        
        section_count = 0
        block_count = 0
        
        for tenant in tenants:
            logger.info(f"Processing tenant: {tenant.name} ({tenant.id})")
            pages = page_manager.list_by_tenant(str(tenant.id), include_unpublished=True)
            
            for page in pages:
                # Check if the page has any sections
                sections = section_manager.list_by_page(str(page.id))
                
                if not sections:
                    logger.info(f"Adding default section to page: {page.title} ({page.id})")
                    
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
                    section_count += 1
                    
                    # Create a text block with default content
                    block_data = {
                        "section_id": str(section.id),
                        "block_type": "text",
                        "position": 0,
                        "content": {
                            "html": f"<h1>Welcome to {tenant.name}</h1><p>This is the {page.title} page. Edit this content to customize your page.</p>"
                        },
                        "settings": {
                            "width": "normal"
                        }
                    }
                    
                    block = block_manager.create(block_data)
                    block_count += 1
                else:
                    # Check if each section has any blocks
                    for section in sections:
                        blocks = block_manager.list_by_section(str(section.id))
                        
                        if not blocks:
                            logger.info(f"Adding default block to section: {section.section_type} ({section.id})")
                            
                            # Create a text block with default content
                            block_data = {
                                "section_id": str(section.id),
                                "block_type": "text",
                                "position": 0,
                                "content": {
                                    "html": f"<h2>{section.section_type.title()} Section</h2><p>This is a default content block. Edit this content to customize your page.</p>"
                                },
                                "settings": {
                                    "width": "normal"
                                }
                            }
                            
                            block = block_manager.create(block_data)
                            block_count += 1
        
        # Commit all changes
        session.commit()
        
        logger.info(f"Added {section_count} sections and {block_count} content blocks")
        return section_count, block_count
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error adding default sections: {str(e)}")
        return 0, 0
    finally:
        session.close()

if __name__ == "__main__":
    logger.info("Starting to add default sections to pages")
    section_count, block_count = add_default_sections()
    logger.info(f"Added {section_count} sections and {block_count} blocks to pages")
    logger.info("Script completed successfully")
