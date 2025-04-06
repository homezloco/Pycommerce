"""
Settings service for PyCommerce platform.

This module provides functionality for storing and retrieving global configuration settings.
"""

import json
import logging
from typing import Any, Dict, Optional
from sqlalchemy import Column, String, Text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from pycommerce.core.db import Base, engine
from sqlalchemy.orm import sessionmaker, scoped_session

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionLocal)

logger = logging.getLogger(__name__)

class SystemSetting(Base):
    """Model for storing system-wide settings."""
    __tablename__ = "system_settings"
    
    key = Column(String(255), primary_key=True)
    value = Column(Text, nullable=True)
    description = Column(String(500), nullable=True)
    setting_type = Column(String(50), default="string")  # string, boolean, number, json

class SettingsService:
    """Service for managing system settings."""
    
    @classmethod
    async def get_setting(cls, key: str, default: Any = None) -> Any:
        """
        Get a system setting by key.
        
        Args:
            key: The settings key
            default: Default value if setting doesn't exist
            
        Returns:
            The setting value, or the default if not found
        """
        session = db_session()
        try:
            setting = session.query(SystemSetting).filter(SystemSetting.key == key).first()
            if not setting:
                return default
                
            # Convert value based on setting type
            if setting.setting_type == "boolean":
                return setting.value.lower() in ("true", "1", "yes")
            elif setting.setting_type == "number":
                try:
                    if "." in setting.value:
                        return float(setting.value)
                    else:
                        return int(setting.value)
                except (ValueError, TypeError):
                    return default
            elif setting.setting_type == "json":
                try:
                    return json.loads(setting.value)
                except (json.JSONDecodeError, TypeError):
                    return default
            else:
                return setting.value
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving setting {key}: {str(e)}")
            return default
        finally:
            session.close()
            
    @classmethod
    async def set_setting(cls, key: str, value: Any, description: Optional[str] = None, 
                        setting_type: Optional[str] = None) -> bool:
        """
        Set a system setting.
        
        Args:
            key: The setting key
            value: The setting value
            description: Optional description of the setting
            setting_type: Type of setting (string, boolean, number, json)
            
        Returns:
            True if successful, False otherwise
        """
        session = db_session()
        try:
            # Determine setting type if not provided
            if setting_type is None:
                if isinstance(value, bool):
                    setting_type = "boolean"
                elif isinstance(value, (int, float)):
                    setting_type = "number"
                elif isinstance(value, (dict, list)):
                    setting_type = "json"
                else:
                    setting_type = "string"
                    
            # Format value for storage
            if setting_type == "boolean":
                stored_value = str(value).lower()
            elif setting_type == "json":
                stored_value = json.dumps(value)
            else:
                stored_value = str(value)
                
            # Check if setting exists
            setting = session.query(SystemSetting).filter(SystemSetting.key == key).first()
            
            if setting:
                # Update existing setting
                setting.value = stored_value
                setting.setting_type = setting_type
                if description:
                    setting.description = description
            else:
                # Create new setting
                setting = SystemSetting(
                    key=key,
                    value=stored_value,
                    description=description,
                    setting_type=setting_type
                )
                session.add(setting)
                
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error saving setting {key}: {str(e)}")
            return False
        finally:
            session.close()
            
    @classmethod
    async def delete_setting(cls, key: str) -> bool:
        """
        Delete a system setting.
        
        Args:
            key: The setting key to delete
            
        Returns:
            True if successful, False otherwise
        """
        session = db_session()
        try:
            session.query(SystemSetting).filter(SystemSetting.key == key).delete()
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error deleting setting {key}: {str(e)}")
            return False
        finally:
            session.close()
            
    @classmethod
    async def get_all_settings(cls, prefix: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all system settings, optionally filtered by prefix.
        
        Args:
            prefix: Optional prefix to filter settings by (e.g., 'payment.')
            
        Returns:
            Dictionary of setting keys and values
        """
        session = db_session()
        try:
            query = session.query(SystemSetting)
            if prefix:
                query = query.filter(SystemSetting.key.startswith(prefix))
                
            settings = {}
            for setting in query.all():
                # Convert value based on setting type
                if setting.setting_type == "boolean":
                    settings[setting.key] = setting.value.lower() in ("true", "1", "yes")
                elif setting.setting_type == "number":
                    try:
                        if "." in setting.value:
                            settings[setting.key] = float(setting.value)
                        else:
                            settings[setting.key] = int(setting.value)
                    except (ValueError, TypeError):
                        settings[setting.key] = setting.value
                elif setting.setting_type == "json":
                    try:
                        settings[setting.key] = json.loads(setting.value)
                    except (json.JSONDecodeError, TypeError):
                        settings[setting.key] = setting.value
                else:
                    settings[setting.key] = setting.value
                    
            return settings
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving settings: {str(e)}")
            return {}
        finally:
            session.close()