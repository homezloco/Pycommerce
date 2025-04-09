"""
Reports management routes for the admin dashboard.

This module provides routes for generating and viewing sales, products, customers,
and tax reports.
"""

from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

def setup_routes(templates: Jinja2Templates):
    """
    Set up reports management routes.
    
    Args:
        templates: Jinja2Templates for rendering
        
    Returns:
        APIRouter: FastAPI router with reports routes
    """
    router = APIRouter()
    
    @router.get("/admin/reports", response_class=HTMLResponse)
    async def reports(request: Request):
        """Reports dashboard."""
        status_message = request.query_params.get('status_message')
        status_type = request.query_params.get('status_type', 'info')
        
        return templates.TemplateResponse(
            "admin/reports.html",
            {
                "request": request,
                "active_page": "reports",
                "status_message": status_message,
                "status_type": status_type
            }
        )
        
    return router