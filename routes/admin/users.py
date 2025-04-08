"""
Admin routes for user management.

This module provides routes for managing users in the admin interface.
"""
import logging
from typing import Dict, Optional, List

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from pycommerce.models.tenant import TenantManager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])

# Template setup will be passed from main app
templates = None

# Initialize managers
tenant_manager = TenantManager()

class UserManager:
    """Simple user manager class for admin users."""
    
    @staticmethod
    def get_users():
        """Return a list of admin users (in a real app, this would query the database)."""
        # This is a placeholder - in a real app we'd query the database
        return [
            {
                "id": "1",
                "username": "admin",
                "email": "admin@example.com",
                "role": "admin",
                "is_active": True,
                "created_at": "2023-01-01T00:00:00Z"
            }
        ]
    
    @staticmethod
    def get_user(user_id):
        """Return a user by ID (in a real app, this would query the database)."""
        # This is a placeholder - in a real app we'd query the database
        if user_id == "1":
            return {
                "id": "1",
                "username": "admin",
                "email": "admin@example.com",
                "role": "admin",
                "is_active": True,
                "created_at": "2023-01-01T00:00:00Z"
            }
        return None

# Initialize manager
user_manager = UserManager()

@router.get("/users", response_class=HTMLResponse)
async def list_users(
    request: Request,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for user management."""
    # Get users
    users = user_manager.get_users()
    
    # Get all tenants for the sidebar
    tenants = tenant_manager.get_all()
    
    # Get selected tenant from session
    selected_tenant_slug = request.session.get("selected_tenant")
    
    return templates.TemplateResponse(
        "admin/users.html",
        {
            "request": request,
            "users": users,
            "selected_tenant": selected_tenant_slug,
            "tenants": tenants,
            "active_page": "users",
            "status_message": status_message,
            "status_type": status_type
        }
    )

@router.get("/users/new", response_class=HTMLResponse)
async def new_user_form(
    request: Request
):
    """Display form for creating a new user."""
    # Get all tenants for the sidebar
    tenants = tenant_manager.get_all()
    
    # Get selected tenant from session
    selected_tenant_slug = request.session.get("selected_tenant")
    
    # Define available roles
    roles = ["admin", "manager", "editor"]
    
    return templates.TemplateResponse(
        "admin/users_form.html",
        {
            "request": request,
            "user": None,
            "roles": roles,
            "action": "/admin/users/new",
            "title": "Create New User",
            "selected_tenant": selected_tenant_slug,
            "tenants": tenants,
            "active_page": "users"
        }
    )

@router.post("/users/new", response_class=RedirectResponse)
async def create_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    role: str = Form("editor"),
    is_active: Optional[str] = Form(None)
):
    """Create a new user."""
    try:
        # Validate password
        if password != confirm_password:
            return templates.TemplateResponse(
                "admin/users_form.html",
                {
                    "request": request,
                    "user": {
                        "username": username,
                        "email": email,
                        "role": role,
                        "is_active": is_active is not None
                    },
                    "roles": ["admin", "manager", "editor"],
                    "action": "/admin/users/new",
                    "title": "Create New User",
                    "active_page": "users",
                    "error": "Passwords do not match"
                },
                status_code=400
            )
        
        # Create user
        # This is a placeholder - in a real app we'd create the user in the database
        
        logger.info(f"Would create user: {username} with role {role}")
        
        return RedirectResponse(
            url="/admin/users?status_message=User+created+successfully&status_type=success",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return RedirectResponse(
            url="/admin/users?status_message=Error+creating+user:+{str(e)}&status_type=danger",
            status_code=status.HTTP_303_SEE_OTHER
        )

@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_form(
    request: Request,
    user_id: str
):
    """Display form for editing an existing user."""
    # Get user
    user = user_manager.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User with ID {user_id} not found"
        )
    
    # Get all tenants for the sidebar
    tenants = tenant_manager.get_all()
    
    # Get selected tenant from session
    selected_tenant_slug = request.session.get("selected_tenant")
    
    # Define available roles
    roles = ["admin", "manager", "editor"]
    
    return templates.TemplateResponse(
        "admin/users_form.html",
        {
            "request": request,
            "user": user,
            "roles": roles,
            "action": f"/admin/users/{user_id}/edit",
            "title": f"Edit User: {user['username']}",
            "selected_tenant": selected_tenant_slug,
            "tenants": tenants,
            "active_page": "users"
        }
    )

@router.post("/users/{user_id}/edit", response_class=RedirectResponse)
async def update_user(
    request: Request,
    user_id: str,
    username: str = Form(...),
    email: str = Form(...),
    password: Optional[str] = Form(None),
    confirm_password: Optional[str] = Form(None),
    role: str = Form("editor"),
    is_active: Optional[str] = Form(None)
):
    """Update an existing user."""
    try:
        # Get user
        user = user_manager.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found"
            )
        
        # Validate password if provided
        if password and password != confirm_password:
            return templates.TemplateResponse(
                "admin/users_form.html",
                {
                    "request": request,
                    "user": {
                        "id": user_id,
                        "username": username,
                        "email": email,
                        "role": role,
                        "is_active": is_active is not None
                    },
                    "roles": ["admin", "manager", "editor"],
                    "action": f"/admin/users/{user_id}/edit",
                    "title": f"Edit User: {username}",
                    "active_page": "users",
                    "error": "Passwords do not match"
                },
                status_code=400
            )
        
        # Update user
        # This is a placeholder - in a real app we'd update the user in the database
        
        logger.info(f"Would update user: {username} with role {role}")
        
        return RedirectResponse(
            url="/admin/users?status_message=User+updated+successfully&status_type=success",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        return RedirectResponse(
            url="/admin/users?status_message=Error+updating+user:+{str(e)}&status_type=danger",
            status_code=status.HTTP_303_SEE_OTHER
        )

def setup_routes(app_templates):
    """
    Set up routes with the given templates.
    
    Args:
        app_templates: Jinja2Templates instance from the main app
    """
    global templates
    templates = app_templates
    return router