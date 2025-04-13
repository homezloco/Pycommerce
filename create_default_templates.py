
"""
Script to create default page templates for the page builder.
"""

import logging
from pycommerce.core.db import SessionLocal
from pycommerce.models.page_builder import PageTemplateManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_default_templates():
    """Create default page templates if they don't exist."""
    session = SessionLocal()
    try:
        template_manager = PageTemplateManager(session)
        
        # Check if we already have templates
        existing_templates = template_manager.list_templates()
        if existing_templates:
            logger.info(f"Found {len(existing_templates)} existing templates - skipping creation")
            return
            
        # Basic page template
        basic_template = {
            "name": "Basic Page",
            "description": "A simple page with header, content, and footer sections",
            "thumbnail_url": "/static/img/templates/basic.jpg",
            "is_system": True,
            "template_data": {
                "sections": [
                    {
                        "section_type": "hero",
                        "settings": {
                            "background": "light",
                            "text_align": "center",
                            "padding": "large"
                        }
                    },
                    {
                        "section_type": "content",
                        "settings": {
                            "background": "white",
                            "width": "normal",
                            "padding": "medium"
                        }
                    },
                    {
                        "section_type": "cta",
                        "settings": {
                            "background": "light",
                            "text_align": "center",
                            "padding": "medium"
                        }
                    }
                ]
            }
        }
        
        # Homepage template
        homepage_template = {
            "name": "Homepage",
            "description": "A template for a store homepage with hero banner, featured products, and testimonials",
            "thumbnail_url": "/static/img/templates/homepage.jpg",
            "is_system": True,
            "template_data": {
                "sections": [
                    {
                        "section_type": "hero",
                        "settings": {
                            "background": "primary",
                            "text_align": "center",
                            "padding": "large"
                        }
                    },
                    {
                        "section_type": "featured_products",
                        "settings": {
                            "background": "white",
                            "width": "wide",
                            "padding": "medium",
                            "products_count": 4
                        }
                    },
                    {
                        "section_type": "content",
                        "settings": {
                            "background": "light",
                            "width": "normal",
                            "padding": "medium"
                        }
                    },
                    {
                        "section_type": "testimonials",
                        "settings": {
                            "background": "white",
                            "text_align": "center",
                            "padding": "medium"
                        }
                    },
                    {
                        "section_type": "cta",
                        "settings": {
                            "background": "primary",
                            "text_align": "center",
                            "padding": "medium"
                        }
                    }
                ]
            }
        }
        
        # About us template
        about_template = {
            "name": "About Us",
            "description": "A template for an about us page with company information and team members",
            "thumbnail_url": "/static/img/templates/about.jpg",
            "is_system": True,
            "template_data": {
                "sections": [
                    {
                        "section_type": "hero",
                        "settings": {
                            "background": "light",
                            "text_align": "center",
                            "padding": "medium"
                        }
                    },
                    {
                        "section_type": "content",
                        "settings": {
                            "background": "white",
                            "width": "normal",
                            "padding": "medium"
                        }
                    },
                    {
                        "section_type": "team",
                        "settings": {
                            "background": "light",
                            "width": "wide",
                            "padding": "medium"
                        }
                    },
                    {
                        "section_type": "cta",
                        "settings": {
                            "background": "primary",
                            "text_align": "center",
                            "padding": "small"
                        }
                    }
                ]
            }
        }
        
        # Create templates
        templates = [basic_template, homepage_template, about_template]
        for template_data in templates:
            template = template_manager.create(template_data)
            logger.info(f"Created template: {template.name} (ID: {template.id})")
            
        logger.info("Default page templates created successfully")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating default templates: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    create_default_templates()
