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
    db_uri = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/pycommerce')
    logger.info(f"Using database URI: {db_uri}")

    # Ensure the database URL is properly formatted
    if db_uri and not db_uri.startswith(('sqlite://', 'postgresql://', 'mysql://')):
        logger.warning(f"Database URI format may be invalid: {db_uri}")
        # Try to fix common issues like missing protocol
        if 'postgres' in db_uri and not db_uri.startswith('postgresql://'):
            db_uri = f"postgresql://{db_uri}"
            logger.info(f"Modified database URI to: {db_uri}")

    try:
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

            logger.info(f"Page builder tables verified successfully:")
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
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        if "Table 'page_sections' is already defined" in str(e):
            logger.info("Tables already exist, continuing with verification...")
            # Continue with verification even if tables already exist
            main()

def create_test_pages():
    """Create test pages for each tenant with proper session handling."""
    logger.info("Checking if page builder tables exist...")
    
    # Create a new session for this operation
    session = SessionLocal()
    
    try:
        # Check if we have all the required tables
        from sqlalchemy import inspect
        inspector = inspect(session.bind)
        tables = inspector.get_table_names()
        logger.info(f"Found tables: {tables}")
        
        required_tables = ['pages', 'page_sections', 'content_blocks', 'page_templates']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            logger.error(f"Missing tables: {missing_tables}")
            return
        
        logger.info("All required tables exist.")
        
        # Get a page manager instance
        page_manager = PageManager(session)
        
        # Get all tenants
        from pycommerce.models.db_registry import Tenant
        tenants = session.query(Tenant).all()
        logger.info(f"Found {len(tenants)} tenants")
        
        # Create a test page for each tenant
        for tenant in tenants:
            logger.info(f"Creating test page for tenant {tenant.name}")
            try:
                # Prepare page data
                page_data = {
                    "title": f"Welcome to {tenant.name}",
                    "slug": "welcome",
                    "meta_title": f"Welcome to {tenant.name} - Home Page",
                    "meta_description": f"This is the welcome page for {tenant.name}",
                    "is_published": True,
                    "layout_data": {
                        "template_id": session.query(PageTemplate.id).first()[0],
                        "sections": [
                            {
                                "type": "header",
                                "settings": {
                                    "heading": f"Welcome to {tenant.name}",
                                    "subheading": "Your one-stop shop for quality products"
                                },
                                "blocks": []
                            },
                            {
                                "type": "content",
                                "settings": {},
                                "blocks": [
                                    {
                                        "type": "text",
                                        "settings": {
                                            "content": f"<h2>About {tenant.name}</h2><p>We offer a wide range of products designed to meet your needs.</p>"
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                }
                
                # Important: We need to use the session directly for CRUD operations
                new_page = Page(
                    tenant_id=tenant.id,
                    title=page_data["title"],
                    slug=page_data["slug"],
                    meta_title=page_data["meta_title"],
                    meta_description=page_data["meta_description"],
                    is_published=page_data["is_published"],
                    layout_data=page_data["layout_data"]
                )
                
                session.add(new_page)
                session.commit()
                
                logger.info(f"Successfully created test page for {tenant.name}")
                
            except Exception as e:
                session.rollback()
                logger.error(f"Error creating test page: {str(e)}")
        
        # Commit all changes
        logger.info("Page builder test completed successfully.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error in create_test_pages: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
    # After the migration is complete, create test pages
    create_test_pages()