"""
Credentials Manager for PyCommerce.

This module handles secure storage and retrieval of API credentials and other
sensitive information used by the application.
"""

import os
import json
import logging
import base64
from typing import Dict, Any, Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from pycommerce.services.settings_service import SettingsService, SystemSetting, db_session

# Configure logging
logger = logging.getLogger(__name__)

class CredentialsManager:
    """
    Manages secure storage and retrieval of credentials.
    
    This class handles encryption, decryption, and storage of sensitive credentials
    such as API keys for payment providers, using Fernet symmetric encryption.
    """
    
    def __init__(self):
        """Initialize the credentials manager."""
        self._encryption_key = self._get_or_create_encryption_key()
        self._fernet = Fernet(self._encryption_key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """
        Get or create the encryption key used for credential encryption.
        
        Returns:
            bytes: The encryption key
        """
        # Try to get existing key from environment or settings
        encryption_key = os.environ.get("CREDENTIALS_ENCRYPTION_KEY")
        
        if not encryption_key:
            # Check if key exists in settings
            try:
                session = db_session()
                key_setting = session.query(SystemSetting).filter(
                    SystemSetting.key == "system.credentials_encryption_key"
                ).first()
                
                if key_setting and key_setting.value:
                    encryption_key = key_setting.value
                session.close()
            except Exception as e:
                logger.error(f"Error getting encryption key from database: {str(e)}")
        
        if not encryption_key:
            # Generate a new key if none exists
            logger.info("Generating new credentials encryption key")
            
            # Use application secret as salt
            app_secret = os.environ.get("APP_SECRET", "pycommerce-development-secret")
            salt = app_secret.encode()[:16].ljust(16, b'\0')  # Ensure salt is 16 bytes
            
            # Generate a key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            # Generate a random password for the key
            password = os.urandom(32)
            key = base64.urlsafe_b64encode(kdf.derive(password))
            
            # Store the key in settings
            try:
                session = db_session()
                key_setting = SystemSetting(
                    key="system.credentials_encryption_key",
                    value=key.decode(),
                    description="Encryption key for credentials"
                )
                session.add(key_setting)
                session.commit()
                session.close()
                
                encryption_key = key.decode()
            except Exception as e:
                logger.error(f"Error storing encryption key in database: {str(e)}")
                # Fallback to a temporary key - will not persist across restarts
                encryption_key = key.decode()
        
        return encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
    
    def encrypt(self, value: str) -> str:
        """
        Encrypt a value.
        
        Args:
            value: The value to encrypt
            
        Returns:
            The encrypted value as a string
        """
        if not value:
            return ""
        
        encrypted = self._fernet.encrypt(value.encode())
        return encrypted.decode()
    
    def decrypt(self, encrypted_value: str) -> str:
        """
        Decrypt a value.
        
        Args:
            encrypted_value: The encrypted value to decrypt
            
        Returns:
            The decrypted value
        """
        if not encrypted_value:
            return ""
            
        try:
            decrypted = self._fernet.decrypt(encrypted_value.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Error decrypting value: {str(e)}")
            return ""
    
    def store_credentials(self, provider: str, credentials: Dict[str, Any], tenant_id: Optional[str] = None) -> bool:
        """
        Store encrypted credentials for a provider.
        
        Args:
            provider: The provider identifier (e.g., 'stripe', 'paypal')
            credentials: The credentials to store
            tenant_id: Optional tenant ID for tenant-specific credentials
            
        Returns:
            True if successful, False otherwise
        """
        try:
            settings_service = SettingsService()
            
            # Encrypt sensitive fields
            encrypted_credentials = {}
            for key, value in credentials.items():
                if self._is_sensitive_field(key):
                    encrypted_credentials[key] = self.encrypt(str(value))
                else:
                    encrypted_credentials[key] = value
            
            # Create key for the settings
            settings_key = f"credentials.{provider}"
            if tenant_id:
                settings_key = f"tenant.{tenant_id}.{settings_key}"
            
            # Store in settings service
            with settings_service.get_session() as session:
                setting = session.query(SystemSetting).filter(
                    SystemSetting.key == settings_key
                ).first()
                
                if setting:
                    setting.value = json.dumps(encrypted_credentials)
                else:
                    setting = SystemSetting(
                        key=settings_key,
                        value=json.dumps(encrypted_credentials),
                        description=f"Encrypted credentials for {provider}"
                    )
                    session.add(setting)
                
                session.commit()
            
            return True
        
        except Exception as e:
            logger.error(f"Error storing credentials for {provider}: {str(e)}")
            return False
    
    def get_credentials(self, provider: str, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve and decrypt credentials for a provider.
        
        Args:
            provider: The provider identifier (e.g., 'stripe', 'paypal')
            tenant_id: Optional tenant ID for tenant-specific credentials
            
        Returns:
            The decrypted credentials
        """
        try:
            settings_service = SettingsService()
            
            # Create key for the settings
            settings_key = f"credentials.{provider}"
            if tenant_id:
                settings_key = f"tenant.{tenant_id}.{settings_key}"
            
            # Try to get tenant-specific settings first, fall back to global settings
            encrypted_credentials = None
            
            with settings_service.get_session() as session:
                setting = session.query(SystemSetting).filter(
                    SystemSetting.key == settings_key
                ).first()
                
                if setting and setting.value:
                    encrypted_credentials = json.loads(setting.value)
                elif tenant_id:
                    # Fall back to global settings if tenant-specific not found
                    global_key = f"credentials.{provider}"
                    global_setting = session.query(SystemSetting).filter(
                        SystemSetting.key == global_key
                    ).first()
                    
                    if global_setting and global_setting.value:
                        encrypted_credentials = json.loads(global_setting.value)
            
            if not encrypted_credentials:
                return {}
            
            # Decrypt sensitive fields
            decrypted_credentials = {}
            for key, value in encrypted_credentials.items():
                if self._is_sensitive_field(key) and value:
                    decrypted_credentials[key] = self.decrypt(str(value))
                else:
                    decrypted_credentials[key] = value
            
            return decrypted_credentials
        
        except Exception as e:
            logger.error(f"Error retrieving credentials for {provider}: {str(e)}")
            return {}
    
    def validate_credentials(self, provider: str, credentials: Dict[str, Any]) -> bool:
        """
        Validate that credentials contain all required fields for a provider.
        
        Args:
            provider: The provider identifier (e.g., 'stripe', 'paypal')
            credentials: The credentials to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = self._get_required_fields(provider)
        
        if not required_fields:
            logger.warning(f"No required fields defined for provider: {provider}")
            return True
        
        for field in required_fields:
            if field not in credentials or not credentials[field]:
                logger.warning(f"Missing required field '{field}' for provider {provider}")
                return False
        
        return True
    
    def _is_sensitive_field(self, field_name: str) -> bool:
        """
        Determine if a field is sensitive and should be encrypted.
        
        Args:
            field_name: The name of the field
            
        Returns:
            True if sensitive, False otherwise
        """
        sensitive_patterns = [
            "api_key", "secret", "password", "token", "private_key", "webhook_secret", 
            "client_secret", "access_token", "refresh_token", "key"
        ]
        
        field_lower = field_name.lower()
        return any(pattern in field_lower for pattern in sensitive_patterns)
    
    def _get_required_fields(self, provider: str) -> list:
        """
        Get the required fields for a specific provider.
        
        Args:
            provider: The provider identifier (e.g., 'stripe', 'paypal')
            
        Returns:
            List of required field names
        """
        provider_fields = {
            "stripe": ["api_key", "public_key"],
            "paypal": ["client_id", "client_secret"],
            "openai": ["api_key"],
            "google": ["api_key"],
            "deepseek": ["api_key"],
            "openrouter": ["api_key"]
        }
        
        return provider_fields.get(provider.lower(), [])


# Global instance
credentials_manager = CredentialsManager()