"""
API Documentation Integration for PyCommerce.

This module provides functions to integrate OpenAPI documentation into the PyCommerce application.
"""

import os
import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create documentation router
docs_router = APIRouter(prefix="/api", tags=["API Documentation"])

# Documentation routes
@docs_router.get("/docs", response_class=HTMLResponse, include_in_schema=False)
async def custom_swagger_ui_html(request: Request):
    """
    Serve the Swagger UI documentation page.
    
    Args:
        request: The request object
        
    Returns:
        The Swagger UI HTML page
    """
    root_path = request.scope.get("root_path", "").rstrip("/")
    openapi_url = f"{root_path}/api/openapi.json"
    
    return get_swagger_ui_html(
        openapi_url=openapi_url,
        title="PyCommerce API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui.css",
        swagger_favicon_url=f"{root_path}/static/favicon.ico" if os.path.exists("static/favicon.ico") else None,
    )

@docs_router.get("/redoc", response_class=HTMLResponse, include_in_schema=False)
async def custom_redoc_html(request: Request):
    """
    Serve the ReDoc documentation page.
    
    Args:
        request: The request object
        
    Returns:
        The ReDoc HTML page
    """
    root_path = request.scope.get("root_path", "").rstrip("/")
    openapi_url = f"{root_path}/api/openapi.json"
    
    return get_redoc_html(
        openapi_url=openapi_url,
        title="PyCommerce API Documentation - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
        redoc_favicon_url=f"{root_path}/static/favicon.ico" if os.path.exists("static/favicon.ico") else None,
    )

@docs_router.get("/documentation", response_class=JSONResponse, include_in_schema=False)
async def api_documentation_links(request: Request):
    """
    Return links to API documentation resources.
    
    Args:
        request: The request object
        
    Returns:
        JSON object with documentation links
    """
    root_path = request.scope.get("root_path", "").rstrip("/")
    
    return {
        "message": "PyCommerce API Documentation",
        "version": "1.0.0",
        "documentation_links": {
            "swagger": f"{root_path}/api/docs",
            "redoc": f"{root_path}/api/redoc",
            "openapi_json": f"{root_path}/api/openapi.json"
        }
    }

def setup_api_documentation(app):
    """
    Setup API documentation routes for the FastAPI application.
    
    Args:
        app: The FastAPI application
    """
    try:
        logger.info("Setting up API documentation routes")
        
        # Configure OpenAPI options
        app.openapi_tags = [
            {
                "name": "System",
                "description": "System-level operations and health checks"
            },
            {
                "name": "Tenants",
                "description": "Operations related to tenant management"
            },
            {
                "name": "Products",
                "description": "Operations related to product management"
            },
            {
                "name": "Orders",
                "description": "Operations related to order management"
            },
            {
                "name": "Categories",
                "description": "Operations related to product categories"
            },
            {
                "name": "Users",
                "description": "Operations related to user management"
            },
            {
                "name": "API Documentation",
                "description": "API documentation endpoints"
            }
        ]
        
        # Update app metadata
        app.title = "PyCommerce API"
        app.description = """
        # PyCommerce API
        
        The official API for the PyCommerce platform, a multi-tenant ecommerce solution.
        
        ## Features
        
        * **Multi-Tenant Architecture**: Complete data isolation between tenants
        * **Product Management**: Comprehensive product catalog with categories
        * **Order Management**: Complete order lifecycle with status tracking
        * **User Management**: Customer accounts and admin controls
        
        ## Authentication
        
        Most endpoints require authentication using JWT tokens.
        """
        app.version = "1.0.0"
        app.contact = {
            "name": "PyCommerce Support",
            "url": "https://pycommerce.example.com/support",
            "email": "support@pycommerce.example.com",
        }
        app.license_info = {
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        }
        
        # Include documentation router
        app.include_router(docs_router)
        
        logger.info("API documentation routes set up successfully")
    except Exception as e:
        logger.error(f"Error setting up API documentation: {str(e)}")
        raise