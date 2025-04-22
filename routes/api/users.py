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
@router.get("/", response_model=UsersResponse, summary="List Users")
async def list_users(
    tenant: str = Query(..., description="Tenant slug"),
    is_admin: Optional[bool] = Query(None, description="Filter by admin status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or email")
):
    """
    Get users for a tenant with optional filtering.
    
    Args:
        tenant: The tenant slug
        is_admin: Filter users by admin status
        is_active: Filter users by active status
        search: Search users by name or email
        
    Returns:
        A list of users matching the filters
        
    Raises:
        404: If the tenant is not found
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

@router.get("/{user_id}", response_model=UserResponse, summary="Get User by ID")
async def get_user(
    user_id: str = Path(..., description="The ID of the user to retrieve")
):
    """
    Get a single user by ID.
    
    Args:
        user_id: The unique identifier of the user
        
    Returns:
        The user details
        
    Raises:
        404: If the user is not found
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

@router.post("/", response_model=UserResponse, summary="Create User")
async def create_user(
    user: UserCreate = Body(..., description="The user to create")
):
    """
    Create a new user.
    
    Args:
        user: The user details
        
    Returns:
        The created user with its ID
        
    Raises:
        404: If the tenant is not found
        400: If a user with the same email already exists
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

@router.put("/{user_id}", response_model=UserResponse, summary="Update User")
async def update_user(
    user_id: str = Path(..., description="The ID of the user to update"),
    user_update: UserUpdate = Body(..., description="The user updates")
):
    """
    Update an existing user.
    
    Args:
        user_id: The unique identifier of the user
        user_update: The fields to update
        
    Returns:
        The updated user
        
    Raises:
        404: If the user is not found
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

@router.put("/{user_id}/password", response_model=Dict[str, Any], summary="Update User Password")
async def update_password(
    user_id: str = Path(..., description="The ID of the user to update password for"),
    password_update: PasswordUpdate = Body(..., description="The password update details")
):
    """
    Update a user's password.
    
    Args:
        user_id: The unique identifier of the user
        password_update: The current and new password
        
    Returns:
        A confirmation message
        
    Raises:
        404: If the user is not found
        400: If the current password is incorrect
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

@router.delete("/{user_id}", response_model=Dict[str, Any], summary="Delete User")
async def delete_user(
    user_id: str = Path(..., description="The ID of the user to delete")
):
    """
    Delete a user.
    
    Args:
        user_id: The unique identifier of the user
        
    Returns:
        A confirmation message
        
    Raises:
        404: If the user is not found
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