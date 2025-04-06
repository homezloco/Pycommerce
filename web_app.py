"""
Main web application for PyCommerce.

This file creates the main FastAPI application using the app factory.
It represents the entry point for uvicorn when running directly.
"""
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the application using the factory
from app_factory import create_app

app, templates = create_app()

# Add health endpoint required by the ASGI-WSGI adapter
@app.get("/api/health")
async def health_check():
    """Health check endpoint that the proxy uses to determine if the app is running."""
    return JSONResponse({
        "status": "ok",
        "version": "0.1.0",
        "message": "PyCommerce API is running"
    })

# Add root endpoint
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Home page for PyCommerce."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "PyCommerce - A Python Ecommerce Platform",
            "cart_item_count": request.session.get("cart_item_count", 0)
        }
    )

# Fallback for admin routes
@app.get("/admin")
@app.get("/admin/")
async def admin_redirect():
    """Redirect /admin to /admin/dashboard."""
    return RedirectResponse(url="/admin/dashboard")