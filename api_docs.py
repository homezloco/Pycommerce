"""
API Documentation for PyCommerce.

This file serves as a standalone API documentation generator using the OpenAPI specification.
It creates comprehensive documentation for all the PyCommerce API endpoints.
"""

import os
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

# Import the API routers
from routes.api import api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app with enhanced metadata
api_docs_app = FastAPI(
    title="PyCommerce API Documentation",
    description="""
    # PyCommerce API Documentation
    
    ## Overview
    
    This is the official API documentation for the PyCommerce platform, a multi-tenant ecommerce solution built with Python.
    The API provides programmatic access to PyCommerce functionality including tenants, products, orders, and more.
    
    ## Authentication
    
    Most endpoints require authentication using JSON Web Tokens (JWT).
    To obtain a token, use the `/api/auth/login` endpoint with valid credentials.
    
    ## Rate Limiting
    
    The API implements rate limiting to ensure fair usage. Standard limits are 100 requests per minute.
    
    ## Webhooks
    
    PyCommerce supports webhooks for real-time notifications of events like order creation, payment completion, etc.
    Configure webhooks in the admin dashboard.
    
    ## Examples
    
    Code examples in various languages are provided throughout the documentation.
    """,
    version="1.0.0",
    docs_url=None,  # Disable default docs to customize our own
    redoc_url=None,  # Disable default redoc to customize our own
    openapi_url="/api/openapi.json",  # Path to the OpenAPI schema
    contact={
        "name": "PyCommerce Support",
        "url": "https://pycommerce.example.com/support",
        "email": "support@pycommerce.example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    swagger_ui_parameters={
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
        "defaultModelsExpandDepth": 3,
        "defaultModelExpandDepth": 3,
        "displayRequestDuration": True,
    }
)

# Add CORS middleware
api_docs_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for docs
if os.path.exists("static"):
    api_docs_app.mount("/static", StaticFiles(directory="static"), name="static")

# Include the API router
api_docs_app.include_router(api_router)

# Custom route for Swagger UI
@api_docs_app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """
    Custom Swagger UI with PyCommerce branding.
    """
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title="PyCommerce API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui.css",
        swagger_favicon_url="/static/favicon.ico" if os.path.exists("static/favicon.ico") else None,
    )

# Custom route for ReDoc
@api_docs_app.get("/api/redoc", include_in_schema=False)
async def custom_redoc_html():
    """
    Custom ReDoc with PyCommerce branding.
    """
    return get_redoc_html(
        openapi_url="/api/openapi.json",
        title="PyCommerce API Documentation - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
        redoc_favicon_url="/static/favicon.ico" if os.path.exists("static/favicon.ico") else None,
    )

# API documentation home
@api_docs_app.get("/api", include_in_schema=False)
async def api_documentation_home():
    """
    API documentation home page with links to Swagger and ReDoc.
    """
    return {
        "message": "Welcome to PyCommerce API Documentation",
        "version": "1.0.0",
        "documentation_links": {
            "swagger": "/api/docs",
            "redoc": "/api/redoc",
            "openapi_json": "/api/openapi.json"
        },
        "api_base_url": "/api"
    }

if __name__ == "__main__":
    uvicorn.run("api_docs:api_docs_app", host="0.0.0.0", port=8000, reload=True)