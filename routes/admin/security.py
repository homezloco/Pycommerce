"""
Admin security routes for the admin dashboard.

This module handles security-related functionality including security settings,
roles, permissions, and audit logs.
"""
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Request, Query, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

# Import auth middleware
try:
    from routes.admin.auth import admin_required_middleware
except ImportError:
    logging.error("Failed to import admin_required_middleware")
    admin_required_middleware = None

# Template setup will be passed from main app
templates = None

# Initialize logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])

# Mock security settings data (in a real app, this would come from the database)
SECURITY_SETTINGS = {
    "password_policy": "enhanced",
    "password_expiry": "90",
    "mfa_enabled": True,
    "account_lockout": True,
    "lockout_threshold": 5,
    "session_timeout": 30,
    "admin_access": "ip_restricted",
    "allowed_ips": "127.0.0.1, 192.168.1.0/24",
    "api_access": "key_only",
    "api_rate_limiting": True,
    "rate_limit": 60,
    "csrf_protection": True,
    "xss_protection": True,
    "sql_injection_protection": True,
    "https_only": True,
    "security_headers": True
}

# Mock security events data (in a real app, this would come from the database)
SECURITY_EVENTS = [
    {
        "timestamp": "2025-04-21 20:13:45",
        "type": "Login",
        "user": "admin@example.com",
        "ip": "192.168.1.100",
        "description": "User logged in successfully",
        "status": "success"
    },
    {
        "timestamp": "2025-04-21 19:45:22",
        "type": "Login Attempt",
        "user": "user@example.com",
        "ip": "203.0.113.42",
        "description": "Failed login attempt - wrong password",
        "status": "warning"
    },
    {
        "timestamp": "2025-04-21 18:32:11",
        "type": "Settings Change",
        "user": "admin@example.com",
        "ip": "192.168.1.100",
        "description": "Security settings updated",
        "status": "info"
    },
    {
        "timestamp": "2025-04-21 15:19:30",
        "type": "API Access",
        "user": "api_user@example.com",
        "ip": "198.51.100.75",
        "description": "API rate limit exceeded",
        "status": "danger"
    },
    {
        "timestamp": "2025-04-21 14:05:19",
        "type": "Permission Change",
        "user": "admin@example.com",
        "ip": "192.168.1.100",
        "description": "User role updated to admin",
        "status": "success"
    }
]

# Mock roles data (in a real app, this would come from the database)
ROLES = [
    {
        "id": 1,
        "name": "Admin",
        "description": "Full access to all administrative functions",
        "users_count": 3,
        "permissions": ["admin.dashboard.view", "admin.settings.manage", "admin.users.manage"],
        "created_at": "2025-01-01"
    },
    {
        "id": 2,
        "name": "Staff",
        "description": "Limited access to admin functions",
        "users_count": 5,
        "permissions": ["admin.dashboard.view", "admin.logs.view"],
        "created_at": "2025-01-01"
    },
    {
        "id": 3,
        "name": "Content Editor",
        "description": "Access to content management",
        "users_count": 7,
        "permissions": ["content.pages.view", "content.pages.create", "content.pages.edit"],
        "created_at": "2025-02-15"
    },
    {
        "id": 4,
        "name": "Store Manager",
        "description": "Management of store operations",
        "users_count": 4,
        "permissions": ["admin.dashboard.view", "products.view", "products.create", "products.edit"],
        "created_at": "2025-03-10"
    },
    {
        "id": 5,
        "name": "Inventory Manager",
        "description": "Management of product inventory",
        "users_count": 2,
        "permissions": ["products.view", "products.inventory.manage"],
        "created_at": "2025-03-15"
    }
]

def setup_routes(template_instance):
    """Set up security routes with the given template instance."""
    global templates
    templates = template_instance
    
    @router.get("/security", response_class=HTMLResponse)
    async def security_settings(
        request: Request,
        current_user: dict = Depends(admin_required_middleware) if admin_required_middleware else None
    ):
        """Security settings page."""
        return templates.TemplateResponse(
            "admin/security/index.html",
            {
                "request": request,
                "active_page": "security",
                "security_settings": SECURITY_SETTINGS,
                "security_events": SECURITY_EVENTS,
                "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )
    
    @router.post("/security/save", response_class=JSONResponse)
    async def save_security_settings(
        request: Request,
        current_user: dict = Depends(admin_required_middleware) if admin_required_middleware else None
    ):
        """Save security settings."""
        try:
            form_data = await request.form()
            
            # Update security settings (in a real app, this would update the database)
            for key, value in form_data.items():
                if key in SECURITY_SETTINGS:
                    # Convert checkbox values to boolean
                    if value == "on":
                        SECURITY_SETTINGS[key] = True
                    elif value == "":
                        SECURITY_SETTINGS[key] = False
                    else:
                        SECURITY_SETTINGS[key] = value
            
            # Log the security settings change
            new_event = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "Settings Change",
                "user": current_user["email"] if current_user else "Unknown",
                "ip": request.client.host,
                "description": "Security settings updated",
                "status": "success"
            }
            SECURITY_EVENTS.insert(0, new_event)
            
            return JSONResponse(content={"success": True, "message": "Security settings saved successfully"})
        except Exception as e:
            logger.error(f"Error saving security settings: {str(e)}")
            return JSONResponse(
                content={"success": False, "message": f"Error saving security settings: {str(e)}"},
                status_code=500
            )
    
    @router.get("/roles", response_class=HTMLResponse)
    async def roles_management(
        request: Request,
        current_user: dict = Depends(admin_required_middleware) if admin_required_middleware else None
    ):
        """Role management page."""
        return templates.TemplateResponse(
            "admin/security/roles.html",
            {
                "request": request,
                "active_page": "roles",
                "roles": ROLES
            }
        )
    
    @router.post("/roles/create", response_class=JSONResponse)
    async def create_role(
        request: Request,
        name: str = Form(...),
        description: str = Form(...),
        permissions: List[str] = Form([]),
        current_user: dict = Depends(admin_required_middleware) if admin_required_middleware else None
    ):
        """Create a new role."""
        try:
            # In a real app, this would create a new role in the database
            new_role = {
                "id": len(ROLES) + 1,
                "name": name,
                "description": description,
                "users_count": 0,
                "permissions": permissions,
                "created_at": datetime.now().strftime("%Y-%m-%d")
            }
            
            ROLES.append(new_role)
            
            # Log the role creation
            new_event = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "Role Creation",
                "user": current_user["email"] if current_user else "Unknown",
                "ip": request.client.host,
                "description": f"Role '{name}' created",
                "status": "success"
            }
            SECURITY_EVENTS.insert(0, new_event)
            
            return JSONResponse(content={"success": True, "message": f"Role '{name}' created successfully"})
        except Exception as e:
            logger.error(f"Error creating role: {str(e)}")
            return JSONResponse(
                content={"success": False, "message": f"Error creating role: {str(e)}"},
                status_code=500
            )
    
    @router.get("/permissions", response_class=HTMLResponse)
    async def permissions_management(
        request: Request,
        current_user: dict = Depends(admin_required_middleware) if admin_required_middleware else None
    ):
        """Permissions management page."""
        return templates.TemplateResponse(
            "admin/security/permissions.html",
            {
                "request": request,
                "active_page": "permissions"
            }
        )
    
    @router.post("/permissions/create", response_class=JSONResponse)
    async def create_permission(
        request: Request,
        name: str = Form(...),
        code: str = Form(...),
        category: str = Form(...),
        description: str = Form(...),
        roles: List[str] = Form([]),
        current_user: dict = Depends(admin_required_middleware) if admin_required_middleware else None
    ):
        """Create a new permission."""
        try:
            # In a real app, this would create a new permission in the database
            
            # Log the permission creation
            new_event = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "Permission Creation",
                "user": current_user["email"] if current_user else "Unknown",
                "ip": request.client.host,
                "description": f"Permission '{name}' created",
                "status": "success"
            }
            SECURITY_EVENTS.insert(0, new_event)
            
            return JSONResponse(content={"success": True, "message": f"Permission '{name}' created successfully"})
        except Exception as e:
            logger.error(f"Error creating permission: {str(e)}")
            return JSONResponse(
                content={"success": False, "message": f"Error creating permission: {str(e)}"},
                status_code=500
            )
    
    @router.get("/audit-logs", response_class=HTMLResponse)
    async def audit_logs(
        request: Request,
        current_user: dict = Depends(admin_required_middleware) if admin_required_middleware else None
    ):
        """Audit logs page."""
        return templates.TemplateResponse(
            "admin/security/audit-logs.html",
            {
                "request": request,
                "active_page": "audit-logs",
                "security_events": SECURITY_EVENTS
            }
        )
    
    return router