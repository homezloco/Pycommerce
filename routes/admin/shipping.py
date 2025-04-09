"""
Shipping management routes for the admin dashboard.

This module provides routes for managing shipping methods, zones, rates, and labels.
"""

from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

def setup_routes(templates: Jinja2Templates):
    """
    Set up shipping management routes.
    
    Args:
        templates: Jinja2Templates for rendering
        
    Returns:
        APIRouter: FastAPI router with shipping routes
    """
    router = APIRouter()
    
    @router.get("/admin/shipping", response_class=HTMLResponse)
    async def shipping(request: Request):
        """Shipping management dashboard."""
        status_message = request.query_params.get('status_message')
        status_type = request.query_params.get('status_type', 'info')
        
        return templates.TemplateResponse(
            "admin/shipping.html",
            {
                "request": request,
                "active_page": "shipping",
                "status_message": status_message,
                "status_type": status_type
            }
        )
        
    return router