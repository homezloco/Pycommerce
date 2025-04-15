
"""
Database models for inventory management.

This module centralizes inventory-related models to avoid circular import issues.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from pycommerce.core.db import Base

# Importing these here to avoid circular imports
from pycommerce.models.db_registry import InventoryRecord

class InventoryTransaction(Base):
    """
    Represents a transaction affecting inventory.
    """
    __tablename__ = "inventory_transactions"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inventory_record_id = Column(String(36), ForeignKey("inventory_records.id"), nullable=False)
    transaction_type = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)  # Positive for additions, negative for reductions
    reference_id = Column(String(100), nullable=True)  # Optional reference (order ID, etc.)
    reference_type = Column(String(50), nullable=True)  # Type of reference (order, shipment, etc.)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), nullable=True)  # User who created the transaction
    transaction_metadata = Column(JSON, nullable=True)  # Renamed from metadata to avoid SQLAlchemy conflict

    # Define relationship with InventoryRecord
    inventory_record = relationship("InventoryRecord", foreign_keys=[inventory_record_id], 
                                   back_populates="transactions")

    def __repr__(self):
        return f"<InventoryTransaction {self.id} of type {self.transaction_type}>"
