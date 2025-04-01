"""
User API routes for PyCommerce SDK.

This module defines the FastAPI routes for user operations.
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends

from pycommerce.models.user import User, UserManager

router = APIRouter()
logger = logging.getLogger("pycommerce.api.users")

# Storage for tenant-specific user managers
_user_managers = {}

def set_user_manager(manager: UserManager):
    """Set the UserManager instance to use in routes for the default tenant."""
    global _user_managers
    _user_managers["default"] = manager

def set_user_manager_func(get_manager_func):
    """
    Set a function that will be called to get the UserManager for a tenant.
    
    Args:
        get_manager_func: A function that takes a tenant_id and returns a UserManager
    """
    global _get_manager_func
    _get_manager_func = get_manager_func

def get_user_manager(tenant_id: str = None) -> UserManager:
    """
    Get the UserManager instance for a tenant.
    
    Args:
        tenant_id: The tenant ID (optional, uses default if not provided)
    
    Returns:
        The UserManager instance
        
    Raises:
        HTTPException: If the UserManager is not initialized for the tenant
    """
    # Use default tenant if not specified
    if tenant_id is None:
        tenant_id = "default"
        
    # Check if we have a manager for this tenant
    if tenant_id in _user_managers:
        return _user_managers[tenant_id]
    
    # Try to get manager using the function if available
    if "_get_manager_func" in globals() and globals()["_get_manager_func"] is not None:
        try:
            manager = globals()["_get_manager_func"](tenant_id)
            _user_managers[tenant_id] = manager
            return manager
        except Exception as e:
            logger.error(f"Error getting user manager for tenant {tenant_id}: {str(e)}")
    
    # Fallback to default manager
    if "default" in _user_managers:
        return _user_managers["default"]
        
    logger.error(f"UserManager not initialized for tenant {tenant_id}")
    raise HTTPException(
        status_code=500,
        detail="User service not available"
    )


@router.get("", response_model=List[User])
async def list_users(
    user_manager: UserManager = Depends(get_user_manager)
):
    """
    List all users.
    
    Returns:
        List of all users
    """
    try:
        users = user_manager.list()
        return users
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    user_manager: UserManager = Depends(get_user_manager)
):
    """
    Get a user by ID.
    
    Args:
        user_id: The ID of the user to get
        
    Returns:
        The user
        
    Raises:
        HTTPException: If the user is not found
    """
    try:
        return user_manager.get(user_id)
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"User not found: {user_id}"
        )


@router.get("/email/{email}", response_model=User)
async def get_user_by_email(
    email: str,
    user_manager: UserManager = Depends(get_user_manager)
):
    """
    Get a user by email.
    
    Args:
        email: The email of the user to get
        
    Returns:
        The user
        
    Raises:
        HTTPException: If the user is not found
    """
    try:
        return user_manager.get_by_email(email)
    except Exception as e:
        logger.error(f"Error getting user by email {email}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"User not found with email: {email}"
        )


@router.post("", response_model=User)
async def create_user(
    user_data: dict,
    user_manager: UserManager = Depends(get_user_manager)
):
    """
    Create a new user.
    
    Args:
        user_data: Dictionary containing user data
        
    Returns:
        The created user
        
    Raises:
        HTTPException: If user creation fails
    """
    try:
        user = user_manager.create(user_data)
        logger.info(f"Created user: {user.id}")
        return user
    except ValueError as e:
        logger.error(f"Validation error creating user: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid user data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"An error occurred: {str(e)}"
        )


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_data: dict,
    user_manager: UserManager = Depends(get_user_manager)
):
    """
    Update a user.
    
    Args:
        user_id: The ID of the user to update
        user_data: Dictionary containing updated user data
        
    Returns:
        The updated user
        
    Raises:
        HTTPException: If the user is not found or update fails
    """
    try:
        user = user_manager.update(user_id, user_data)
        logger.info(f"Updated user: {user.id}")
        return user
    except ValueError as e:
        logger.error(f"Validation error updating user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid user data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"User not found: {user_id}"
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    user_manager: UserManager = Depends(get_user_manager)
):
    """
    Delete a user.
    
    Args:
        user_id: The ID of the user to delete
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If the user is not found
    """
    try:
        user_manager.delete(user_id)
        logger.info(f"Deleted user: {user_id}")
        return {"message": "User deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"User not found: {user_id}"
        )
