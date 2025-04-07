"""
Initialize the database with required tables and initial data.
"""
import os
import sys
import logging
from contextlib import contextmanager
from datetime import datetime
from uuid import uuid4

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import SQLAlchemy models and db
from database import db
from models import Tenant, Product
from app import app

# Create ProductCategory model
class ProductCategory(db.Model):
    """Product category model."""
    __tablename__ = "product_categories"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey("tenants.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    slug = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ProductCategory {self.name}>"

def initialize_database():
    """Initialize the database."""
    logger.info("Initializing database...")
    
    # Create all tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables created successfully")

if __name__ == "__main__":
    initialize_database()