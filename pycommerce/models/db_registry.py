"""
Database registry for PyCommerce.

This module centralizes all SQLAlchemy model imports to avoid circular dependencies
and model declaration conflicts.
"""

import logging
from sqlalchemy import MetaData, Column, String, DateTime, ForeignKey, Integer, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from pycommerce.core.db import Base
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

# Create a unified metadata instance
metadata = MetaData()

# Define all models here to avoid circular imports
class Tenant(Base):
    """SQLAlchemy Tenant model."""
    __tablename__ = "tenants"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    domain = Column(String(255), unique=True, nullable=True)
    active = Column(Boolean, default=True)
    settings = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - forward declarations
    products = relationship("Product", back_populates="tenant", cascade="all, delete-orphan")
    plugin_configs = relationship("PluginConfig", back_populates="tenant", cascade="all, delete-orphan")
    media_files = relationship("MediaFile", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tenant {self.name}>"
        
class Product(Base):
    """SQLAlchemy Product model."""
    __tablename__ = "products"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    price = Column(Integer, nullable=False)  # Price in cents
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
        
class InventoryRecord(Base):
    """SQLAlchemy InventoryRecord model for tracking inventory changes."""
    __tablename__ = "inventory_records"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    quantity_change = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="inventory_records")
    
    def __repr__(self):
        return f"<InventoryRecord {self.id}: {self.quantity_change}>"
        
class PluginConfig(Base):
    """SQLAlchemy PluginConfig model for storing plugin configuration data."""
    __tablename__ = "plugin_configs"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    plugin_type = Column(String(50), nullable=False)  # 'payment', 'shipping', etc.
    plugin_id = Column(String(100), nullable=False)   # 'stripe', 'paypal', 'standard', etc.
    config = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with Tenant
    tenant = relationship("Tenant", back_populates="plugin_configs")
    
    def __repr__(self):
        return f"<PluginConfig {self.plugin_type}:{self.plugin_id} for tenant {self.tenant_id}>"

class MediaFile(Base):
    """SQLAlchemy MediaFile model for storing file information."""
    __tablename__ = "media_files"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=True)  # mime type
    file_size = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Media sharing and additional fields (added for the sharing feature)
    meta_data = Column(JSON, nullable=True)  # For storing sharing_level and other metadata
    is_public = Column(Boolean, default=False)  # True for community-shared media
    is_ai_generated = Column(Boolean, default=False)  # True for AI-generated media
    url = Column(String(500), nullable=True)  # URL for accessing the media
    thumbnail_url = Column(String(500), nullable=True)  # URL for thumbnail
    alt_text = Column(Text, nullable=True)  # Alternative text for accessibility
    
    # Relationship with Tenant
    tenant = relationship("Tenant", back_populates="media_files")
    
    def __repr__(self):
        return f"<MediaFile {self.filename}>"
        
    @property
    def name(self):
        """Alias for filename for compatibility with existing code."""
        return self.filename
    
    @property
    def file_name(self):
        """Alias for filename for compatibility with existing code."""
        return self.filename