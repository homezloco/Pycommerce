"""
Return Request model for PyCommerce.

This module defines the ReturnRequest model and related functionality for handling
customer returns and refunds.
"""

import uuid
import logging
from datetime import datetime
from enum import Enum, auto
from typing import List, Optional, Dict, Any, Union

from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Enum as SQLAlchemyEnum, JSON
from sqlalchemy.orm import relationship

from pycommerce.core.db import Base, get_session

logger = logging.getLogger(__name__)


class ReturnStatus(Enum):
    """Return status enumeration."""
    REQUESTED = auto()  # Customer has requested a return
    APPROVED = auto()   # Return request approved by merchant
    DENIED = auto()     # Return request denied by merchant
    AWAITING_RECEIPT = auto()  # Waiting for customer to send items back
    RECEIVED = auto()   # Items have been received by merchant
    INSPECTING = auto() # Items are being inspected for damage/condition
    COMPLETED = auto()  # Return process is completed
    REFUNDED = auto()   # Refund has been processed


class ReturnReason(Enum):
    """Return reason enumeration."""
    DAMAGED = auto()          # Item arrived damaged
    DEFECTIVE = auto()        # Item is defective
    NOT_AS_DESCRIBED = auto() # Item different from description
    WRONG_ITEM = auto()       # Wrong item was sent
    WRONG_SIZE = auto()       # Item is wrong size
    NO_LONGER_NEEDED = auto() # Customer no longer needs
    ARRIVED_LATE = auto()     # Order arrived too late
    OTHER = auto()            # Other reason


class ReturnRequest(Base):
    """Return Request model."""
    __tablename__ = "return_requests"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    return_number = Column(String(50), nullable=False, unique=True)
    status = Column(String(50), default=ReturnStatus.REQUESTED.name)
    reason = Column(String(50), nullable=True)
    customer_comments = Column(String(1000), nullable=True)
    admin_notes = Column(String(1000), nullable=True)
    
    # Return processing dates
    requested_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    received_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Refund information
    refund_amount = Column(Float, nullable=True)
    refund_transaction_id = Column(String(255), nullable=True)
    refund_method = Column(String(100), nullable=True)
    refunded_at = Column(DateTime, nullable=True)
    is_refunded = Column(Boolean, default=False)
    
    # Shipping information for returns
    return_shipping_label = Column(String(255), nullable=True)
    return_tracking_number = Column(String(100), nullable=True)
    return_carrier = Column(String(100), nullable=True)
    
    # Relationships
    order = relationship("Order", back_populates="returns")
    items = relationship("ReturnItem", back_populates="return_request", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ReturnRequest {self.id}>"


class ReturnItem(Base):
    """Return Item model."""
    __tablename__ = "return_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    return_id = Column(String(36), ForeignKey("return_requests.id"), nullable=False)
    order_item_id = Column(String(36), ForeignKey("order_items.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    reason = Column(String(50), nullable=True)
    condition = Column(String(50), nullable=True)  # New, Used, Damaged, etc.
    refund_amount = Column(Float, nullable=True)
    restocked = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    return_request = relationship("ReturnRequest", back_populates="items")
    order_item = relationship("OrderItem")
    product = relationship("Product")
    
    def __repr__(self):
        return f"<ReturnItem {self.id}>"


class ReturnManager:
    """Manager class for return requests."""
    
    def generate_return_number(self) -> str:
        """Generate a unique return number."""
        # Generate a random string of 8 characters
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        random_part = ''.join(uuid.uuid4().hex[:8].upper())
        
        # Add a timestamp prefix to ensure uniqueness
        timestamp_part = datetime.now().strftime("%y%m%d")
        
        return f"RET-{timestamp_part}-{random_part}"
    
    def get_by_id(self, return_id: str) -> Optional[ReturnRequest]:
        """
        Get a return request by ID.
        
        Args:
            return_id: The ID of the return request
            
        Returns:
            The return request if found, None otherwise
        """
        try:
            with get_session() as session:
                return session.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
        except Exception as e:
            logger.error(f"Error getting return request: {str(e)}")
            return None
    
    def get_for_order(self, order_id: str) -> List[ReturnRequest]:
        """
        Get all return requests for an order.
        
        Args:
            order_id: The ID of the order
            
        Returns:
            List of return requests for the order
        """
        try:
            with get_session() as session:
                return session.query(ReturnRequest).filter(ReturnRequest.order_id == order_id).all()
        except Exception as e:
            logger.error(f"Error getting return requests for order: {str(e)}")
            return []
    
    def get_for_tenant(self, tenant_id: str, filters: Optional[Dict[str, Any]] = None) -> List[ReturnRequest]:
        """
        Get all return requests for a tenant with optional filtering.
        
        Args:
            tenant_id: The ID of the tenant
            filters: Optional dictionary of filters to apply
            
        Returns:
            List of return requests
        """
        try:
            with get_session() as session:
                # Join with orders to filter by tenant
                query = session.query(ReturnRequest).join(
                    ReturnRequest.order
                ).filter(ReturnRequest.order.has(tenant_id=tenant_id))
                
                # Apply filters if provided
                if filters:
                    if 'status' in filters and filters['status']:
                        query = query.filter(ReturnRequest.status == filters['status'])
                    
                    if 'date_from' in filters and filters['date_from']:
                        query = query.filter(ReturnRequest.requested_at >= filters['date_from'])
                    
                    if 'date_to' in filters and filters['date_to']:
                        query = query.filter(ReturnRequest.requested_at <= filters['date_to'])
                
                # Order by requested_at desc by default
                query = query.order_by(ReturnRequest.requested_at.desc())
                
                return query.all()
        except Exception as e:
            logger.error(f"Error getting return requests: {str(e)}")
            return []
    
    def create_return(self, data: Dict[str, Any]) -> Optional[ReturnRequest]:
        """
        Create a new return request.
        
        Args:
            data: Dictionary containing return request data
            
        Returns:
            The created return request if successful, None otherwise
        """
        try:
            with get_session() as session:
                # Generate return number if not provided
                if 'return_number' not in data or not data['return_number']:
                    data['return_number'] = self.generate_return_number()
                
                return_request = ReturnRequest(**data)
                session.add(return_request)
                session.commit()
                session.refresh(return_request)
                return return_request
        except Exception as e:
            logger.error(f"Error creating return request: {str(e)}")
            return None
    
    def add_item_to_return(self, return_id: str, item_data: Dict[str, Any]) -> bool:
        """
        Add an item to a return request.
        
        Args:
            return_id: ID of the return request
            item_data: Data for the return item
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with get_session() as session:
                # Check if return exists
                return_request = session.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
                if not return_request:
                    logger.error(f"Return request not found: {return_id}")
                    return False
                
                # Create return item
                item_data['return_id'] = return_id
                return_item = ReturnItem(**item_data)
                session.add(return_item)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding item to return: {str(e)}")
            return False
    
    def update_return_status(self, return_id: str, status: str, notes: Optional[str] = None) -> bool:
        """
        Update a return request status.
        
        Args:
            return_id: The ID of the return request
            status: The new status
            notes: Optional notes about the status change
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with get_session() as session:
                return_request = session.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
                if not return_request:
                    return False
                
                # Update status
                return_request.status = status
                
                # Add notes if provided
                if notes:
                    if return_request.admin_notes:
                        return_request.admin_notes += f"\n\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} - Status changed to {status}:\n{notes}"
                    else:
                        return_request.admin_notes = f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} - Status changed to {status}:\n{notes}"
                
                # Update timestamps based on status
                if status == ReturnStatus.APPROVED.name:
                    return_request.approved_at = datetime.utcnow()
                elif status == ReturnStatus.RECEIVED.name:
                    return_request.received_at = datetime.utcnow()
                elif status == ReturnStatus.COMPLETED.name:
                    return_request.completed_at = datetime.utcnow()
                elif status == ReturnStatus.REFUNDED.name:
                    return_request.is_refunded = True
                    return_request.refunded_at = datetime.utcnow()
                
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating return status: {str(e)}")
            return False
    
    def process_refund(self, return_id: str, refund_data: Dict[str, Any]) -> bool:
        """
        Process a refund for a return request.
        
        Args:
            return_id: The ID of the return request
            refund_data: Dictionary with refund information
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with get_session() as session:
                return_request = session.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
                if not return_request:
                    return False
                
                # Update refund fields
                return_request.refund_amount = refund_data.get('amount')
                return_request.refund_method = refund_data.get('method')
                return_request.refund_transaction_id = refund_data.get('transaction_id')
                return_request.refunded_at = datetime.utcnow()
                return_request.is_refunded = True
                
                # Update status to REFUNDED
                return_request.status = ReturnStatus.REFUNDED.name
                
                # Add notes if provided
                notes = refund_data.get('notes')
                if notes:
                    if return_request.admin_notes:
                        return_request.admin_notes += f"\n\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} - Refund processed:\n{notes}"
                    else:
                        return_request.admin_notes = f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} - Refund processed:\n{notes}"
                
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error processing refund: {str(e)}")
            return False