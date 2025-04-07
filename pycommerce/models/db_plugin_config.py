"""
Plugin configuration database model for PyCommerce.

This module defines the SQLAlchemy PluginConfig model for storing plugin configurations.
"""

import uuid
import logging
from datetime import datetime

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship

from pycommerce.core.db import Base

logger = logging.getLogger(__name__)


class PluginConfig(Base):
    """SQLAlchemy PluginConfig model for storing plugin configuration data."""
    __tablename__ = "plugin_configs"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    plugin_type = Column(String(50), nullable=False)  # 'payment', 'shipping', etc.
    plugin_id = Column(String(100), nullable=False)   # 'stripe', 'paypal', 'standard', etc.
    config = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with Tenant
    tenant = relationship("Tenant", back_populates="plugin_configs")
    
    def __repr__(self):
        return f"<PluginConfig {self.plugin_type}:{self.plugin_id} for tenant {self.tenant_id}>"