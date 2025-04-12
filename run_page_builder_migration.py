
"""
Script to run the page builder migration and create necessary tables.
"""

import logging
import os
from sqlalchemy import create_engine
from migrations.add_page_builder_tables import run_migration
from pycommerce.models.page_builder import (
    Page, PageSection, ContentBlock, PageTemplate,
    PageManager, PageSectionManager, ContentBlockManager, PageTemplateManager
)
from pycommerce.core.db import SessionLocal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Run page builder migration and verify tables."""
    logger.info("Running page builder migration...")
    
    # Get database URL from environment variable or use a default
    db_uri = os.environ.get('DATABASE_URL', 'sqlite:///pycommerce.db')
    logger.info(f"Using database URI: {db_uri}")
    
    # Run the migration to create tables
    run_migration(db_uri)
    
    # Verify tables were created by creating a test session
    session = SessionLocal()
    try:
        # Check if we can query the tables
        page_count = session.query(Page).count()
        section_count = session.query(PageSection).count()
        block_count = session.query(ContentBlock).count()
        template_count = session.query(PageTemplate).count()
        
        logger.info(f"Page builder tables created successfully:")
        logger.info(f"- Pages: {page_count}")
        logger.info(f"- Page Sections: {section_count}")
        logger.info(f"- Content Blocks: {block_count}")
        logger.info(f"- Page Templates: {template_count}")
        
        # Create a default template
        template_manager = PageTemplateManager(session)
        if template_count == 0:
            logger.info("Creating default page template...")
            default_template = {
                "name": "Basic Page",
                "description": "A simple page template with header, content, and footer sections",
                "is_system": True,
                "thumbnail_url": "/static/media/uploads/page_templates/basic_template.png",
                "template_data": {
                    "sections": [
                        {
                            "section_type": "header",
                            "position": 0,
                            "settings": {"background_color": "#ffffff", "text_color": "#333333"}
                        },
                        {
                            "section_type": "content",
                            "position": 1,
                            "settings": {"padding": "20px", "max_width": "1200px"}
                        },
                        {
                            "section_type": "footer",
                            "position": 2,
                            "settings": {"background_color": "#f5f5f5", "text_color": "#666666"}
                        }
                    ]
                }
            }
            template_manager.create(default_template)
            logger.info("Default template created.")

    except Exception as e:
        logger.error(f"Error verifying page builder tables: {str(e)}")
        raise
    finally:
        session.close()
    
    logger.info("Page builder migration completed successfully.")

if __name__ == "__main__":
    main()
