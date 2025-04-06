"""
Models for the Flask app.

This module contains SQLAlchemy models for the Flask app.
"""

import os
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from database import db

class User(db.Model):
    """User model."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    first_name = Column(String(64), nullable=True)
    last_name = Column(String(64), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # orders = relationship("Order", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.username}>"

class Tenant(db.Model):
    """Tenant model for multi-tenant architecture."""
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

class Product(db.Model):
    """Product model."""
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

class Cart(db.Model):
    """Shopping cart model."""
    __tablename__ = "carts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    session_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Cart {self.id}>"

class CartItem(db.Model):
    """Shopping cart item model."""
    __tablename__ = "cart_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cart_id = Column(String(36), ForeignKey("carts.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")
    
    def __repr__(self):
        return f"<CartItem {self.id}>"

class Order(db.Model):
    """Order model."""
    __tablename__ = "orders"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="pending")
    total = Column(Float, default=0.0)
    email = Column(String(120), nullable=False)
    shipping_address = Column(JSON, nullable=True)
    billing_address = Column(JSON, nullable=True)
    payment_info = Column(JSON, nullable=True)
    shipping_method = Column(String(100), nullable=True)
    payment_method = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    notes = relationship("OrderNote", back_populates="order", cascade="all, delete-orphan")
    shipments = relationship("Shipment", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order {self.id}>"

class OrderNote(db.Model):
    """Order note model."""
    __tablename__ = "order_notes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    content = Column(Text, nullable=False)  # Using Text for longer note content
    author = Column(String(100), nullable=True)
    is_customer_visible = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    order = relationship("Order", back_populates="notes")
    
    def __repr__(self):
        return f"<OrderNote {self.id}>"
class OrderItem(db.Model):
    """Order item model."""
    __tablename__ = "order_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(Float, nullable=False)  # Price at the time of order
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    
    def __repr__(self):
        return f"<OrderItem {self.id}>"

class Shipment(db.Model):
    """Shipment model."""
    __tablename__ = "shipments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    status = Column(String(50), default="pending")
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
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    order = relationship("Order", back_populates="shipments")
    items = relationship("ShipmentItem", back_populates="shipment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Shipment {self.id}>"

class ShipmentItem(db.Model):
    """Shipment item model."""
    __tablename__ = "shipment_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    shipment_id = Column(String(36), ForeignKey("shipments.id"), nullable=False)
    order_item_id = Column(String(36), ForeignKey("order_items.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    shipment = relationship("Shipment", back_populates="items")
    order_item = relationship("OrderItem")
    product = relationship("Product")
    
    def __repr__(self):
        return f"<ShipmentItem {self.id}>"

class InventoryRecord(db.Model):
    """Inventory record model."""
    __tablename__ = "inventory_records"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    location = Column(String(100), nullable=True)  # Optional inventory location
    sku = Column(String(100), nullable=True)
    quantity = Column(Integer, default=0)
    available_quantity = Column(Integer, default=0)  # Available for sale (quantity - reserved)
    reserved_quantity = Column(Integer, default=0)   # Reserved for orders
    reorder_point = Column(Integer, default=0)       # When to reorder
    reorder_quantity = Column(Integer, default=0)    # How much to reorder
    last_counted = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    product = relationship("Product", back_populates="inventory_records")
    transactions = relationship("InventoryTransaction", back_populates="inventory_record", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<InventoryRecord {self.id} for product {self.product_id}>"

class InventoryTransaction(db.Model):
    """Inventory transaction model."""
    __tablename__ = "inventory_transactions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inventory_record_id = Column(String(36), ForeignKey("inventory_records.id"), nullable=False)
    transaction_type = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)  # Positive for additions, negative for reductions
    reference_id = Column(String(100), nullable=True)  # Optional reference (order ID, etc.)
    reference_type = Column(String(50), nullable=True)  # Type of reference (order, shipment, etc.)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), nullable=True)  # User who created the transaction
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    inventory_record = relationship("InventoryRecord", back_populates="transactions")
    
    def __repr__(self):
        return f"<InventoryTransaction {self.id} of type {self.transaction_type}>"
