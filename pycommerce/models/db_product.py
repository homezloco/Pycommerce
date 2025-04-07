"""
Product database model for PyCommerce.

This module defines the SQLAlchemy Product model for database interactions.
"""

import uuid
import logging
from datetime import datetime

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship

from pycommerce.core.db import Base
from pycommerce.models.db_tenant import Tenant
# Import inventory record class to resolve circular reference
from pycommerce.models.db_inventory import InventoryRecord

logger = logging.getLogger(__name__)


class Product(Base):
    """SQLAlchemy Product model."""
    __tablename__ = "products"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    price = Column(Float, nullable=False)
    sku = Column(String(100), nullable=False)
    stock = Column(Integer, default=0)
    categories = Column(JSON, default=list)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="products")
    inventory_records = relationship("InventoryRecord", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Product {self.name}>"