"""
Inventory database model for PyCommerce.

This module defines the SQLAlchemy InventoryRecord model for tracking product inventory.
"""

import uuid
import logging
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from pycommerce.core.db import Base

logger = logging.getLogger(__name__)


class InventoryRecord(Base):
    """SQLAlchemy InventoryRecord model for tracking inventory changes."""
    __tablename__ = "inventory_records"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    quantity_change = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="inventory_records")
    
    def __repr__(self):
        return f"<InventoryRecord {self.id}: {self.quantity_change}>"