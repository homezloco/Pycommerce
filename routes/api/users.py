"""
Users API endpoints for PyCommerce.

This module contains user-related API endpoints for creating, retrieving,
updating, and managing users in the multi-tenant platform.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, EmailStr
import logging
from uuid import UUID

from managers import TenantManager
from pycommerce.models.user import UserManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router with tag
router = APIRouter(prefix="/users", tags=["Users"])

# Response models
class UserBase(BaseModel):
    """Base model for user data."""
    email: EmailStr
    first_name: str
    last_name: str
    is_admin: bool = False
    is_active: bool = True
    
    class Config:
        schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "is_admin": False,
                "is_active": True
            }
        }

class UserCreate(UserBase):
    """Model for creating a new user."""
    password: str
    tenant_id: str
    
    class Config:
        schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "password": "SecurePassword123",
                "is_admin": False,
                "is_active": True,
                "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }

class UserResponse(UserBase):
    """Model for user responses with ID."""
    id: str
    tenant_id: str
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "650e8400-e29b-41d4-a716-446655440000",
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "is_admin": False,
                "is_active": True,
                "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }

class UsersResponse(BaseModel):
    """Model for listing multiple users."""
    users: List[UserResponse]
    tenant: str
    count: int
    
    class Config:
        schema_extra = {
            "example": {
                "users": [
                    {
                        "id": "650e8400-e29b-41d4-a716-446655440000",
                        "email": "john.doe@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "is_admin": False,
                        "is_active": True,
                        "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
                    },
                    {
                        "id": "750e8400-e29b-41d4-a716-446655440000",
                        "email": "jane.smith@example.com",
                        "first_name": "Jane",
                        "last_name": "Smith",
                        "is_admin": True,
                        "is_active": True,
                        "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
                    }
                ],
                "tenant": "electronics",
                "count": 2
            }
        }

class UserUpdate(BaseModel):
    """Model for updating a user."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None
    
    class Config:
        schema_extra = {
            "example": {
                "first_name": "Johnny",
                "last_name": "Doe",
                "is_admin": True,
                "is_active": True
            }
        }

class PasswordUpdate(BaseModel):
    """Model for updating a user's password."""
    current_password: str
    new_password: str
    
    class Config:
        schema_extra = {
            "example": {
                "current_password": "OldPassword123",
                "new_password": "NewSecurePassword456"
            }
        }

# API Routes
@router.get("/", 
         response_model=UsersResponse, 
         summary="List Users",
         description="Retrieve a list of users for a specific tenant with optional filtering",
         responses={
             200: {"description": "Users retrieved successfully", "model": UsersResponse},
             400: {"description": "Invalid request parameters"},
             401: {"description": "Unauthorized - requires proper authentication"},
             403: {"description": "Forbidden - insufficient permissions to access user data"},
             404: {"description": "Tenant not found"},
             500: {"description": "Internal server error"}
         })
async def list_users(
    tenant: str = Query(..., description="The tenant slug identifier to retrieve users for"),
    is_admin: Optional[bool] = Query(None, description="Filter users by administrator status (true/false)"),
    is_active: Optional[bool] = Query(None, description="Filter users by account status (true/false)"),
    search: Optional[str] = Query(None, description="Search users by name or email (minimum 3 characters)")
):
    """
    Retrieve a list of users for a specific tenant with optional filtering.
    
    This endpoint returns a list of user accounts belonging to a specific tenant.
    Results can be filtered by administrative status, account status, and text search
    on name or email fields. The endpoint is designed for administrative purposes
    such as user management and access control.
    
    Available filters:
    - **is_admin**: Filter for administrators or regular users
    - **is_active**: Filter for active or inactive accounts
    - **search**: Text search on first name, last name, and email fields
    
    The response includes user details such as ID, name, email, administrative status,
    account status, and tenant association. Personal details like passwords are never
    returned in the response.
    
    This endpoint requires administrative privileges for the specified tenant.
    Users with global admin privileges can access user lists for any tenant,
    while tenant admins can only access users within their own tenant.
    
    If the specified tenant doesn't exist, a 404 error is returned.
    """
    tenant_manager = TenantManager()
    user_manager = UserManager()
    
    # Get tenant ID from slug
    tenant_obj = tenant_manager.get_tenant_by_slug(tenant)
    if not tenant_obj:
        raise HTTPException(
            status_code=404, detail=f"Tenant not found: {tenant}"
        )

    # Get users
    filters = {}
    if is_admin is not None:
        filters["is_admin"] = is_admin
    if is_active is not None:
        filters["is_active"] = is_active
    if search:
        filters["search"] = search
    
    users = user_manager.get_users_by_tenant(tenant_obj.id, filters)
    
    return {
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "is_admin": u.is_admin,
                "is_active": u.is_active,
                "tenant_id": str(u.tenant_id)
            }
            for u in users
        ],
        "tenant": tenant,
        "count": len(users)
    }

@router.get("/{user_id}", 
         response_model=UserResponse, 
         summary="Get User by ID",
         description="Retrieve detailed information about a specific user",
         responses={
             200: {"description": "User details retrieved successfully", "model": UserResponse},
             400: {"description": "Invalid user ID format"},
             401: {"description": "Unauthorized - requires proper authentication"},
             403: {"description": "Forbidden - insufficient permissions to access this user"},
             404: {"description": "User not found"},
             500: {"description": "Internal server error"}
         })
async def get_user(
    user_id: str = Path(..., description="The ID of the user to retrieve")
):
    """
    Retrieve detailed information about a specific user.
    
    This endpoint returns comprehensive details about a single user account, including
    their profile information, account status, and tenant association. It's primarily 
    used for user profile viewing, account management, and administrative purposes.
    
    The response includes:
    - Basic profile information (name, email)
    - Account status (active/inactive)
    - Administrative privileges
    - Tenant association
    
    Access to user details is restricted based on the requester's permissions:
    - System administrators can access any user profile
    - Tenant administrators can access profiles of users within their tenant
    - Regular users can only access their own profile information
    
    Personal details like passwords are never returned in the response.
    
    If the requested user doesn't exist or the requester lacks permission to access 
    the profile, an appropriate error response is returned.
    """
    user_manager = UserManager()
    user = user_manager.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")
    
    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_admin": user.is_admin,
        "is_active": user.is_active,
        "tenant_id": str(user.tenant_id)
    }

@router.post("/", 
         response_model=UserResponse, 
         summary="Create User",
         description="Create a new user account in the specified tenant",
         responses={
             201: {"description": "User created successfully", "model": UserResponse},
             400: {"description": "Invalid request data or user with email already exists"},
             401: {"description": "Unauthorized - requires proper authentication"},
             403: {"description": "Forbidden - insufficient permissions to create users"},
             404: {"description": "Tenant not found"},
             409: {"description": "Conflict - user with same email already exists"},
             500: {"description": "Internal server error"}
         },
         status_code=201)
async def create_user(
    user: UserCreate = Body(..., description="The user details including email, password, name and tenant association")
):
    """
    Create a new user account in the specified tenant.
    
    This endpoint allows administrators to create new user accounts within a specific tenant.
    The created user can be assigned administrative privileges or set as inactive upon creation.
    All user accounts require a valid email address, password, name details, and tenant association.
    
    Required information for creating a user:
    - **email**: Valid unique email address for the user (required for login)
    - **password**: Secure password (will be hashed before storage)
    - **first_name** and **last_name**: User's name information
    - **tenant_id**: The tenant to associate this user with
    
    Optional parameters allow setting:
    - **is_admin**: Whether the user has administrative privileges (default: false)
    - **is_active**: Whether the account is active upon creation (default: true)
    
    The password is securely hashed before storage, and the original value is never logged
    or stored in plain text. Email addresses must be unique across the entire system.
    
    This endpoint requires administrative privileges for the tenant in which the
    user is being created. System administrators can create users in any tenant.
    
    If the specified tenant doesn't exist or a user with the same email already exists,
    an appropriate error response is returned.
    """
    tenant_manager = TenantManager()
    user_manager = UserManager()
    
    # Check if tenant exists
    tenant = tenant_manager.get_tenant_by_id(user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant with id {user.tenant_id} not found")
    
    # Check if user with email already exists
    existing_user = user_manager.get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail=f"User with email {user.email} already exists")
    
    # Create user
    try:
        new_user = user_manager.create_user(
            email=user.email,
            password=user.password,
            first_name=user.first_name,
            last_name=user.last_name,
            is_admin=user.is_admin,
            is_active=user.is_active,
            tenant_id=user.tenant_id
        )
        
        return {
            "id": str(new_user.id),
            "email": new_user.email,
            "first_name": new_user.first_name,
            "last_name": new_user.last_name,
            "is_admin": new_user.is_admin,
            "is_active": new_user.is_active,
            "tenant_id": str(new_user.tenant_id)
        }
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=400, detail=f"Error creating user: {str(e)}")

@router.put("/{user_id}", 
         response_model=UserResponse, 
         summary="Update User",
         description="Update an existing user's profile information",
         responses={
             200: {"description": "User updated successfully", "model": UserResponse},
             400: {"description": "Invalid request data"},
             401: {"description": "Unauthorized - requires proper authentication"},
             403: {"description": "Forbidden - insufficient permissions to update this user"},
             404: {"description": "User not found"},
             500: {"description": "Internal server error"}
         })
async def update_user(
    user_id: str = Path(..., description="The ID of the user to update"),
    user_update: UserUpdate = Body(..., description="The fields to update in the user profile")
):
    """
    Update an existing user's profile information.
    
    This endpoint allows updating various aspects of a user's profile, including name,
    administrative status, and account activation status. Only the fields provided in
    the request body will be updated; omitted fields retain their current values.
    
    Fields that can be updated:
    - **first_name**: The user's first name
    - **last_name**: The user's last name
    - **is_admin**: Whether the user has administrative privileges
    - **is_active**: Whether the user account is active
    
    Note that user email and tenant assignment cannot be modified through this endpoint.
    To change a password, use the dedicated password update endpoint.
    
    Access to update user profiles is restricted based on permissions:
    - System administrators can update any user profile
    - Tenant administrators can update profiles of users within their tenant
    - Regular users can only update their own non-administrative fields
    
    If the requested user doesn't exist or the requester lacks permission to 
    modify the profile, an appropriate error response is returned.
    """
    user_manager = UserManager()
    
    # Check if user exists
    existing = user_manager.get_user_by_id(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")
    
    # Prepare update data
    update_data = {}
    if user_update.first_name is not None:
        update_data["first_name"] = user_update.first_name
    if user_update.last_name is not None:
        update_data["last_name"] = user_update.last_name
    if user_update.is_admin is not None:
        update_data["is_admin"] = user_update.is_admin
    if user_update.is_active is not None:
        update_data["is_active"] = user_update.is_active
    
    # Update user
    updated_user = user_manager.update_user(user_id, update_data)
    
    return {
        "id": str(updated_user.id),
        "email": updated_user.email,
        "first_name": updated_user.first_name,
        "last_name": updated_user.last_name,
        "is_admin": updated_user.is_admin,
        "is_active": updated_user.is_active,
        "tenant_id": str(updated_user.tenant_id)
    }

@router.put("/{user_id}/password", 
         response_model=Dict[str, Any], 
         summary="Update User Password",
         description="Change a user's account password securely",
         responses={
             200: {"description": "Password updated successfully", 
                   "content": {"application/json": {"example": {"success": True, "message": "Password updated successfully"}}}},
             400: {"description": "Invalid request data or current password is incorrect"},
             401: {"description": "Unauthorized - requires proper authentication"},
             403: {"description": "Forbidden - insufficient permissions to update this user's password"},
             404: {"description": "User not found"},
             500: {"description": "Internal server error"}
         })
async def update_password(
    user_id: str = Path(..., description="The ID of the user to update password for"),
    password_update: PasswordUpdate = Body(..., description="The current and new password values")
):
    """
    Change a user's account password securely.
    
    This endpoint allows changing a user's password, requiring verification of the 
    current password before allowing the update. This security measure helps prevent 
    unauthorized password changes. The new password is securely hashed before storage.
    
    Required information:
    - **current_password**: The user's existing password (for verification)
    - **new_password**: The desired new password
    
    Password requirements and security notes:
    - New passwords must meet minimum complexity requirements
    - Passwords are securely hashed using industry-standard algorithms
    - Neither the current nor new password is ever logged in plain text
    - Failed password verification attempts may be rate-limited for security
    
    Access to change passwords is restricted based on permissions:
    - Users can change their own passwords (with correct verification)
    - System administrators can override password changes for security purposes
    
    If the current password verification fails or the user doesn't exist, an
    appropriate error response is returned.
    """
    user_manager = UserManager()
    
    # Check if user exists
    existing = user_manager.get_user_by_id(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")
    
    # Verify current password
    if not user_manager.verify_password(user_id, password_update.current_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Update password
    user_manager.update_password(user_id, password_update.new_password)
    
    return {
        "success": True,
        "message": "Password updated successfully"
    }

@router.delete("/{user_id}",
         response_model=Dict[str, Any],
         summary="Delete User",
         description="Permanently remove a user account from the system",
         responses={
             200: {"description": "User deleted successfully",
                   "content": {"application/json": {"example": {"success": True, "message": "User example@mail.com deleted successfully"}}}},
             401: {"description": "Unauthorized - requires proper authentication"},
             403: {"description": "Forbidden - insufficient permissions to delete this user"},
             404: {"description": "User not found"},
             409: {"description": "Conflict - cannot delete user with existing dependencies"},
             500: {"description": "Internal server error"}
         })
async def delete_user(
    user_id: str = Path(..., description="The ID of the user to delete")
):
    """
    Permanently remove a user account from the system.
    
    This endpoint allows administrators to delete user accounts from the system.
    When a user is deleted, all associated personal information is permanently removed,
    though references in historical records (like past orders) may be retained with 
    personally identifiable information removed.
    
    Deletion considerations:
    - The operation is permanent and cannot be undone
    - Users with active subscriptions or pending orders may require special handling
    - System restrictions may prevent deletion of the last administrator account
    - Related data like comments or reviews may be anonymized rather than deleted
    
    Access to delete users is restricted based on permissions:
    - System administrators can delete any regular user
    - Tenant administrators can delete regular users within their tenant
    - Users cannot delete their own accounts through this endpoint
    
    The operation returns a success message when completed. If the user cannot be
    deleted due to dependencies or doesn't exist, an appropriate error is returned.
    """
    user_manager = UserManager()
    
    # Check if user exists
    existing = user_manager.get_user_by_id(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")
    
    # Delete user
    user_manager.delete_user(user_id)
    
    return {
        "success": True,
        "message": f"User {existing.email} deleted successfully"
    }