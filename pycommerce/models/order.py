"""
Order module for PyCommerce.

This module defines the Order model and related models.
"""

import uuid
import logging
import random
import string
from datetime import datetime
from enum import Enum, auto
from typing import List, Optional, Dict, Any, Union

from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Enum as SQLAlchemyEnum, and_, or_
from sqlalchemy.orm import relationship

from pycommerce.core.db import Base, get_session
from pycommerce.models.order_note import OrderNote
from pycommerce.models.order_item import OrderItem
from pycommerce.models.shipment import Shipment

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = auto()
    PROCESSING = auto()
    PAID = auto()
    SHIPPED = auto()
    DELIVERED = auto()
    COMPLETED = auto()
    CANCELLED = auto()
    REFUNDED = auto()


class OrderType(Enum):
    """Order type enumeration."""
    STANDARD = auto()  # Regular customer order
    TEST = auto()      # Test order for development/testing
    SUBSCRIPTION = auto()  # Recurring subscription order
    WHOLESALE = auto()  # Bulk order from wholesale customer
    BACKORDER = auto()  # Order for items currently out of stock
    PREORDER = auto()  # Order for items not yet released
    GIFT = auto()      # Gift order with special handling
    EXPEDITED = auto() # Order with expedited shipping priority
    INTERNATIONAL = auto() # International order with customs handling


class Order(Base):
    """Order model."""
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)
    customer_id = Column(String(36), nullable=True)
    order_number = Column(String(50), nullable=False, unique=True)
    status = Column(SQLAlchemyEnum(OrderStatus), default=OrderStatus.PENDING)
    # Note: order_type is commented out because it's not in the database yet
    # Uncomment this when performing a proper migration to add this column
    # order_type = Column(SQLAlchemyEnum(OrderType), default=OrderType.STANDARD)
    total = Column(Float, nullable=False, default=0.0)
    subtotal = Column(Float, nullable=False, default=0.0)
    tax = Column(Float, nullable=False, default=0.0)
    shipping_cost = Column(Float, nullable=False, default=0.0)
    discount = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Customer information
    customer_email = Column(String(255), nullable=True)
    customer_name = Column(String(255), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    
    # Shipping information
    shipping_address_line1 = Column(String(255), nullable=True)
    shipping_address_line2 = Column(String(255), nullable=True)
    shipping_city = Column(String(100), nullable=True)
    shipping_state = Column(String(100), nullable=True)
    shipping_postal_code = Column(String(20), nullable=True)
    shipping_country = Column(String(100), nullable=True)
    
    # Billing information
    billing_address_line1 = Column(String(255), nullable=True)
    billing_address_line2 = Column(String(255), nullable=True)
    billing_city = Column(String(100), nullable=True)
    billing_state = Column(String(100), nullable=True)
    billing_postal_code = Column(String(20), nullable=True)
    billing_country = Column(String(100), nullable=True)
    
    # Payment information
    payment_method = Column(String(100), nullable=True)
    payment_transaction_id = Column(String(255), nullable=True)
    is_paid = Column(Boolean, default=False)
    paid_at = Column(DateTime, nullable=True)
    
    # Shipping information
    tracking_number = Column(String(255), nullable=True)
    shipping_carrier = Column(String(100), nullable=True)
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    
    # Relationships
    notes = relationship("OrderNote", back_populates="order", cascade="all, delete-orphan")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    shipments = relationship("Shipment", back_populates="order", cascade="all, delete-orphan")


class OrderManager:
    """Manager class for orders."""

    def generate_order_number(self) -> str:
        """Generate a unique order number."""
        # Generate a random string of 8 characters
        chars = string.ascii_uppercase + string.digits
        random_part = ''.join(random.choice(chars) for _ in range(8))
        
        # Add a timestamp prefix to ensure uniqueness
        timestamp_part = datetime.now().strftime("%y%m%d")
        
        return f"ORD-{timestamp_part}-{random_part}"

    def get_by_id(self, order_id: str) -> Optional[Order]:
        """
        Get an order by ID.
        
        Args:
            order_id: The ID of the order
            
        Returns:
            The order if found, None otherwise
        """
        try:
            with get_session() as session:
                return session.query(Order).filter(Order.id == order_id).first()
        except Exception as e:
            logger.error(f"Error getting order: {str(e)}")
            return None

    def get_for_tenant(self, tenant_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Order]:
        """
        Get all orders for a tenant with optional filtering.
        
        Args:
            tenant_id: The ID of the tenant
            filters: Optional dictionary of filters to apply
            
        Returns:
            List of orders
        """
        try:
            with get_session() as session:
                query = session.query(Order).filter(Order.tenant_id == tenant_id)
                
                # Apply filters if provided
                if filters:
                    if 'status' in filters and filters['status']:
                        query = query.filter(Order.status == filters['status'])
                    
                    if 'customer_email' in filters and filters['customer_email']:
                        query = query.filter(Order.customer_email.like(f"%{filters['customer_email']}%"))
                    
                    if 'min_total' in filters and filters['min_total'] is not None:
                        query = query.filter(Order.total >= filters['min_total'])
                    
                    if 'max_total' in filters and filters['max_total'] is not None:
                        query = query.filter(Order.total <= filters['max_total'])
                    
                    if 'date_from' in filters and filters['date_from']:
                        query = query.filter(Order.created_at >= filters['date_from'])
                    
                    if 'date_to' in filters and filters['date_to']:
                        query = query.filter(Order.created_at <= filters['date_to'])
                
                # Order by created_at desc by default
                query = query.order_by(Order.created_at.desc())
                
                return query.all()
        except Exception as e:
            logger.error(f"Error getting orders: {str(e)}")
            return []

    def create_order(self, data: Dict[str, Any]) -> Optional[Order]:
        """
        Create a new order.
        
        Args:
            data: Dictionary containing order data
            
        Returns:
            The created order if successful, None otherwise
        """
        try:
            with get_session() as session:
                # Generate order number if not provided
                if 'order_number' not in data or not data['order_number']:
                    data['order_number'] = self.generate_order_number()
                
                order = Order(**data)
                session.add(order)
                session.commit()
                session.refresh(order)
                return order
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return None

    def update_order(self, order_id: str, data: Dict[str, Any]) -> Optional[Order]:
        """
        Update an order.
        
        Args:
            order_id: The ID of the order to update
            data: Dictionary containing updated order data
            
        Returns:
            The updated order if successful, None otherwise
        """
        try:
            with get_session() as session:
                order = session.query(Order).filter(Order.id == order_id).first()
                if not order:
                    return None
                
                # Update order attributes
                for key, value in data.items():
                    if hasattr(order, key) and key != 'id':
                        setattr(order, key, value)
                
                session.commit()
                session.refresh(order)
                return order
        except Exception as e:
            logger.error(f"Error updating order: {str(e)}")
            return None

    def update_status(self, order_id: str, status: OrderStatus) -> bool:
        """
        Update an order's status.
        
        Args:
            order_id: The ID of the order
            status: The new status
            
        Returns:
            True if the status was updated successfully, False otherwise
        """
        try:
            with get_session() as session:
                order = session.query(Order).filter(Order.id == order_id).first()
                if not order:
                    return False
                
                order.status = status
                
                # Update timestamps based on status
                if status == OrderStatus.PAID:
                    order.is_paid = True
                    order.paid_at = datetime.utcnow()
                elif status == OrderStatus.SHIPPED:
                    order.shipped_at = datetime.utcnow()
                elif status == OrderStatus.DELIVERED:
                    order.delivered_at = datetime.utcnow()
                
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating order status: {str(e)}")
            return False

    def update_shipping(self, order_id: str, status: str, tracking_number: Optional[str] = None, carrier: Optional[str] = None) -> bool:
        """
        Update shipping information for an order.
        
        Args:
            order_id: The ID of the order
            status: The shipping status (pending, ready, shipped, delivered, returned)
            tracking_number: Optional tracking number
            carrier: Optional shipping carrier
            
        Returns:
            True if the shipping info was updated successfully, False otherwise
        """
        try:
            with get_session() as session:
                order = session.query(Order).filter(Order.id == order_id).first()
                if not order:
                    return False
                
                # Update shipping fields
                if tracking_number:
                    order.tracking_number = tracking_number
                
                if carrier:
                    order.shipping_carrier = carrier
                
                # Update status based on shipping status
                if status == "shipped":
                    order.status = OrderStatus.SHIPPED
                    order.shipped_at = datetime.utcnow()
                elif status == "delivered":
                    order.status = OrderStatus.DELIVERED
                    order.delivered_at = datetime.utcnow()
                elif status == "returned":
                    # We could add a RETURNED status to OrderStatus if needed
                    pass
                
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating shipping information: {str(e)}")
            return False
    
    def delete_order(self, order_id: str) -> bool:
        """
        Delete an order.
        
        Args:
            order_id: The ID of the order to delete
            
        Returns:
            True if the order was deleted successfully, False otherwise
        """
        try:
            with get_session() as session:
                order = session.query(Order).filter(Order.id == order_id).first()
                if order:
                    session.delete(order)
                    session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting order: {str(e)}")
            return False