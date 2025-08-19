#!/usr/bin/env python3
"""Script to add additional page templates to the system.

This script will create three new templates:
1. E-commerce Homepage - A full-featured homepage template with product showcase
2. About Us Page - A template with team/company information sections
3. Product Category Page - A template focused on displaying product categories
"""

import logging
import json
from pycommerce.core.db import SessionLocal
from pycommerce.models.page_builder import PageTemplateManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_additional_templates():
    """Create additional page templates for the system."""
    session = SessionLocal()
    try:
        template_manager = PageTemplateManager(session)
        
        # Check existing templates
        existing_templates = template_manager.list_templates()
        existing_names = [t.name for t in existing_templates]
        logger.info(f"Found {len(existing_templates)} existing templates: {existing_names}")
        
        # 1. E-commerce Homepage Template
        ecommerce_homepage = {
            "name": "E-commerce Homepage",
            "description": "A full-featured homepage with hero banner, featured products, and promotional sections",
            "thumbnail_url": "/static/img/templates/ecommerce-home.jpg",
            "is_system": True,
            "template_data": {
                "sections": [
                    {
                        "section_type": "hero_banner",
                        "settings": {
                            "background_color": "#f8f9fa",
                            "text_color": "#212529",
                            "height": "large",
                            "alignment": "center",
                            "overlay": True,
                            "button_style": "primary"
                        }
                    },
                    {
                        "section_type": "featured_categories",
                        "settings": {
                            "background_color": "#ffffff",
                            "heading": "Shop by Category",
                            "columns": 3,
                            "padding": "medium"
                        }
                    },
                    {
                        "section_type": "featured_products",
                        "settings": {
                            "background_color": "#f8f9fa",
                            "heading": "Featured Products",
                            "products_count": 4,
                            "layout": "grid",
                            "show_prices": True
                        }
                    },
                    {
                        "section_type": "promotion_banner",
                        "settings": {
                            "background_color": "#212529",
                            "text_color": "#ffffff",
                            "padding": "large",
                            "alignment": "center",
                            "button_style": "outline-light"
                        }
                    },
                    {
                        "section_type": "testimonials",
                        "settings": {
                            "background_color": "#ffffff",
                            "heading": "What Our Customers Say",
                            "columns": 3,
                            "style": "cards"
                        }
                    },
                    {
                        "section_type": "newsletter",
                        "settings": {
                            "background_color": "#f8f9fa",
                            "text_color": "#212529",
                            "padding": "medium",
                            "alignment": "center"
                        }
                    }
                ]
            }
        }
        
        # 2. About Us Page Template
        about_us = {
            "name": "About Us Page",
            "description": "A template for company information with team members and values sections",
            "thumbnail_url": "/static/img/templates/about-us.jpg",
            "is_system": True,
            "template_data": {
                "sections": [
                    {
                        "section_type": "page_header",
                        "settings": {
                            "background_color": "#f8f9fa",
                            "text_color": "#212529",
                            "alignment": "center",
                            "padding": "large"
                        }
                    },
                    {
                        "section_type": "company_intro",
                        "settings": {
                            "background_color": "#ffffff",
                            "layout": "image_text",
                            "image_position": "left",
                            "padding": "medium"
                        }
                    },
                    {
                        "section_type": "values",
                        "settings": {
                            "background_color": "#f8f9fa",
                            "columns": 3,
                            "style": "cards",
                            "padding": "medium"
                        }
                    },
                    {
                        "section_type": "team_members",
                        "settings": {
                            "background_color": "#ffffff",
                            "heading": "Our Team",
                            "columns": 4,
                            "style": "circle"
                        }
                    },
                    {
                        "section_type": "cta",
                        "settings": {
                            "background_color": "#212529",
                            "text_color": "#ffffff",
                            "alignment": "center",
                            "padding": "medium"
                        }
                    }
                ]
            }
        }
        
        # 3. Product Category Page Template
        category_page = {
            "name": "Product Category Page",
            "description": "A template designed for showcasing product categories with filters and sorting options",
            "thumbnail_url": "/static/img/templates/category-page.jpg",
            "is_system": True,
            "template_data": {
                "sections": [
                    {
                        "section_type": "category_header",
                        "settings": {
                            "background_color": "#f8f9fa",
                            "text_color": "#212529",
                            "alignment": "center",
                            "show_breadcrumbs": True
                        }
                    },
                    {
                        "section_type": "product_filter",
                        "settings": {
                            "background_color": "#ffffff",
                            "layout": "sidebar",
                            "show_filters": True,
                            "show_sorting": True
                        }
                    },
                    {
                        "section_type": "product_grid",
                        "settings": {
                            "background_color": "#ffffff",
                            "columns": 3,
                            "products_per_page": 12,
                            "show_pagination": True
                        }
                    },
                    {
                        "section_type": "related_categories",
                        "settings": {
                            "background_color": "#f8f9fa",
                            "heading": "Related Categories",
                            "columns": 4,
                            "style": "cards"
                        }
                    }
                ]
            }
        }
        
        # 4. Contact Page Template
        contact_page = {
            "name": "Contact Page",
            "description": "A template for contact information with map and contact form",
            "thumbnail_url": "/static/img/templates/contact-page.jpg",
            "is_system": True,
            "template_data": {
                "sections": [
                    {
                        "section_type": "page_header",
                        "settings": {
                            "background_color": "#f8f9fa",
                            "text_color": "#212529",
                            "alignment": "center",
                            "padding": "medium"
                        }
                    },
                    {
                        "section_type": "contact_info",
                        "settings": {
                            "background_color": "#ffffff",
                            "layout": "columns",
                            "columns": 3,
                            "show_icons": True
                        }
                    },
                    {
                        "section_type": "contact_form",
                        "settings": {
                            "background_color": "#f8f9fa",
                            "text_color": "#212529",
                            "form_width": "medium",
                            "show_map": True
                        }
                    },
                    {
                        "section_type": "business_hours",
                        "settings": {
                            "background_color": "#ffffff",
                            "text_color": "#212529",
                            "alignment": "center",
                            "padding": "medium"
                        }
                    }
                ]
            }
        }
        
        # List of templates to create
        new_templates = [
            ("E-commerce Homepage", ecommerce_homepage),
            ("About Us Page", about_us),
            ("Product Category Page", category_page),
            ("Contact Page", contact_page)
        ]
        
        # Create each template if it doesn't already exist
        for name, template_data in new_templates:
            if name not in existing_names:
                template = template_manager.create(template_data)
                logger.info(f"Created template: {template.name} (ID: {template.id})")
            else:
                logger.info(f"Template '{name}' already exists, skipping creation")
                
        logger.info("Template creation completed")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating templates: {str(e)}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    create_additional_templates()