"""
Admin interface for tenant management.

This module provides routes for managing tenants in the admin interface.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Request, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from pycommerce.models.tenant import TenantManager

# Set up logging
logger = logging.getLogger(__name__)

# Router and templates initialized in setup_routes
router = None
templates = None

# Initialize managers
tenant_manager = TenantManager()

def setup_routes(templates_instance: Jinja2Templates):
    """
    Set up routes for tenant management.
    
    Args:
        templates_instance: Jinja2 templates instance
        
    Returns:
        APIRouter: FastAPI router
    """
    global templates, router
    templates = templates_instance
    router = APIRouter()
    
    @router.get("/admin/tenants", response_class=HTMLResponse)
    async def tenants_page(
        request: Request
    ):
        """
        Render the tenants management page.
        
        Args:
            request: The request object
        """
        # Get all tenants
        tenants = tenant_manager.get_all()
        
        # Initialize context
        context = {
            "request": request,
            "active_page": "tenants",
            "tenants": tenants,
            "error": None,
            "success": None
        }
        
        try:
            # Add tenant count
            context["tenant_count"] = len(tenants)
        except Exception as e:
            logger.error(f"Error fetching tenants: {e}")
            context["error"] = f"Error fetching tenants: {str(e)}"
        
        return templates.TemplateResponse("admin/tenants.html", context)
            
    return router