"""
Shipment-related models and management.

This module defines the Shipment model and ShipmentManager class for
managing order shipments in the PyCommerce SDK.
"""

import logging
import uuid
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from enum import Enum

from pycommerce.core.db import Base, engine, get_session
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Boolean, Integer
from sqlalchemy.orm import relationship, Session
from pycommerce.models.product import Product
from pycommerce.models.order_item import OrderItem



logger = logging.getLogger("pycommerce.models.shipment")


class ShipmentStatus(str, Enum):
    """
    Possible statuses for a shipment.
    """
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    EXCEPTION = "exception"
    RETURNED = "returned"


class Shipment(Base):
    """
    Represents a shipment for an order.
    """
    __tablename__ = "shipments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    status = Column(String(50), default=ShipmentStatus.PENDING.value)
    tracking_number = Column(String(100), nullable=True)
    carrier = Column(String(100), nullable=True)
    shipping_method = Column(String(100), nullable=True)
    shipping_address = Column(JSON, nullable=True)
    shipping_cost = Column(Float, default=0.0)
    tracking_url = Column(String(255), nullable=True)
    label_url = Column(String(255), nullable=True)
    estimated_delivery = Column(DateTime, nullable=True)
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    shipment_metadata = Column(JSON, nullable=True)  # Renamed from metadata to avoid reserved name conflict
    
    # Relationships
    order = relationship("Order", back_populates="shipments")
    items = relationship("ShipmentItem", back_populates="shipment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Shipment {self.id}>"


class ShipmentItem(Base):
    """
    Represents an item in a shipment.
    """
    __tablename__ = "shipment_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    shipment_id = Column(String(36), ForeignKey("shipments.id"), nullable=False)
    order_item_id = Column(String(36), ForeignKey("order_items.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    shipment = relationship("Shipment", back_populates="items", lazy="selectin")
    order_item = relationship(OrderItem, lazy="selectin")
    product = relationship(Product, lazy="selectin")
    
    def __repr__(self):
        return f"<ShipmentItem {self.id}>"


class ShipmentManager:
    """
    Manager for shipment operations.
    """
    
    def __init__(self, session_factory=get_session):
        """
        Initialize the shipment manager.
        
        Args:
            session_factory: Function that provides a database session
        """
        self.session_factory = session_factory
    
    def create_shipment(
        self,
        order_id: str,
        shipping_method: str,
        tracking_number: Optional[str] = None,
        carrier: Optional[str] = None,
        shipping_address: Optional[Dict[str, Any]] = None,
        tracking_url: Optional[str] = None,
        label_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Shipment:
        """
        Create a new shipment for an order.
        
        Args:
            order_id: The ID of the order to create shipment for
            shipping_method: The shipping method name
            tracking_number: Optional tracking number
            carrier: Optional carrier name
            shipping_address: Optional shipping address information
            tracking_url: Optional URL to track the shipment
            label_url: Optional URL to download shipping label
            metadata: Optional additional metadata
            
        Returns:
            The created shipment
            
        Raises:
            ValueError: If the order doesn't exist
        """
        with self.session_factory() as session:
            # Check if the order exists
            from pycommerce.models.order import Order
            order = session.query(Order).filter_by(id=order_id).first()
            if not order:
                raise ValueError(f"Order not found: {order_id}")
                
            # Create the shipment
            shipment = Shipment(
                order_id=order_id,
                shipping_method=shipping_method,
                tracking_number=tracking_number,
                carrier=carrier,
                shipping_address=shipping_address,
                tracking_url=tracking_url,
                label_url=label_url,
                shipment_metadata=metadata or {}
            )
            
            session.add(shipment)
            session.commit()
            session.refresh(shipment)
            
            logger.info(f"Created shipment {shipment.id} for order {order_id}")
            
            return shipment
    
    def add_items_to_shipment(
        self,
        shipment_id: str,
        items: List[Dict[str, Any]]
    ) -> List[ShipmentItem]:
        """
        Add items to a shipment.
        
        Args:
            shipment_id: The ID of the shipment
            items: List of items to add, each with order_item_id, product_id, and quantity
            
        Returns:
            List of created shipment items
            
        Raises:
            ValueError: If the shipment doesn't exist
        """
        with self.session_factory() as session:
            # Check if the shipment exists
            shipment = session.query(Shipment).filter_by(id=shipment_id).first()
            if not shipment:
                raise ValueError(f"Shipment not found: {shipment_id}")
                
            shipment_items = []
            for item_data in items:
                shipment_item = ShipmentItem(
                    shipment_id=shipment_id,
                    order_item_id=item_data["order_item_id"],
                    product_id=item_data["product_id"],
                    quantity=item_data.get("quantity", 1)
                )
                session.add(shipment_item)
                shipment_items.append(shipment_item)
            
            session.commit()
            for item in shipment_items:
                session.refresh(item)
            
            logger.info(f"Added {len(shipment_items)} items to shipment {shipment_id}")
            
            return shipment_items
    
    def update_shipment_status(
        self,
        shipment_id: str,
        status: Union[str, ShipmentStatus],
        tracking_number: Optional[str] = None,
        tracking_url: Optional[str] = None,
        estimated_delivery: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Shipment:
        """
        Update the status of a shipment.
        
        Args:
            shipment_id: The ID of the shipment to update
            status: The new status
            tracking_number: Optional updated tracking number
            tracking_url: Optional updated tracking URL
            estimated_delivery: Optional estimated delivery date
            metadata: Optional additional metadata to merge with existing metadata
            
        Returns:
            The updated shipment
            
        Raises:
            ValueError: If the shipment doesn't exist
        """
        with self.session_factory() as session:
            # Check if the shipment exists
            shipment = session.query(Shipment).filter_by(id=shipment_id).first()
            if not shipment:
                raise ValueError(f"Shipment not found: {shipment_id}")
            
            # Update the shipment
            shipment.status = status.value if isinstance(status, ShipmentStatus) else status
            
            if tracking_number is not None:
                shipment.tracking_number = tracking_number
                
            if tracking_url is not None:
                shipment.tracking_url = tracking_url
                
            if estimated_delivery is not None:
                shipment.estimated_delivery = estimated_delivery
                
            # Update timestamp fields based on status
            if status == ShipmentStatus.SHIPPED or status == "shipped":
                shipment.shipped_at = datetime.utcnow()
                
            if status == ShipmentStatus.DELIVERED or status == "delivered":
                shipment.delivered_at = datetime.utcnow()
                
            # Update metadata if provided
            if metadata:
                current_metadata = shipment.shipment_metadata or {}
                current_metadata.update(metadata)
                shipment.shipment_metadata = current_metadata
            
            session.commit()
            session.refresh(shipment)
            
            logger.info(f"Updated shipment {shipment_id} status to {status}")
            
            # Update order status if needed
            self._update_order_status_based_on_shipments(session, shipment.order_id)
            
            return shipment
    
    def get_shipment(self, shipment_id: str) -> Optional[Shipment]:
        """
        Get a shipment by ID.
        
        Args:
            shipment_id: The ID of the shipment to get
            
        Returns:
            The shipment, or None if not found
        """
        with self.session_factory() as session:
            return session.query(Shipment).filter_by(id=shipment_id).first()
    
    def get_shipments_for_order(self, order_id: str) -> List[Shipment]:
        """
        Get all shipments for an order.
        
        Args:
            order_id: The ID of the order
            
        Returns:
            List of shipments for the order
        """
        with self.session_factory() as session:
            return session.query(Shipment).filter_by(order_id=order_id).all()
    
    def _update_order_status_based_on_shipments(self, session: Session, order_id: str):
        """
        Update the order status based on the status of its shipments.
        
        Args:
            session: The database session
            order_id: The order ID
        """
        from pycommerce.models.order import Order, OrderStatus
        
        # Get the order
        order = session.query(Order).filter_by(id=order_id).first()
        if not order:
            logger.warning(f"Order not found when updating status: {order_id}")
            return
            
        # Get all shipments for the order
        shipments = session.query(Shipment).filter_by(order_id=order_id).all()
        if not shipments:
            logger.info(f"No shipments found for order {order_id}")
            return
            
        # Determine the new order status based on shipment statuses
        shipment_statuses = [s.status for s in shipments]
        
        if all(s == ShipmentStatus.DELIVERED.value for s in shipment_statuses):
            # All shipments delivered
            order.status = OrderStatus.DELIVERED.value
        elif any(s == ShipmentStatus.SHIPPED.value for s in shipment_statuses):
            # At least one shipment has been shipped
            order.status = OrderStatus.SHIPPED.value
        elif all(s in [ShipmentStatus.PENDING.value, ShipmentStatus.PROCESSING.value] for s in shipment_statuses):
            # All shipments are being processed
            order.status = OrderStatus.PROCESSING.value
            
        session.commit()
        logger.info(f"Updated order {order_id} status to {order.status} based on shipments")


# Create the tables
Base.metadata.create_all(engine)