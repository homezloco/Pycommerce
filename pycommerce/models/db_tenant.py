"""
Tenant database model for PyCommerce.

This module defines the SQLAlchemy Tenant model for database interactions.
"""

import uuid
import logging
from datetime import datetime

from sqlalchemy import Column, String, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship

from pycommerce.core.db import Base

logger = logging.getLogger(__name__)


class Tenant(Base):
    """SQLAlchemy Tenant model."""
    __tablename__ = "tenants"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    domain = Column(String(255), unique=True, nullable=True)
    active = Column(Boolean, default=True)
    settings = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products = relationship("Product", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tenant {self.name}>"