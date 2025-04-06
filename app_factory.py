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

logger = logging.getLogger(__name__)

# Define template directory
templates_dir = Path("templates")
templates = Jinja2Templates(directory=str(templates_dir))

def create_app():
    """
    Create and configure a FastAPI application.
    
    Returns:
        FastAPI: A configured FastAPI application
    """
    # Create FastAPI app
    app = FastAPI(
        title="PyCommerce",
        description="A modular Python e-commerce platform",
        version="0.1.0",
    )
    
    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Add session middleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=os.environ.get("SESSION_SECRET", "dev_secret_key"),
        max_age=7 * 24 * 60 * 60  # 1 week
    )
    
    return app, templates