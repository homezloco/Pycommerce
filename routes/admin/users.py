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
                "name": "Admin User",
                "first_name": "Admin",
                "last_name": "User",
                "email": "admin@example.com",
                "role": "administrator",
                "active": True,
                "created_at": "2023-01-01",
                "last_login": "2023-06-15 09:45:22"
            },
            {
                "id": "2",
                "name": "Store Manager",
                "first_name": "Store",
                "last_name": "Manager",
                "email": "manager@example.com",
                "role": "manager",
                "active": True,
                "created_at": "2023-02-15",
                "last_login": "2023-06-14 15:30:10"
            },
            {
                "id": "3",
                "name": "Sales Staff",
                "first_name": "Sales",
                "last_name": "Staff",
                "email": "staff@example.com",
                "role": "staff",
                "active": False,
                "created_at": "2023-03-20",
                "last_login": None
            }
        ]

    @staticmethod
    def get_user(user_id):
        """Return a user by ID (in a real app, this would query the database)."""
        # This is a placeholder - in a real app we'd query the database
        users = {
            "1": {
                "id": "1",
                "name": "Admin User",
                "first_name": "Admin",
                "last_name": "User",
                "email": "admin@example.com",
                "role": "administrator",
                "active": True,
                "created_at": "2023-01-01",
                "last_login": "2023-06-15 09:45:22"
            },
            "2": {
                "id": "2",
                "name": "Store Manager",
                "first_name": "Store",
                "last_name": "Manager",
                "email": "manager@example.com",
                "role": "manager",
                "active": True,
                "created_at": "2023-02-15",
                "last_login": "2023-06-14 15:30:10"
            },
            "3": {
                "id": "3",
                "name": "Sales Staff",
                "first_name": "Sales",
                "last_name": "Staff",
                "email": "staff@example.com",
                "role": "staff",
                "active": False,
                "created_at": "2023-03-20",
                "last_login": None
            }
        }
        return users.get(user_id)
    
    @staticmethod
    def get_users_by_tenant(tenant_id):
        # Placeholder - Replace with actual database query
        return [{"id": f"{tenant_id}_1", "name": f"User in Tenant {tenant_id}"}, {"id": f"{tenant_id}_2", "name": f"Another User in Tenant {tenant_id}"}]

    @staticmethod
    def get_all_users():
        #Placeholder - Replace with actual database query
        return [{"id": "all_1", "name": "User 1 (All Tenants)"}, {"id": "all_2", "name": "User 2 (All Tenants)"}]


# Initialize manager
user_manager = UserManager()

@router.get("/users", response_class=HTMLResponse)
async def list_users(
    request: Request,
    tenant: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for user management."""
    # Get tenant from query parameters or session
    selected_tenant_slug = tenant or request.session.get("selected_tenant")

    # If no tenant is selected, redirect to dashboard with message
    if not selected_tenant_slug:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Please+select+a+store+first&status_type=warning", 
            status_code=303
        )

    # Store the selected tenant in session for future requests
    request.session["selected_tenant"] = selected_tenant_slug

    # Get tenant object
    tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
    if not tenant_obj and selected_tenant_slug.lower() != "all":
        return RedirectResponse(
            url="/admin/dashboard?status_message=Store+not+found&status_type=error", 
            status_code=303
        )

    # Handle "all" tenant slug case
    if selected_tenant_slug.lower() == "all":
        logger.info("Using 'All Stores' selection in users page")
        from routes.admin.tenant_utils import create_virtual_all_tenant
        tenant_obj = type('AllStoresTenant', (), create_virtual_all_tenant())
        # Get users for all tenants
        try:
            # First try to get all tenants
            all_tenants = tenant_manager.get_all() or []
            
            # Then fetch users for each tenant and combine them
            all_users = []
            for tenant in all_tenants:
                try:
                    tenant_users = user_manager.get_users_by_tenant(tenant_id=str(tenant.id))
                    all_users.extend(tenant_users)
                    logger.info(f"Found {len(tenant_users)} users for tenant {tenant.name}")
                except Exception as e:
                    logger.error(f"Error fetching users for tenant {tenant.name}: {str(e)}")
            
            users = all_users
            logger.info(f"Found {len(users)} users across all stores")
            
            # If no users found, fall back to get_all_users method
            if not users:
                logger.info("No users found using tenant queries, trying get_all_users() method")
                users = user_manager.get_all_users()
                logger.info(f"Found {len(users)} users using get_all_users() method")
        except Exception as e:
            logger.error(f"Error fetching all users: {str(e)}")
            # Fallback to the general get_users method
            users = user_manager.get_users()
            logger.info(f"Falling back to get_users() method, found {len(users)} users")
    else:
        # Get users for specific tenant
        users = user_manager.get_users()

    # Get all tenants for the sidebar
    tenants = tenant_manager.get_all()

    return templates.TemplateResponse(
        "admin/users.html",
        {
            "request": request,
            "users": users,
            "tenant": tenant_obj,
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
    tenant = next((t for t in tenants if t.slug == selected_tenant_slug), tenants[0] if tenants else None)

    # Define available roles
    roles = ["administrator", "manager", "staff"]

    return templates.TemplateResponse(
        "admin/user_create.html",
        {
            "request": request,
            "tenant": tenant,
            "selected_tenant": selected_tenant_slug,
            "tenants": tenants,
            "active_page": "users",
            "status_message": None,
            "status_type": "info"
        }
    )

@router.post("/users/create", response_class=RedirectResponse)
async def create_user(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    role: str = Form("staff"),
    active: Optional[str] = Form(None),
    send_welcome_email: Optional[str] = Form(None)
):
    """Create a new user."""
    try:
        # Get all tenants for the sidebar
        tenants = tenant_manager.get_all()

        # Get selected tenant from session
        selected_tenant_slug = request.session.get("selected_tenant")
        tenant = next((t for t in tenants if t.slug == selected_tenant_slug), tenants[0] if tenants else None)

        # Validate password
        if password != confirm_password:
            return templates.TemplateResponse(
                "admin/user_create.html",
                {
                    "request": request,
                    "tenant": tenant,
                    "selected_tenant": selected_tenant_slug,
                    "tenants": tenants,
                    "active_page": "users",
                    "status_message": "Passwords do not match",
                    "status_type": "danger"
                },
                status_code=400
            )

        # Create user
        # This is a placeholder - in a real app we'd create the user in the database
        name = f"{first_name} {last_name}"
        is_active = active is not None
        send_email = send_welcome_email is not None

        logger.info(f"Would create user: {name} ({email}) with role {role}, active: {is_active}, send email: {send_email}")

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
    tenant = next((t for t in tenants if t.slug == selected_tenant_slug), tenants[0] if tenants else None)

    return templates.TemplateResponse(
        "admin/user_edit.html",
        {
            "request": request,
            "user": user,
            "tenant": tenant,
            "selected_tenant": selected_tenant_slug,
            "tenants": tenants,
            "active_page": "users",
            "status_message": None,
            "status_type": "info"
        }
    )

@router.post("/users/update", response_class=RedirectResponse)
async def update_user(
    request: Request,
    user_id: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    password: Optional[str] = Form(None),
    confirm_password: Optional[str] = Form(None),
    role: str = Form("staff"),
    active: Optional[str] = Form(None)
):
    """Update an existing user."""
    try:
        # Get all tenants for the sidebar
        tenants = tenant_manager.get_all()

        # Get selected tenant from session
        selected_tenant_slug = request.session.get("selected_tenant")
        tenant = next((t for t in tenants if t.slug == selected_tenant_slug), tenants[0] if tenants else None)

        # Get user
        user = user_manager.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found"
            )

        # Validate password if provided
        if password and password != confirm_password:
            user_with_form_data = {
                "id": user_id,
                "first_name": first_name,
                "last_name": last_name,
                "name": f"{first_name} {last_name}",
                "email": email,
                "role": role,
                "active": active is not None,
                "created_at": user["created_at"],
                "last_login": user["last_login"]
            }

            return templates.TemplateResponse(
                "admin/user_edit.html",
                {
                    "request": request,
                    "user": user_with_form_data,
                    "tenant": tenant,
                    "selected_tenant": selected_tenant_slug,
                    "tenants": tenants,
                    "active_page": "users",
                    "status_message": "Passwords do not match",
                    "status_type": "danger"
                },
                status_code=400
            )

        # Update user
        # This is a placeholder - in a real app we'd update the user in the database
        name = f"{first_name} {last_name}"
        is_active = active is not None

        logger.info(f"Would update user: {name} ({email}) with role {role}, active: {is_active}")

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

@router.post("/users/delete", response_class=RedirectResponse)
async def delete_user(
    request: Request,
    user_id: str = Form(...)
):
    """Delete a user."""
    try:
        # Get user
        user = user_manager.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found"
            )

        # Delete user
        # This is a placeholder - in a real app we'd delete the user from the database

        logger.info(f"Would delete user: {user['name']} ({user['email']})")

        return RedirectResponse(
            url="/admin/users?status_message=User+deleted+successfully&status_type=success",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        return RedirectResponse(
            url="/admin/users?status_message=Error+deleting+user:+{str(e)}&status_type=danger",
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