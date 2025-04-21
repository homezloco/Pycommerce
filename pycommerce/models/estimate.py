"""
Estimate model for PyCommerce.

This module defines the Estimate model and related models for tracking
quotes before they become orders.
"""

import uuid
import logging
from datetime import datetime

from sqlalchemy.sql import func
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship

from pycommerce.core.db import Base

logger = logging.getLogger(__name__)


class Estimate(Base):
    """Estimate model for tracking quotes before they become orders."""
    __tablename__ = "estimates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)
    customer_id = Column(String(36), nullable=True)
    estimate_number = Column(String(50), nullable=False, unique=True)
    status = Column(String(50), default="DRAFT")
    total = Column(Float, nullable=False, default=0.0)
    subtotal = Column(Float, nullable=False, default=0.0)
    tax = Column(Float, nullable=False, default=0.0)
    
    # Profit calculation fields
    total_cost = Column(Float, nullable=False, default=0.0)
    total_profit = Column(Float, nullable=False, default=0.0)
    profit_margin = Column(Float, nullable=False, default=0.0)  # Stored as percentage
    
    # Customer information
    customer_email = Column(String(255), nullable=True)
    customer_name = Column(String(255), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    
    # Project details
    project_name = Column(String(255), nullable=True)
    project_description = Column(Text, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    materials = relationship("EstimateMaterial", back_populates="estimate", cascade="all, delete-orphan")
    labor_items = relationship("EstimateLabor", back_populates="estimate", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Estimate {self.id}>"
        
    def calculate_totals(self):
        """Calculate the total cost, selling price, and profit margin."""
        material_cost = sum(m.cost_price * m.quantity for m in self.materials)
        material_price = sum(m.selling_price * m.quantity for m in self.materials)
        
        labor_cost = sum(l.cost_price * l.hours for l in self.labor_items)
        labor_price = sum(l.selling_price * l.hours for l in self.labor_items)
        
        self.total_cost = material_cost + labor_cost
        self.subtotal = material_price + labor_price
        
        # Add tax
        self.total = self.subtotal * (1 + (self.tax / 100))
        
        # Calculate profit
        self.total_profit = self.subtotal - self.total_cost
        
        # Calculate profit margin as a percentage
        if self.subtotal > 0:
            self.profit_margin = (self.total_profit / self.subtotal) * 100
        else:
            self.profit_margin = 0


class EstimateMaterial(Base):
    """Material items for an estimate."""
    __tablename__ = "estimate_materials"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    estimate_id = Column(String(36), ForeignKey("estimates.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Float, nullable=False, default=1.0)
    unit = Column(String(50), nullable=True)  # e.g., "sq ft", "piece", etc.
    
    # Cost and pricing
    cost_price = Column(Float, nullable=False, default=0.0)  # Cost to business
    selling_price = Column(Float, nullable=False, default=0.0)  # Price charged to customer
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    estimate = relationship("Estimate", back_populates="materials")
    
    def __repr__(self):
        return f"<EstimateMaterial {self.id}>"
        
    @property
    def total_cost(self):
        """Calculate the total cost for this material."""
        return self.cost_price * self.quantity
        
    @property
    def total_price(self):
        """Calculate the total selling price for this material."""
        return self.selling_price * self.quantity
        
    @property
    def profit(self):
        """Calculate the profit for this material."""
        return self.total_price - self.total_cost
        
    @property
    def profit_margin(self):
        """Calculate the profit margin as a percentage."""
        if self.total_price > 0:
            return (self.profit / self.total_price) * 100
        return 0


class EstimateLabor(Base):
    """Labor items for an estimate."""
    __tablename__ = "estimate_labor"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    estimate_id = Column(String(36), ForeignKey("estimates.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    hours = Column(Float, nullable=False, default=1.0)
    
    # Cost and pricing
    cost_price = Column(Float, nullable=False, default=0.0)  # Cost per hour
    selling_price = Column(Float, nullable=False, default=0.0)  # Price per hour charged to customer
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    estimate = relationship("Estimate", back_populates="labor_items")
    
    def __repr__(self):
        return f"<EstimateLabor {self.id}>"
        
    @property
    def total_cost(self):
        """Calculate the total cost for this labor."""
        return self.cost_price * self.hours
        
    @property
    def total_price(self):
        """Calculate the total selling price for this labor."""
        return self.selling_price * self.hours
        
    @property
    def profit(self):
        """Calculate the profit for this labor."""
        return self.total_price - self.total_cost
        
    @property
    def profit_margin(self):
        """Calculate the profit margin as a percentage."""
        if self.total_price > 0:
            return (self.profit / self.total_price) * 100
        return 0