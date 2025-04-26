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
from typing import Dict, Any, List, Optional

from app import app
from pycommerce.models.page_builder import PageTemplateManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_blog_template(template_manager: PageTemplateManager) -> str:
    """Create a blog page template."""
    template_id = str(uuid.uuid4())
    template_name = "Blog Page"
    template_description = "A template for blog posts and articles with sidebar and featured content"
    is_system_template = True

    sections = [
        {
            "id": str(uuid.uuid4()),
            "name": "page_header",
            "order": 1,
            "settings": {
                "background_color": "#f8f9fa",
                "text_color": "#212529",
                "alignment": "center",
                "padding": "medium",
                "show_title": True,
                "show_date": True
            },
            "blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "text",
                    "content": "<h1>Blog</h1><p>Latest news and articles</p>",
                    "order": 1,
                    "settings": {}
                }
            ]
        },
        {
            "id": str(uuid.uuid4()),
            "name": "blog_layout",
            "order": 2,
            "settings": {
                "background_color": "#ffffff",
                "layout": "sidebar_right",
                "content_width": "medium",
                "sidebar_width": "narrow"
            },
            "blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "blog_posts",
                    "content": "{}",
                    "order": 1,
                    "settings": {
                        "posts_per_page": 5,
                        "show_featured_image": True,
                        "show_excerpt": True,
                        "show_author": True,
                        "show_date": True,
                        "show_read_more": True
                    }
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "sidebar",
                    "content": "{}",
                    "order": 2,
                    "settings": {
                        "show_categories": True,
                        "show_recent_posts": True,
                        "show_tags": True,
                        "show_search": True
                    }
                }
            ]
        },
        {
            "id": str(uuid.uuid4()),
            "name": "featured_posts",
            "order": 3,
            "settings": {
                "background_color": "#f8f9fa",
                "text_color": "#212529",
                "heading": "Featured Posts",
                "layout": "grid",
                "columns": 3
            },
            "blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "text",
                    "content": "<h2>Featured Posts</h2>",
                    "order": 1,
                    "settings": {}
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "featured_posts",
                    "content": "{}",
                    "order": 2,
                    "settings": {
                        "count": 3,
                        "show_image": True,
                        "show_title": True,
                        "show_excerpt": True
                    }
                }
            ]
        },
        {
            "id": str(uuid.uuid4()),
            "name": "newsletter_signup",
            "order": 4,
            "settings": {
                "background_color": "#212529",
                "text_color": "#ffffff",
                "alignment": "center",
                "padding": "large"
            },
            "blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "text",
                    "content": "<h2>Subscribe to Our Newsletter</h2><p>Stay updated with our latest articles and news</p>",
                    "order": 1,
                    "settings": {}
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "form",
                    "content": "{}",
                    "order": 2,
                    "settings": {
                        "form_type": "newsletter",
                        "button_text": "Subscribe",
                        "button_style": "primary"
                    }
                }
            ]
        }
    ]

    template_manager.create_template(
        template_id,
        template_name,
        template_description,
        is_system_template,
        sections
    )
    
    logger.info(f"Created blog template: {template_name} with ID: {template_id}")
    return template_id


def create_faq_template(template_manager: PageTemplateManager) -> str:
    """Create a FAQ page template."""
    template_id = str(uuid.uuid4())
    template_name = "FAQ Page"
    template_description = "A template for frequently asked questions with accordion sections"
    is_system_template = True

    sections = [
        {
            "id": str(uuid.uuid4()),
            "name": "page_header",
            "order": 1,
            "settings": {
                "background_color": "#f8f9fa",
                "text_color": "#212529",
                "alignment": "center",
                "padding": "medium"
            },
            "blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "text",
                    "content": "<h1>Frequently Asked Questions</h1><p>Find answers to common questions about our products and services</p>",
                    "order": 1,
                    "settings": {}
                }
            ]
        },
        {
            "id": str(uuid.uuid4()),
            "name": "search_section",
            "order": 2,
            "settings": {
                "background_color": "#ffffff",
                "text_color": "#212529",
                "alignment": "center",
                "padding": "small"
            },
            "blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "text",
                    "content": "<p>Search our FAQ database for quick answers</p>",
                    "order": 1,
                    "settings": {}
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "search",
                    "content": "{}",
                    "order": 2,
                    "settings": {
                        "placeholder": "What are you looking for?",
                        "button_text": "Search"
                    }
                }
            ]
        },
        {
            "id": str(uuid.uuid4()),
            "name": "faq_categories",
            "order": 3,
            "settings": {
                "background_color": "#f8f9fa",
                "text_color": "#212529",
                "columns": 4,
                "style": "cards"
            },
            "blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "text",
                    "content": "<h2>FAQ Categories</h2>",
                    "order": 1,
                    "settings": {}
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "categories",
                    "content": "{}",
                    "order": 2,
                    "settings": {
                        "show_icons": True,
                        "show_count": True
                    }
                }
            ]
        },
        {
            "id": str(uuid.uuid4()),
            "name": "faq_accordion",
            "order": 4,
            "settings": {
                "background_color": "#ffffff",
                "text_color": "#212529",
                "padding": "medium",
                "style": "accordion"
            },
            "blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "text",
                    "content": "<h2>General Questions</h2>",
                    "order": 1,
                    "settings": {}
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "accordion",
                    "content": json.dumps([
                        {
                            "question": "How do I create an account?",
                            "answer": "You can create an account by clicking the 'Sign Up' button in the top right corner of our website."
                        },
                        {
                            "question": "What payment methods do you accept?",
                            "answer": "We accept major credit cards, PayPal, and bank transfers."
                        },
                        {
                            "question": "How can I track my order?",
                            "answer": "You can track your order by logging into your account and visiting the 'Orders' section."
                        },
                        {
                            "question": "What is your return policy?",
                            "answer": "We offer a 30-day return policy for all unused and unopened products."
                        },
                        {
                            "question": "How can I contact customer support?",
                            "answer": "You can reach our customer support team through email, phone, or live chat on our website."
                        }
                    ]),
                    "order": 2,
                    "settings": {
                        "expandable": True,
                        "initially_expanded": False
                    }
                }
            ]
        },
        {
            "id": str(uuid.uuid4()),
            "name": "contact_section",
            "order": 5,
            "settings": {
                "background_color": "#f8f9fa",
                "text_color": "#212529",
                "alignment": "center",
                "padding": "medium"
            },
            "blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "text",
                    "content": "<h2>Still Have Questions?</h2><p>Contact our support team for personalized assistance</p>",
                    "order": 1,
                    "settings": {}
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "button",
                    "content": "Contact Us",
                    "order": 2,
                    "settings": {
                        "url": "/contact",
                        "style": "primary",
                        "size": "large"
                    }
                }
            ]
        }
    ]

    template_manager.create_template(
        template_id,
        template_name,
        template_description,
        is_system_template,
        sections
    )
    
    logger.info(f"Created FAQ template: {template_name} with ID: {template_id}")
    return template_id


def create_services_template(template_manager: PageTemplateManager) -> str:
    """Create a services page template."""
    template_id = str(uuid.uuid4())
    template_name = "Services Page"
    template_description = "A template for showcasing services with features and pricing options"
    is_system_template = True

    sections = [
        {
            "id": str(uuid.uuid4()),
            "name": "hero_section",
            "order": 1,
            "settings": {
                "background_color": "#212529",
                "text_color": "#ffffff",
                "alignment": "center",
                "height": "medium",
                "padding": "large"
            },
            "blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "text",
                    "content": "<h1>Our Services</h1><p>Professional solutions tailored to your needs</p>",
                    "order": 1,
                    "settings": {}
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "button",
                    "content": "Get Started",
                    "order": 2,
                    "settings": {
                        "url": "#services",
                        "style": "outline-light",
                        "size": "large"
                    }
                }
            ]
        },
        {
            "id": str(uuid.uuid4()),
            "name": "services_overview",
            "order": 2,
            "settings": {
                "background_color": "#ffffff",
                "text_color": "#212529",
                "alignment": "center",
                "padding": "medium"
            },
            "blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "text",
                    "content": "<h2 id='services'>Our Service Offerings</h2><p>We provide comprehensive solutions to help your business grow</p>",
                    "order": 1,
                    "settings": {}
                }
            ]
        },
        {
            "id": str(uuid.uuid4()),
            "name": "services_grid",
            "order": 3,
            "settings": {
                "background_color": "#f8f9fa",
                "text_color": "#212529",
                "columns": 3,
                "style": "cards",
                "padding": "medium"
            },
            "blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "service_card",
                    "content": json.dumps({
                        "title": "Consulting",
                        "description": "Expert advice and guidance for your business challenges",
                        "icon": "users",
                        "link": "/services/consulting"
                    }),
                    "order": 1,
                    "settings": {
                        "show_icon": True,
                        "show_button": True,
                        "button_text": "Learn More"
                    }
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "service_card",
                    "content": json.dumps({
                        "title": "Implementation",
                        "description": "End-to-end implementation of solutions tailored to your needs",
                        "icon": "cogs",
                        "link": "/services/implementation"
                    }),
                    "order": 2,
                    "settings": {
                        "show_icon": True,
                        "show_button": True,
                        "button_text": "Learn More"
                    }
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "service_card",
                    "content": json.dumps({
                        "title": "Support",
                        "description": "Ongoing support and maintenance for your systems",
                        "icon": "headset",
                        "link": "/services/support"
                    }),
                    "order": 3,
                    "settings": {
                        "show_icon": True,
                        "show_button": True,
                        "button_text": "Learn More"
                    }
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "service_card",
                    "content": json.dumps({
                        "title": "Training",
                        "description": "Comprehensive training programs for your team",
                        "icon": "graduation-cap",
                        "link": "/services/training"
                    }),
                    "order": 4,
                    "settings": {
                        "show_icon": True,
                        "show_button": True,
                        "button_text": "Learn More"
                    }
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "service_card",
                    "content": json.dumps({
                        "title": "Development",
                        "description": "Custom software development for your business needs",
                        "icon": "code",
                        "link": "/services/development"
                    }),
                    "order": 5,
                    "settings": {
                        "show_icon": True,
                        "show_button": True,
                        "button_text": "Learn More"
                    }
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "service_card",
                    "content": json.dumps({
                        "title": "Analysis",
                        "description": "Data analysis and reporting to drive business insights",
                        "icon": "chart-bar",
                        "link": "/services/analysis"
                    }),
                    "order": 6,
                    "settings": {
                        "show_icon": True,
                        "show_button": True,
                        "button_text": "Learn More"
                    }
                }
            ]
        },
        {
            "id": str(uuid.uuid4()),
            "name": "pricing_section",
            "order": 4,
            "settings": {
                "background_color": "#ffffff",
                "text_color": "#212529",
                "alignment": "center",
                "padding": "medium"
            },
            "blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "text",
                    "content": "<h2>Service Packages</h2><p>Choose the package that best fits your business needs</p>",
                    "order": 1,
                    "settings": {}
                }
            ]
        },
        {
            "id": str(uuid.uuid4()),
            "name": "pricing_tables",
            "order": 5,
            "settings": {
                "background_color": "#ffffff",
                "text_color": "#212529",
                "columns": 3,
                "style": "pricing",
                "padding": "medium"
            },
            "blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "pricing_table",
                    "content": json.dumps({
                        "title": "Basic",
                        "price": "$99",
                        "period": "per month",
                        "features": [
                            "2 service areas",
                            "5 hours of consultation",
                            "Basic support",
                            "Monthly reporting"
                        ],
                        "popular": False
                    }),
                    "order": 1,
                    "settings": {
                        "button_text": "Choose Plan",
                        "button_style": "outline-primary"
                    }
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "pricing_table",
                    "content": json.dumps({
                        "title": "Professional",
                        "price": "$299",
                        "period": "per month",
                        "features": [
                            "5 service areas",
                            "15 hours of consultation",
                            "Priority support",
                            "Weekly reporting",
                            "2 training sessions"
                        ],
                        "popular": True
                    }),
                    "order": 2,
                    "settings": {
                        "button_text": "Choose Plan",
                        "button_style": "primary"
                    }
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "pricing_table",
                    "content": json.dumps({
                        "title": "Enterprise",
                        "price": "$999",
                        "period": "per month",
                        "features": [
                            "All service areas",
                            "Unlimited consultation",
                            "24/7 premium support",
                            "Daily reporting",
                            "Unlimited training",
                            "Dedicated account manager"
                        ],
                        "popular": False
                    }),
                    "order": 3,
                    "settings": {
                        "button_text": "Choose Plan",
                        "button_style": "outline-primary"
                    }
                }
            ]
        },
        {
            "id": str(uuid.uuid4()),
            "name": "testimonials",
            "order": 6,
            "settings": {
                "background_color": "#f8f9fa",
                "text_color": "#212529",
                "alignment": "center",
                "padding": "medium"
            },
            "blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "text",
                    "content": "<h2>What Our Clients Say</h2>",
                    "order": 1,
                    "settings": {}
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "testimonials",
                    "content": json.dumps([
                        {
                            "name": "John Smith",
                            "company": "ABC Corp",
                            "text": "The consulting services provided were exceptional. Our business has seen a 30% increase in efficiency.",
                            "image": ""
                        },
                        {
                            "name": "Jane Doe",
                            "company": "XYZ Inc",
                            "text": "The implementation team was professional and thorough. They delivered on time and within budget.",
                            "image": ""
                        },
                        {
                            "name": "Robert Johnson",
                            "company": "123 Industries",
                            "text": "The ongoing support has been invaluable to our operations. Quick response times and expert solutions.",
                            "image": ""
                        }
                    ]),
                    "order": 2,
                    "settings": {
                        "style": "cards",
                        "show_image": True,
                        "show_company": True
                    }
                }
            ]
        },
        {
            "id": str(uuid.uuid4()),
            "name": "cta_section",
            "order": 7,
            "settings": {
                "background_color": "#212529",
                "text_color": "#ffffff",
                "alignment": "center",
                "padding": "large"
            },
            "blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "text",
                    "content": "<h2>Ready to Get Started?</h2><p>Contact us today to discuss how our services can help your business</p>",
                    "order": 1,
                    "settings": {}
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "button",
                    "content": "Contact Us",
                    "order": 2,
                    "settings": {
                        "url": "/contact",
                        "style": "primary",
                        "size": "large"
                    }
                }
            ]
        }
    ]

    template_manager.create_template(
        template_id,
        template_name,
        template_description,
        is_system_template,
        sections
    )
    
    logger.info(f"Created services template: {template_name} with ID: {template_id}")
    return template_id


def create_portfolio_template(template_manager: PageTemplateManager) -> str:
    """Create a portfolio page template."""
    template_id = str(uuid.uuid4())
    template_name = "Portfolio Page"
    template_description = "A template for showcasing projects, work, or products in a portfolio format"
    is_system_template = True

    sections = [
        {
            "id": str(uuid.uuid4()),
            "name": "page_header",
            "order": 1,
            "settings": {
                "background_color": "#212529",
                "text_color": "#ffffff",
                "alignment": "center",
                "padding": "medium"
            },
            "blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "text",
                    "content": "<h1>Our Portfolio</h1><p>A showcase of our best work and projects</p>",
                    "order": 1,
                    "settings": {}
                }
            ]
        },
        {
            "id": str(uuid.uuid4()),
            "name": "portfolio_filters",
            "order": 2,
            "settings": {
                "background_color": "#f8f9fa",
                "text_color": "#212529",
                "alignment": "center",
                "padding": "small"
            },
            "blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "filters",
                    "content": json.dumps([
                        "All",
                        "Web Design",
                        "Mobile Apps",
                        "Branding",
                        "Print"
                    ]),
                    "order": 1,
                    "settings": {
                        "active_filter": "All",
                        "style": "buttons"
                    }
                }
            ]
        },
        {
            "id": str(uuid.uuid4()),
            "name": "portfolio_grid",
            "order": 3,
            "settings": {
                "background_color": "#ffffff",
                "padding": "medium",
                "columns": 3,
                "gap": "medium",
                "layout": "masonry"
            },
            "blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "portfolio_item",
                    "content": json.dumps({
                        "title": "E-commerce Website",
                        "category": "Web Design",
                        "description": "A modern e-commerce platform with integrated payment processing and inventory management.",
                        "image": "",
                        "link": "/portfolio/ecommerce-website"
                    }),
                    "order": 1,
                    "settings": {
                        "hover_effect": "zoom",
                        "show_title": True,
                        "show_category": True
                    }
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "portfolio_item",
                    "content": json.dumps({
                        "title": "Mobile Banking App",
                        "category": "Mobile Apps",
                        "description": "A secure mobile banking application with biometric authentication and real-time transaction tracking.",
                        "image": "",
                        "link": "/portfolio/mobile-banking-app"
                    }),
                    "order": 2,
                    "settings": {
                        "hover_effect": "zoom",
                        "show_title": True,
                        "show_category": True
                    }
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "portfolio_item",
                    "content": json.dumps({
                        "title": "Restaurant Branding",
                        "category": "Branding",
                        "description": "Complete brand identity for a high-end restaurant, including logo, color palette, and brand guidelines.",
                        "image": "",
                        "link": "/portfolio/restaurant-branding"
                    }),
                    "order": 3,
                    "settings": {
                        "hover_effect": "zoom",
                        "show_title": True,
                        "show_category": True
                    }
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "portfolio_item",
                    "content": json.dumps({
                        "title": "Corporate Annual Report",
                        "category": "Print",
                        "description": "Design and layout of a 45-page annual report for a Fortune 500 company.",
                        "image": "",
                        "link": "/portfolio/annual-report"
                    }),
                    "order": 4,
                    "settings": {
                        "hover_effect": "zoom",
                        "show_title": True,
                        "show_category": True
                    }
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "portfolio_item",
                    "content": json.dumps({
                        "title": "Fitness Tracking App",
                        "category": "Mobile Apps",
                        "description": "A comprehensive fitness tracking application with workout plans, nutrition tracking, and progress visualization.",
                        "image": "",
                        "link": "/portfolio/fitness-app"
                    }),
                    "order": 5,
                    "settings": {
                        "hover_effect": "zoom",
                        "show_title": True,
                        "show_category": True
                    }
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "portfolio_item",
                    "content": json.dumps({
                        "title": "Tech Startup Website",
                        "category": "Web Design",
                        "description": "A modern, responsive website for a tech startup with interactive elements and animations.",
                        "image": "",
                        "link": "/portfolio/tech-startup"
                    }),
                    "order": 6,
                    "settings": {
                        "hover_effect": "zoom",
                        "show_title": True,
                        "show_category": True
                    }
                }
            ]
        },
        {
            "id": str(uuid.uuid4()),
            "name": "skills_section",
            "order": 4,
            "settings": {
                "background_color": "#f8f9fa",
                "text_color": "#212529",
                "alignment": "center",
                "padding": "medium"
            },
            "blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "text",
                    "content": "<h2>Our Skills</h2><p>Expertise that drives our success</p>",
                    "order": 1,
                    "settings": {}
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "skills",
                    "content": json.dumps([
                        {
                            "name": "Web Development",
                            "percentage": 95
                        },
                        {
                            "name": "Mobile Development",
                            "percentage": 90
                        },
                        {
                            "name": "UI/UX Design",
                            "percentage": 85
                        },
                        {
                            "name": "Branding",
                            "percentage": 80
                        },
                        {
                            "name": "Print Design",
                            "percentage": 75
                        }
                    ]),
                    "order": 2,
                    "settings": {
                        "show_percentage": True,
                        "bar_color": "#007bff"
                    }
                }
            ]
        },
        {
            "id": str(uuid.uuid4()),
            "name": "process_section",
            "order": 5,
            "settings": {
                "background_color": "#ffffff",
                "text_color": "#212529",
                "alignment": "center",
                "padding": "medium"
            },
            "blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "text",
                    "content": "<h2>Our Process</h2><p>How we approach each project to ensure success</p>",
                    "order": 1,
                    "settings": {}
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "process_steps",
                    "content": json.dumps([
                        {
                            "title": "Discovery",
                            "description": "We start by understanding your requirements, goals, and target audience.",
                            "icon": "search"
                        },
                        {
                            "title": "Planning",
                            "description": "We develop a comprehensive project plan with milestones and deliverables.",
                            "icon": "clipboard"
                        },
                        {
                            "title": "Execution",
                            "description": "Our team gets to work, implementing the plan with regular updates and reviews.",
                            "icon": "cogs"
                        },
                        {
                            "title": "Delivery",
                            "description": "We finalize the project, conduct thorough testing, and prepare for launch.",
                            "icon": "rocket"
                        },
                        {
                            "title": "Support",
                            "description": "We provide ongoing support and maintenance to ensure long-term success.",
                            "icon": "headset"
                        }
                    ]),
                    "order": 2,
                    "settings": {
                        "style": "timeline",
                        "show_icons": True
                    }
                }
            ]
        },
        {
            "id": str(uuid.uuid4()),
            "name": "cta_section",
            "order": 6,
            "settings": {
                "background_color": "#212529",
                "text_color": "#ffffff",
                "alignment": "center",
                "padding": "large"
            },
            "blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "text",
                    "content": "<h2>Let's Work Together</h2><p>Ready to discuss your next project?</p>",
                    "order": 1,
                    "settings": {}
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "button",
                    "content": "Get in Touch",
                    "order": 2,
                    "settings": {
                        "url": "/contact",
                        "style": "primary",
                        "size": "large"
                    }
                }
            ]
        }
    ]

    template_manager.create_template(
        template_id,
        template_name,
        template_description,
        is_system_template,
        sections
    )
    
    logger.info(f"Created portfolio template: {template_name} with ID: {template_id}")
    return template_id


def create_advanced_templates():
    """Create advanced page templates for the system."""
    with app.app_context():
        template_manager = PageTemplateManager()
        
        # Check existing templates to avoid duplicates
        existing_templates = template_manager.list_templates()
        existing_names = [t.name for t in existing_templates]
        
        template_ids = []
        
        if "Blog Page" not in existing_names:
            template_ids.append(create_blog_template(template_manager))
            logger.info("Blog Page template created")
        else:
            logger.info("Blog Page template already exists, skipping")
            
        if "FAQ Page" not in existing_names:
            template_ids.append(create_faq_template(template_manager))
            logger.info("FAQ Page template created")
        else:
            logger.info("FAQ Page template already exists, skipping")
            
        if "Services Page" not in existing_names:
            template_ids.append(create_services_template(template_manager))
            logger.info("Services Page template created")
        else:
            logger.info("Services Page template already exists, skipping")
            
        if "Portfolio Page" not in existing_names:
            template_ids.append(create_portfolio_template(template_manager))
            logger.info("Portfolio Page template created")
        else:
            logger.info("Portfolio Page template already exists, skipping")
        
        total_created = len(template_ids)
        logger.info(f"Created {total_created} new page templates")
        
        return template_ids


if __name__ == "__main__":
    logger.info("Creating advanced page templates...")
    template_ids = create_advanced_templates()
    logger.info(f"Created {len(template_ids)} templates")
    sys.exit(0)