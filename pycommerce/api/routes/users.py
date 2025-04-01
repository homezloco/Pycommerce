"""
User API routes for PyCommerce SDK.

This module defines the FastAPI routes for user operations.
"""

import logging
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from pycommerce.models.user import User, UserManager, UserRole

# Define response models for authentication
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    sub: Optional[str] = None

class UserCreate(BaseModel):
    email: str
    first_name: str
    last_name: str
    password: str
    role: UserRole = UserRole.CUSTOMER

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool
    created_at: datetime  # Use specific type
    updated_at: datetime  # Use specific type
    
    class Config:
        from_attributes = True  # Updated from orm_mode
        
    # Helper function to convert from pydantic model  
    @classmethod
    def from_user(cls, user: User):
        # Convert UUID to string and return new model instance
        return cls(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

router = APIRouter()
logger = logging.getLogger("pycommerce.api.users")

# Create a reusable OAuth2 scheme that can be updated with the correct tokenUrl
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")

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
    
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_manager: UserManager = Depends(get_user_manager)
) -> User:
    """
    Get the current authenticated user from the token.
    
    Args:
        token: The JWT access token
        user_manager: The UserManager instance
        
    Returns:
        The authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify token
    user = user_manager.verify_token(token)
    if user is None:
        raise credentials_exception
    
    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's information.
    
    Returns:
        The current user
    """
    return UserResponse.from_user(current_user)

@router.get("", response_model=List[UserResponse])
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
        # Convert each user to UserResponse
        return [UserResponse.from_user(user) for user in users]
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse)
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
        user = user_manager.get(user_id)
        return UserResponse.from_user(user)
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"User not found: {user_id}"
        )


@router.get("/email/{email}", response_model=UserResponse)
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
        user = user_manager.get_by_email(email)
        return UserResponse.from_user(user)
    except Exception as e:
        logger.error(f"Error getting user by email {email}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"User not found with email: {email}"
        )


@router.post("", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    user_manager: UserManager = Depends(get_user_manager)
):
    """
    Create a new user.
    
    Args:
        user_data: User registration data with password
        
    Returns:
        The created user
        
    Raises:
        HTTPException: If user creation fails
    """
    try:
        # Extract password from the model
        password = user_data.password
        
        # Convert to dict and remove password field
        user_dict = user_data.dict()
        del user_dict["password"]
        
        # Create user with hashed password
        user = user_manager.create(user_dict, password)
        logger.info(f"Created user: {user.id}")
        return UserResponse.from_user(user)
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
        
@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_manager: UserManager = Depends(get_user_manager)
):
    """
    Authenticate user and provide access token.
    
    Args:
        form_data: OAuth2 password request form with username and password
        
    Returns:
        Access token for the authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    # OAuth2 form uses username field, but we use email
    email = form_data.username
    password = form_data.password
    
    # Authenticate user
    auth_result = user_manager.authenticate(email, password)
    if not auth_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Unpack auth result
    user, access_token = auth_result
    
    return {"access_token": access_token, "token_type": "bearer"}


class UserUpdate(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    user_manager: UserManager = Depends(get_user_manager)
):
    """
    Update a user.
    
    Args:
        user_id: The ID of the user to update
        user_data: User update data with optional fields
        
    Returns:
        The updated user
        
    Raises:
        HTTPException: If the user is not found or update fails
    """
    try:
        # Extract password if provided
        password = user_data.password
        
        # Convert to dict and remove password field
        user_dict = user_data.dict(exclude_unset=True, exclude_none=True)
        if "password" in user_dict:
            del user_dict["password"]
        
        # Update the user
        user = user_manager.update(user_id, user_dict, password)
        logger.info(f"Updated user: {user.id}")
        return UserResponse.from_user(user)
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
