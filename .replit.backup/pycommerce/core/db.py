"""
Database connectivity module for PyCommerce SDK.

This module provides database connection and ORM functionality
for storing PyCommerce data in persistent storage.
"""

import os
import logging
from sqlalchemy import create_engine, Column, String, Boolean, Text, Integer, Float, ForeignKey, DateTime, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

# Configure logging
logger = logging.getLogger("pycommerce.db")

# Get database URL from environment or use SQLite in-memory
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///:memory:")

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionLocal)

# Create base class for models
metadata = MetaData(schema="pycommerce")
Base = declarative_base(metadata=metadata)


class Tenant(Base):
    """SQLAlchemy model for a Tenant."""
    
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True)
    domain = Column(String(255), nullable=True, unique=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    products = relationship("Product", back_populates="tenant", cascade="all, delete-orphan")
    carts = relationship("Cart", back_populates="tenant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="tenant", cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")


class Product(Base):
    """SQLAlchemy model for a Product."""
    
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True)
    sku = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    categories = Column(String(255), nullable=True)  # Comma-separated list of categories
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product", cascade="all, delete-orphan")
    
    # Add a unique constraint for (tenant_id, sku) to ensure SKUs are unique within a tenant
    __table_args__ = (
        {"schema": "pycommerce"}
    )


class User(Base):
    """SQLAlchemy model for a User."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True)
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    carts = relationship("Cart", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    
    # Add a unique constraint for (tenant_id, email) to ensure emails are unique within a tenant
    __table_args__ = (
        {"schema": "pycommerce"}
    )


class Cart(Base):
    """SQLAlchemy model for a Cart."""
    
    __tablename__ = "carts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="carts")
    user = relationship("User", back_populates="carts")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")
    
    __table_args__ = (
        {"schema": "pycommerce"}
    )


class CartItem(Base):
    """SQLAlchemy model for a CartItem."""
    
    __tablename__ = "cart_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cart_id = Column(UUID(as_uuid=True), ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, default=1)
    added_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product", back_populates="cart_items")
    
    __table_args__ = (
        {"schema": "pycommerce"}
    )


class Order(Base):
    """SQLAlchemy model for an Order."""
    
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    total = Column(Float, nullable=False)
    shipping_address = Column(Text, nullable=True)
    billing_address = Column(Text, nullable=True)
    payment_method = Column(String(50), nullable=True)
    payment_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="orders")
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    __table_args__ = (
        {"schema": "pycommerce"}
    )


class OrderItem(Base):
    """SQLAlchemy model for an OrderItem."""
    
    __tablename__ = "order_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    quantity = Column(Integer, default=1)
    price = Column(Float, nullable=False)
    product_name = Column(String(255), nullable=False)
    product_sku = Column(String(255), nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    
    __table_args__ = (
        {"schema": "pycommerce"}
    )


def init_db():
    """Initialize the database by creating all tables."""
    # Create the pycommerce schema if it doesn't exist
    try:
        # Use text() for SQLAlchemy 2.0 compatibility
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS pycommerce"))
            conn.commit()
            logger.info("PyCommerce schema created or already exists")
    except Exception as e:
        logger.error(f"Error creating schema: {str(e)}")
        return False
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
        return True
    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        return False


def get_db():
    """
    Get a database session.
    
    This function should be used as a dependency in FastAPI route functions.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()