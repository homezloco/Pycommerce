"""
Factory module for creating the FastAPI application instance.

This module creates a configured FastAPI application with all the necessary middleware,
template configuration, and static files setup.
"""
import os
import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

# PyCommerce core imports
from pycommerce.core.db import init_db
from pycommerce.core.migrations import init_migrations
from pycommerce.models.tenant import TenantManager
from pycommerce.models.product import ProductManager
from pycommerce.models.order import OrderManager
from pycommerce.models.user import UserManager
from pycommerce.services.media_service import MediaService
from pycommerce.plugins import StripePaymentPlugin, StandardShippingPlugin

# Import route registration
from routes import register_routes

logger = logging.getLogger(__name__)

# Define template directory
templates_dir = Path("templates")
# Disable template caching for development
templates = Jinja2Templates(directory=str(templates_dir))
templates.env.globals.update({
    "DEBUG": True,
})
templates.env.auto_reload = True
templates.env.cache_size = 0  # Disable caching completely

def create_app():
    """
    Create and configure a FastAPI application.

    Returns:
        FastAPI: A configured FastAPI application
    """
    # Initialize database
    init_db()
    init_migrations()

    # Create FastAPI app
    app = FastAPI(
        title="PyCommerce",
        description="A modular Python e-commerce platform",
        version="0.1.0",
        debug=True,  # Enable debug mode
    )

    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Add session middleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=os.environ.get("SESSION_SECRET", "dev_secret_key"),
        max_age=7 * 24 * 60 * 60  # 1 week
    )

    # Register all modular routes
    register_routes(app, templates)

    return app, templates