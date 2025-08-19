"""
Configuration module for PyCommerce.

This module provides access to configuration settings for the PyCommerce platform.
"""

import os
from typing import Dict, Any, Optional
from functools import lru_cache
import secrets

class Settings:
    """Settings class for PyCommerce."""

    def __init__(self):
        """Initialize settings with environment variables and defaults."""
        # Base settings
        self.debug = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")
        self.environment = os.environ.get("ENVIRONMENT", "development")

        # API settings
        self.api_prefix = os.environ.get("API_PREFIX", "/api")

        # Security settings - require secure configurations in production
        self.secret_key = os.environ.get("SECRET_KEY")
        if not self.secret_key:
            if self.environment == "production":
                raise ValueError("SECRET_KEY environment variable is required in production")
            else:
                self.secret_key = secrets.token_urlsafe(32)

        self.algorithm = os.environ.get("ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

        # OpenAI settings
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")

        # Database settings - require explicit configuration in production
        self.database_url = os.environ.get("DATABASE_URL")
        if not self.database_url:
            if self.environment == "production":
                raise ValueError("DATABASE_URL environment variable is required in production")
            else:
                self.database_url = "sqlite:///pycommerce.db"

        # Media settings
        self.media_dir = os.environ.get("MEDIA_DIR", "static/media")
        self.uploads_dir = os.environ.get("UPLOADS_DIR", f"{self.media_dir}/uploads")
        self.generated_dir = os.environ.get("GENERATED_DIR", f"{self.media_dir}/generated")
        self.allowed_extensions = os.environ.get("ALLOWED_EXTENSIONS", "jpg,jpeg,png,gif,svg,pdf,doc,docx,xls,xlsx,ppt,pptx,mp4,mp3,wav,zip").split(",")
        self.max_upload_size = int(os.environ.get("MAX_UPLOAD_SIZE", "20971520"))  # 20MB

        # Create media directories if they don't exist
        os.makedirs(self.media_dir, exist_ok=True)
        os.makedirs(self.uploads_dir, exist_ok=True)
        os.makedirs(self.generated_dir, exist_ok=True)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting by key.

        Args:
            key: The setting key
            default: Default value if key is not found

        Returns:
            The setting value
        """
        return getattr(self, key, default)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert settings to a dictionary.

        Returns:
            Dictionary of all settings
        """
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith("_") and not callable(value)
        }


@lru_cache
def get_settings() -> Settings:
    """
    Get the settings singleton.

    Returns:
        Settings instance
    """
    return Settings()


# Export settings instance for easy import
settings = get_settings()