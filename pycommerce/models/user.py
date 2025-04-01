"""
User-related models and management.

This module defines the User model and UserManager class for
managing users in the PyCommerce SDK.
"""

import logging
import secrets
from typing import Dict, List, Optional, Union, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator, EmailStr
from datetime import datetime, timedelta
import hashlib
import base64
import jwt
from enum import Enum

logger = logging.getLogger("pycommerce.models.user")

# JWT settings
JWT_SECRET = secrets.token_hex(32)  # Generate a random secret key
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class UserRole(str, Enum):
    """
    Possible roles for a user.
    """
    CUSTOMER = "customer"
    ADMIN = "admin"
    STAFF = "staff"


class User(BaseModel):
    """
    Represents a user in the system.
    """
    id: UUID = Field(default_factory=uuid4)
    email: EmailStr
    first_name: str
    last_name: str
    password_hash: Optional[str] = None
    role: UserRole = UserRole.CUSTOMER
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        return f"{self.first_name} {self.last_name}"
        
    def dict(self, *args, **kwargs):
        """Convert the model to a dictionary with string ID."""
        data = super().dict(*args, **kwargs)
        if 'id' in data and isinstance(data['id'], UUID):
            data['id'] = str(data['id'])
        return data


class UserManager:
    """
    Manages user operations.
    """
    
    def __init__(self):
        """Initialize a new UserManager."""
        self._users: Dict[UUID, User] = {}
        self._email_index: Dict[str, UUID] = {}
    
    def _hash_password(self, password: str) -> str:
        """
        Hash a password using SHA-256.
        
        Args:
            password: The password to hash
            
        Returns:
            The hashed password
        """
        # Generate a random salt
        salt = secrets.token_hex(16)
        
        # Hash the password with the salt
        pw_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        
        # Return the salt and hash, separated by a colon
        return f"{salt}:{pw_hash}"
    
    def _verify_password(self, stored_hash: str, password: str) -> bool:
        """
        Verify a password against a stored hash.
        
        Args:
            stored_hash: The stored password hash
            password: The password to verify
            
        Returns:
            True if the password matches, False otherwise
        """
        # Split the stored hash into salt and hash
        salt, pw_hash = stored_hash.split(':', 1)
        
        # Hash the password with the same salt
        new_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        
        # Compare the hashes
        return new_hash == pw_hash
    
    def _create_access_token(self, user_id: UUID, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token for a user.
        
        Args:
            user_id: The ID of the user
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
            "type": "access"
        }
        
        # Encode and return the token
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[User]:
        """
        Verify a JWT token and return the associated user.
        
        Args:
            token: The JWT token to verify
            
        Returns:
            The user associated with the token, or None if the token is invalid
        """
        try:
            # Decode the token
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            
            # Get the user ID from the token
            user_id = payload.get("sub")
            if user_id is None:
                return None
            
            # Get the user
            user = self.get(user_id)
            if not user.is_active:
                return None
            
            return user
        except jwt.PyJWTError:
            return None
    
    def create(self, user_data: dict, password: Optional[str] = None) -> User:
        """
        Create a new user.
        
        Args:
            user_data: Dictionary containing user data
            password: Optional password for the user
            
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
            
            # Hash the password if provided
            if password:
                user_data['password_hash'] = self._hash_password(password)
            
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
    
    def update(self, user_id: Union[UUID, str], user_data: dict, password: Optional[str] = None) -> User:
        """
        Update a user.
        
        Args:
            user_id: The ID of the user to update
            user_data: Dictionary containing updated user data
            password: Optional new password for the user
            
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
            
            # Hash the password if provided
            if password:
                user_data['password_hash'] = self._hash_password(password)
            
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
        
    def authenticate(self, email: str, password: str) -> Optional[tuple]:
        """
        Authenticate a user with email and password.
        
        Args:
            email: The user's email
            password: The user's password
            
        Returns:
            A tuple of (user, access_token) if authentication is successful, None otherwise
        """
        try:
            # Get the user by email
            user = self.get_by_email(email)
            
            # Verify the password
            if not user.password_hash or not self._verify_password(user.password_hash, password):
                return None
            
            # Create and return access token
            access_token = self._create_access_token(user.id)
            
            return (user, access_token)
            
        except Exception as e:
            logger.warning(f"Authentication failed: {str(e)}")
            return None
