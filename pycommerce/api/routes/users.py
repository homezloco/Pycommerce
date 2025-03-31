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

# Dependency to get the UserManager instance
_user_manager = None

def set_user_manager(manager: UserManager):
    """Set the UserManager instance to use in routes."""
    global _user_manager
    _user_manager = manager

def get_user_manager() -> UserManager:
    """
    Get the UserManager instance.
    
    Returns:
        The UserManager instance
        
    Raises:
        HTTPException: If the UserManager is not initialized
    """
    if _user_manager is None:
        logger.error("UserManager not initialized")
        raise HTTPException(
            status_code=500,
            detail="User service not available"
        )
    return _user_manager


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
