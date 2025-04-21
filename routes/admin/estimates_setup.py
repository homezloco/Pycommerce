"""
Estimates route setup for the admin dashboard.

This module sets up the routes for managing estimates in the admin dashboard.
"""

import logging
from fastapi import APIRouter
from fastapi.templating import Jinja2Templates

from routes.admin.estimates import estimates_bp

logger = logging.getLogger(__name__)

def setup_routes(templates: Jinja2Templates) -> APIRouter:
    """
    Set up the routes for managing estimates.
    
    Args:
        templates: Jinja2Templates instance
    
    Returns:
        APIRouter: FastAPI router with estimate routes
    """
    router = APIRouter()
    
    # Register the Flask blueprint
    try:
        from flask_adapter import flask_app
        flask_app.register_blueprint(estimates_bp)
        logger.info("Estimate routes registered successfully")
    except ImportError as e:
        logger.warning(f"Could not register Flask blueprint: {str(e)}")
        # Continue even if Flask registration fails
    
    return router