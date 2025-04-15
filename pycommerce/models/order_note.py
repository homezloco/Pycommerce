
"""
Order note module for PyCommerce.

This module defines the OrderNote model and OrderNoteManager.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import logging

from pycommerce.core.db import Base

logger = logging.getLogger(__name__)

# Import get_session function inside methods to avoid circular imports
def get_session():
    """Import and return the session factory to avoid circular imports."""
    from pycommerce.core.db import get_session as core_get_session
    return core_get_session()

class OrderNote(Base):
    """Order note model."""
    __tablename__ = "order_notes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_customer_note = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Define relationship with string reference to avoid circular imports
    order = relationship("pycommerce.models.order.Order", back_populates="notes", lazy="selectin")

class OrderNoteManager:
    """Manager class for order notes."""

    def get_for_order(self, order_id: str) -> List[OrderNote]:
        """
        Get all notes for an order.
        
        Args:
            order_id: The ID of the order
            
        Returns:
            List of order notes
        """
        try:
            session_factory = get_session()
            with session_factory() as session:
                notes = session.query(OrderNote).filter(
                    OrderNote.order_id == order_id
                ).order_by(OrderNote.created_at.desc()).all()
                return notes
        except Exception as e:
            logger.error(f"Error getting order notes: {str(e)}")
            return []

    def add_note(self, order_id: str, content: str, is_customer_note: bool = False) -> bool:
        """
        Add a note to an order.
        
        Args:
            order_id: The ID of the order
            content: The content of the note
            is_customer_note: Whether the note is visible to the customer
            
        Returns:
            True if the note was added successfully, False otherwise
        """
        try:
            session_factory = get_session()
            with session_factory() as session:
                note = OrderNote(
                    order_id=order_id,
                    content=content,
                    is_customer_note=is_customer_note
                )
                session.add(note)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding order note: {str(e)}")
            return False

    def delete_note(self, note_id: str) -> bool:
        """
        Delete a note.
        
        Args:
            note_id: The ID of the note to delete
            
        Returns:
            True if the note was deleted successfully, False otherwise
        """
        try:
            session_factory = get_session()
            with session_factory() as session:
                note = session.query(OrderNote).filter(OrderNote.id == note_id).first()
                if note:
                    session.delete(note)
                    session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting order note: {str(e)}")
            return False
