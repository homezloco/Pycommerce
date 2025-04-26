#!/usr/bin/env python3
"""Script to add additional advanced page templates to the system.

This script will create four new templates:
1. Blog Page - For displaying blog posts and articles
2. FAQ Page - For frequently asked questions 
3. Services Page - For highlighting services offered
4. Portfolio Page - For showcasing projects or work
"""

import json
import logging
import sys
import uuid
from typing import Dict, Any, List

from pycommerce.core.db import SessionLocal
from pycommerce.models.page_builder import PageTemplateManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_advanced_templates():
    """Create advanced page templates for the system."""
    session = SessionLocal()
    try:
        template_manager = PageTemplateManager(session)
        
        # Check existing templates
        existing_templates = template_manager.list_templates()
        existing_names = [t.name for t in existing_templates]
        logger.info(f"Found {len(existing_templates)} existing templates: {existing_names}")
        
        created_count = 0
        
        # 1. Blog Page Template
        if "Blog Page" not in existing_names:
            blog_template = {
                "name": "Blog Page",
                "description": "A template for blog posts and articles with sidebar and featured content",
                "thumbnail_url": "/static/img/templates/blog.jpg",
                "is_system": True,
                "template_data": {
                    "sections": [
                        {
                            "section_type": "header",
                            "settings": {
                                "background_color": "#f8f9fa",
                                "text_color": "#212529",
                                "alignment": "center",
                                "padding": "medium",
                                "show_title": True,
                                "show_date": True
                            }
                        },
                        {
                            "section_type": "blog_layout",
                            "settings": {
                                "background_color": "#ffffff",
                                "layout": "sidebar_right",
                                "content_width": "medium",
                                "sidebar_width": "narrow"
                            }
                        },
                        {
                            "section_type": "featured_posts",
                            "settings": {
                                "background_color": "#f8f9fa",
                                "text_color": "#212529",
                                "heading": "Featured Posts",
                                "layout": "grid",
                                "columns": 3
                            }
                        },
                        {
                            "section_type": "newsletter",
                            "settings": {
                                "background_color": "#212529",
                                "text_color": "#ffffff",
                                "alignment": "center",
                                "padding": "large",
                                "heading": "Subscribe to Our Newsletter",
                                "subheading": "Stay updated with our latest articles and news",
                                "button_text": "Subscribe",
                                "button_style": "primary"
                            }
                        }
                    ]
                }
            }
            
            template = template_manager.create(blog_template)
            logger.info(f"Created blog template: {template.name} (ID: {template.id})")
            created_count += 1
        else:
            logger.info("Blog Page template already exists, skipping")
        
        # 2. FAQ Page Template
        if "FAQ Page" not in existing_names:
            faq_template = {
                "name": "FAQ Page",
                "description": "A template for frequently asked questions with accordion sections",
                "thumbnail_url": "/static/img/templates/faq.jpg",
                "is_system": True,
                "template_data": {
                    "sections": [
                        {
                            "section_type": "header",
                            "settings": {
                                "background_color": "#f8f9fa",
                                "text_color": "#212529",
                                "alignment": "center",
                                "padding": "medium",
                                "heading": "Frequently Asked Questions",
                                "subheading": "Find answers to common questions about our products and services"
                            }
                        },
                        {
                            "section_type": "search",
                            "settings": {
                                "background_color": "#ffffff",
                                "text_color": "#212529",
                                "alignment": "center",
                                "padding": "small",
                                "placeholder": "What are you looking for?",
                                "button_text": "Search"
                            }
                        },
                        {
                            "section_type": "faq_categories",
                            "settings": {
                                "background_color": "#f8f9fa",
                                "text_color": "#212529",
                                "columns": 4,
                                "style": "cards",
                                "show_icons": True,
                                "show_count": True
                            }
                        },
                        {
                            "section_type": "accordion",
                            "settings": {
                                "background_color": "#ffffff",
                                "text_color": "#212529",
                                "padding": "medium",
                                "style": "accordion",
                                "heading": "General Questions",
                                "expandable": True,
                                "initially_expanded": False
                            }
                        },
                        {
                            "section_type": "cta",
                            "settings": {
                                "background_color": "#f8f9fa",
                                "text_color": "#212529",
                                "alignment": "center",
                                "padding": "medium",
                                "heading": "Still Have Questions?",
                                "subheading": "Contact our support team for personalized assistance",
                                "button_text": "Contact Us",
                                "button_style": "primary",
                                "button_size": "large",
                                "button_url": "/contact"
                            }
                        }
                    ]
                }
            }
            
            template = template_manager.create(faq_template)
            logger.info(f"Created FAQ template: {template.name} (ID: {template.id})")
            created_count += 1
        else:
            logger.info("FAQ Page template already exists, skipping")
        
        # 3. Services Page Template
        if "Services Page" not in existing_names:
            services_template = {
                "name": "Services Page",
                "description": "A template for showcasing services with features and pricing options",
                "thumbnail_url": "/static/img/templates/services.jpg",
                "is_system": True,
                "template_data": {
                    "sections": [
                        {
                            "section_type": "hero",
                            "settings": {
                                "background_color": "#212529",
                                "text_color": "#ffffff",
                                "alignment": "center",
                                "height": "medium",
                                "padding": "large",
                                "heading": "Our Services",
                                "subheading": "Professional solutions tailored to your needs",
                                "button_text": "Get Started",
                                "button_style": "outline-light",
                                "button_size": "large",
                                "button_url": "#services"
                            }
                        },
                        {
                            "section_type": "text",
                            "settings": {
                                "background_color": "#ffffff",
                                "text_color": "#212529",
                                "alignment": "center",
                                "padding": "medium",
                                "heading": "Our Service Offerings",
                                "content": "We provide comprehensive solutions to help your business grow"
                            }
                        },
                        {
                            "section_type": "services",
                            "settings": {
                                "background_color": "#f8f9fa",
                                "text_color": "#212529",
                                "columns": 3,
                                "style": "cards",
                                "padding": "medium",
                                "show_icon": True,
                                "show_button": True,
                                "button_text": "Learn More"
                            }
                        },
                        {
                            "section_type": "pricing",
                            "settings": {
                                "background_color": "#ffffff",
                                "text_color": "#212529",
                                "alignment": "center",
                                "padding": "medium",
                                "heading": "Service Packages",
                                "subheading": "Choose the package that best fits your business needs",
                                "columns": 3,
                                "style": "pricing"
                            }
                        },
                        {
                            "section_type": "testimonials",
                            "settings": {
                                "background_color": "#f8f9fa",
                                "text_color": "#212529",
                                "alignment": "center",
                                "padding": "medium",
                                "heading": "What Our Clients Say",
                                "style": "cards",
                                "show_image": True,
                                "show_company": True
                            }
                        },
                        {
                            "section_type": "cta",
                            "settings": {
                                "background_color": "#212529",
                                "text_color": "#ffffff",
                                "alignment": "center",
                                "padding": "large",
                                "heading": "Ready to Get Started?",
                                "subheading": "Contact us today to discuss how our services can help your business",
                                "button_text": "Contact Us",
                                "button_style": "primary",
                                "button_size": "large",
                                "button_url": "/contact"
                            }
                        }
                    ]
                }
            }
            
            template = template_manager.create(services_template)
            logger.info(f"Created services template: {template.name} (ID: {template.id})")
            created_count += 1
        else:
            logger.info("Services Page template already exists, skipping")
        
        # 4. Portfolio Page Template
        if "Portfolio Page" not in existing_names:
            portfolio_template = {
                "name": "Portfolio Page",
                "description": "A template for showcasing projects, work, or products in a portfolio format",
                "thumbnail_url": "/static/img/templates/portfolio.jpg",
                "is_system": True,
                "template_data": {
                    "sections": [
                        {
                            "section_type": "header",
                            "settings": {
                                "background_color": "#212529",
                                "text_color": "#ffffff",
                                "alignment": "center",
                                "padding": "medium",
                                "heading": "Our Portfolio",
                                "subheading": "A showcase of our best work and projects"
                            }
                        },
                        {
                            "section_type": "filters",
                            "settings": {
                                "background_color": "#f8f9fa",
                                "text_color": "#212529",
                                "alignment": "center",
                                "padding": "small",
                                "style": "buttons",
                                "active_filter": "All"
                            }
                        },
                        {
                            "section_type": "portfolio",
                            "settings": {
                                "background_color": "#ffffff",
                                "padding": "medium",
                                "columns": 3,
                                "gap": "medium",
                                "layout": "masonry",
                                "hover_effect": "zoom",
                                "show_title": True,
                                "show_category": True
                            }
                        },
                        {
                            "section_type": "skills",
                            "settings": {
                                "background_color": "#f8f9fa",
                                "text_color": "#212529",
                                "alignment": "center",
                                "padding": "medium",
                                "heading": "Our Skills",
                                "subheading": "Expertise that drives our success",
                                "show_percentage": True,
                                "bar_color": "#007bff"
                            }
                        },
                        {
                            "section_type": "process",
                            "settings": {
                                "background_color": "#ffffff",
                                "text_color": "#212529",
                                "alignment": "center",
                                "padding": "medium",
                                "heading": "Our Process",
                                "subheading": "How we approach each project to ensure success",
                                "style": "timeline",
                                "show_icons": True
                            }
                        },
                        {
                            "section_type": "cta",
                            "settings": {
                                "background_color": "#212529",
                                "text_color": "#ffffff",
                                "alignment": "center",
                                "padding": "large",
                                "heading": "Let's Work Together",
                                "subheading": "Ready to discuss your next project?",
                                "button_text": "Get in Touch",
                                "button_style": "primary",
                                "button_size": "large",
                                "button_url": "/contact"
                            }
                        }
                    ]
                }
            }
            
            template = template_manager.create(portfolio_template)
            logger.info(f"Created portfolio template: {template.name} (ID: {template.id})")
            created_count += 1
        else:
            logger.info("Portfolio Page template already exists, skipping")
        
        logger.info(f"Created {created_count} new page templates")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating advanced templates: {str(e)}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    logger.info("Creating advanced page templates...")
    create_advanced_templates()
    logger.info("Finished creating advanced templates")
    sys.exit(0)