"""
Order Item model for PyCommerce.

This module defines the OrderItem model which represents an item in an order.
"""

import uuid
import logging
from datetime import datetime

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from pycommerce.core.db import Base
from pycommerce.models.product import Product

logger = logging.getLogger(__name__)


class OrderItem(Base):
    """Order item model."""
    __tablename__ = "order_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(Float, nullable=False)  # Price at the time of order
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    order = relationship("Order", back_populates="items", lazy="selectin")
    # Using the directly imported Product class
    product = relationship(Product, lazy="selectin")
    
    def __repr__(self):
        return f"<OrderItem {self.id}>"