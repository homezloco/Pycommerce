"""
Admin authentication routes for the admin dashboard.

This module handles admin login, logout, and authentication middleware.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Request, Response, HTTPException, Depends, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND, HTTP_401_UNAUTHORIZED
import jwt
from datetime import datetime, timedelta
import secrets
import hashlib

# Template setup will be passed from main app
templates = None

# Initialize logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])

# Globals for middleware functions (to be set in setup_routes)
get_current_user_middleware = None
admin_required_middleware = None
staff_or_admin_required_middleware = None

# Import models and managers
try:
    from pycommerce.models.user import UserManager, UserRole
    # Initialize managers
    user_manager = UserManager()
except ImportError as e:
    logger.error(f"Error importing user modules: {str(e)}")

# JWT settings (should be moved to environment variables in production)
JWT_SECRET = secrets.token_hex(32)  # Generate a random secret key
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Longer session for admin users


def create_access_token(user_id: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token for a user.
    
    Args:
        user_id: The ID of the user
        role: The user's role
        expires_delta: Optional expiration time delta
        
    Returns:
        The JWT access token
    """
    # Set the expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Create the JWT payload
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.utcnow(),
        "role": role,
        "type": "access"
    }
    
    # Encode and return the token
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str):
    """
    Decode a JWT token.
    
    Args:
        token: The JWT token to decode
        
    Returns:
        The decoded payload, or None if the token is invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


async def get_current_user(request: Request):
    """
    Get the current authenticated user from the request.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        The current user, or None if not authenticated
    """
    # Check if authentication info is already in the session
    if "user" in request.session:
        return request.session["user"]
    
    # Check for access token in cookies
    access_token = request.cookies.get("admin_access_token")
    if not access_token:
        return None
    
    # Decode the token
    payload = decode_token(access_token)
    if not payload:
        return None
    
    # Get the user
    try:
        user_id = payload.get("sub")
        user = user_manager.get(user_id)
        
        # Verify the user is active and has admin privileges
        if not user.is_active or user.role not in [UserRole.ADMIN, UserRole.STAFF]:
            return None
        
        # Store user in session for efficiency
        request.session["user"] = {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "full_name": user.full_name
        }
        
        return request.session["user"]
    except Exception as e:
        logger.warning(f"Error retrieving user from token: {str(e)}")
        return None


async def admin_required(request: Request):
    """
    Middleware to ensure the current user is an admin.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        The current user if they are an admin, otherwise redirects to login
        
    Raises:
        HTTPException: If user is not authenticated as admin
    """
    user = await get_current_user(request)
    if not user or user.get("role") != UserRole.ADMIN:
        return RedirectResponse(url="/admin/login", status_code=HTTP_302_FOUND)
    return user


async def staff_or_admin_required(request: Request):
    """
    Middleware to ensure the current user is staff or admin.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        The current user if they are staff or admin, otherwise redirects to login
        
    Raises:
        HTTPException: If user is not authenticated as staff or admin
    """
    user = await get_current_user(request)
    if not user or user.get("role") not in [UserRole.ADMIN, UserRole.STAFF]:
        return RedirectResponse(url="/admin/login", status_code=HTTP_302_FOUND)
    return user


def setup_routes(template_instance: Jinja2Templates):
    """Set up authentication routes with the given template instance."""
    global templates
    templates = template_instance
    
    @router.get("/login", response_class=HTMLResponse)
    async def login_page(request: Request, error: Optional[str] = None):
        """Admin login page."""
        # Check if user is already authenticated
        user = await get_current_user(request)
        if user:
            return RedirectResponse(url="/admin/dashboard", status_code=HTTP_302_FOUND)
        
        return templates.TemplateResponse(
            "admin/login.html",
            {"request": request, "error": error}
        )
    
    @router.post("/login", response_class=HTMLResponse)
    async def login(
        request: Request,
        response: Response,
        email: str = Form(...),
        password: str = Form(...),
        remember: bool = Form(False)
    ):
        """Process admin login."""
        try:
            # Authenticate user
            auth_result = user_manager.authenticate(email, password)
            
            if not auth_result:
                logger.warning(f"Failed login attempt for {email}")
                return templates.TemplateResponse(
                    "admin/login.html",
                    {"request": request, "error": "Invalid email or password"}
                )
            
            user, access_token = auth_result
            
            # Check if user has admin or staff role
            if user.role not in [UserRole.ADMIN, UserRole.STAFF]:
                logger.warning(f"Non-admin user attempted to log in to admin: {email}")
                return templates.TemplateResponse(
                    "admin/login.html",
                    {"request": request, "error": "You do not have permission to access the admin area"}
                )
            
            # Generate a custom token with role information
            token = create_access_token(
                user_id=str(user.id),
                role=user.role,
                expires_delta=timedelta(days=30 if remember else 1)
            )
            
            # Set cookie with the token
            response = RedirectResponse(url="/admin/dashboard", status_code=HTTP_302_FOUND)
            response.set_cookie(
                key="admin_access_token",
                value=token,
                httponly=True,
                max_age=2592000 if remember else 86400,  # 30 days or 1 day
                path="/"
            )
            
            # Store user in session
            request.session["user"] = {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "full_name": user.full_name
            }
            
            logger.info(f"Admin login successful: {email}")
            return response
            
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            return templates.TemplateResponse(
                "admin/login.html",
                {"request": request, "error": "An error occurred during login. Please try again."}
            )
    
    @router.get("/logout")
    async def logout(request: Request, response: Response):
        """Process admin logout."""
        # Clear session
        if "user" in request.session:
            del request.session["user"]
        
        # Clear auth cookie
        response = RedirectResponse(url="/admin/login", status_code=HTTP_302_FOUND)
        response.delete_cookie(key="admin_access_token", path="/")
        
        return response
    
    # Store the middleware functions as module-level variables so they can be imported elsewhere
    global get_current_user_middleware, admin_required_middleware, staff_or_admin_required_middleware
    get_current_user_middleware = get_current_user
    admin_required_middleware = admin_required
    staff_or_admin_required_middleware = staff_or_admin_required
    
    # Return the router object
    return router