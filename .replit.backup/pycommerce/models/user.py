"""
User-related models and management.

This module defines the User model and UserManager class for
managing users in the PyCommerce SDK.
"""

import logging
from typing import Dict, List, Optional, Union, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator, EmailStr
from datetime import datetime

logger = logging.getLogger("pycommerce.models.user")


class User(BaseModel):
    """
    Represents a user in the system.
    """
    id: UUID = Field(default_factory=uuid4)
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class UserManager:
    """
    Manages user operations.
    """
    
    def __init__(self):
        """Initialize a new UserManager."""
        self._users: Dict[UUID, User] = {}
        self._email_index: Dict[str, UUID] = {}
    
    def create(self, user_data: dict) -> User:
        """
        Create a new user.
        
        Args:
            user_data: Dictionary containing user data
            
        Returns:
            The created user
            
        Raises:
            ValueError: If user creation fails
        """
        from pycommerce.core.exceptions import PyCommerceError
        
        try:
            # Check if email already exists
            if 'email' in user_data and user_data['email'].lower() in self._email_index:
                raise PyCommerceError(f"User with email '{user_data['email']}' already exists")
            
            # Create and store the user
            user = User(**user_data)
            self._users[user.id] = user
            self._email_index[user.email.lower()] = user.id
            
            logger.debug(f"Created user: {user.email} (ID: {user.id})")
            return user
            
        except ValueError as e:
            raise PyCommerceError(f"Invalid user data: {str(e)}")
    
    def get(self, user_id: Union[UUID, str]) -> User:
        """
        Get a user by ID.
        
        Args:
            user_id: The ID of the user to get
            
        Returns:
            The user
            
        Raises:
            PyCommerceError: If the user is not found
        """
        from pycommerce.core.exceptions import PyCommerceError
        
        # Convert string ID to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                raise PyCommerceError(f"Invalid user ID: {user_id}")
        
        if user_id not in self._users:
            raise PyCommerceError(f"User not found: {user_id}")
        
        return self._users[user_id]
    
    def get_by_email(self, email: str) -> User:
        """
        Get a user by email.
        
        Args:
            email: The email of the user to get
            
        Returns:
            The user
            
        Raises:
            PyCommerceError: If the user is not found
        """
        from pycommerce.core.exceptions import PyCommerceError
        
        email = email.lower()
        if email not in self._email_index:
            raise PyCommerceError(f"User not found with email: {email}")
        
        return self.get(self._email_index[email])
    
    def update(self, user_id: Union[UUID, str], user_data: dict) -> User:
        """
        Update a user.
        
        Args:
            user_id: The ID of the user to update
            user_data: Dictionary containing updated user data
            
        Returns:
            The updated user
            
        Raises:
            PyCommerceError: If the user is not found or update fails
        """
        from pycommerce.core.exceptions import PyCommerceError
        
        # Get the user first
        user = self.get(user_id)
        
        try:
            # Handle email changes
            if 'email' in user_data and user_data['email'].lower() != user.email.lower():
                if user_data['email'].lower() in self._email_index:
                    raise PyCommerceError(f"User with email '{user_data['email']}' already exists")
                # Update email index
                del self._email_index[user.email.lower()]
                self._email_index[user_data['email'].lower()] = user.id
            
            # Update the user
            for key, value in user_data.items():
                setattr(user, key, value)
            
            # Update timestamp
            user.updated_at = datetime.now()
            
            logger.debug(f"Updated user: {user.email} (ID: {user.id})")
            return user
            
        except ValueError as e:
            raise PyCommerceError(f"Invalid user data: {str(e)}")
    
    def delete(self, user_id: Union[UUID, str]) -> None:
        """
        Delete a user.
        
        Args:
            user_id: The ID of the user to delete
            
        Raises:
            PyCommerceError: If the user is not found
        """
        # Get the user first (this will validate the ID)
        user = self.get(user_id)
        
        # Remove from indexes
        del self._email_index[user.email.lower()]
        del self._users[user.id]
        
        logger.debug(f"Deleted user: {user.email} (ID: {user.id})")
    
    def list(self) -> List[User]:
        """
        List all users.
        
        Returns:
            List of all users
        """
        return list(self._users.values())
