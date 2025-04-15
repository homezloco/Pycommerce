"""
Database configuration for PyCommerce.

This module configures the SQLAlchemy engine and session for the application.
"""

from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

import os
import logging
import time
import backoff

logger = logging.getLogger(__name__)

# Get database URL from environment variable or use SQLite as fallback
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///pycommerce.db")

# Configure engine with more resilient connection pooling settings
engine_args = {
    "pool_recycle": 300,  # Recycle connections after 5 minutes
    "pool_timeout": 30,   # Wait up to 30 seconds for a connection
    "pool_size": 5,       # Keep 5 connections in the pool
    "max_overflow": 10,   # Allow up to 10 additional connections
    "connect_args": {}    # Connection-specific args
}

# Additional connect_args for PostgreSQL
if DATABASE_URL.startswith("postgresql"):
    engine_args["connect_args"].update({
        "connect_timeout": 10,  # 10 second connection timeout
        "keepalives": 1,        # Enable keepalives
        "keepalives_idle": 30,  # Start keepalives after 30 seconds
        "keepalives_interval": 10, # 10 seconds between keepalives
        "keepalives_count": 5   # 5 failures before connection is considered dead
    })

# Create SQLAlchemy engine with retries for transient errors
@backoff.on_exception(backoff.expo, 
                     (Exception),
                     max_tries=5,
                     max_time=30)
def create_db_engine():
    logger.info(f"Creating database engine with URL: {DATABASE_URL}")
    return create_engine(DATABASE_URL, **engine_args)

try:
    engine = create_db_engine()
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Error creating database engine: {str(e)}")
    # Fallback to SQLite if PostgreSQL connection fails
    if DATABASE_URL.startswith("postgresql"):
        logger.warning("Falling back to SQLite database")
        DATABASE_URL = "sqlite:///pycommerce.db"
        engine_args = {"pool_recycle": 300}
        engine = create_engine(DATABASE_URL, **engine_args)
    else:
        raise

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()

# Add connection event listeners for better debugging
@event.listens_for(engine, "connect")
def connect(dbapi_connection, connection_record):
    logger.debug("Database connection established")

@event.listens_for(engine, "checkout")
def checkout(dbapi_connection, connection_record, connection_proxy):
    logger.debug("Database connection checkout")

@event.listens_for(engine, "checkin")
def checkin(dbapi_connection, connection_record):
    logger.debug("Database connection checkin")

# Create a base class for declarative models
convention = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s'
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)

# Import models to ensure they're registered before connections are made
from pycommerce.models.tenant import Tenant
from pycommerce.models.product import Product
from pycommerce.models.user import User
from pycommerce.models.cart import Cart, CartItem
from pycommerce.models.order import Order, OrderItem
from pycommerce.models.db_registry import (
        Tenant, 
        Product, 
        InventoryRecord,
        PluginConfig,
        MediaFile
    )
from pycommerce.models.inventory import InventoryTransaction


# Initialize database
def init_db():
    """Initialize database by creating all tables."""
    # Import all models to ensure they are registered with SQLAlchemy

    logger.info(f"Initializing database with URL: {DATABASE_URL}")
    retry_attempts = 3

    for attempt in range(retry_attempts):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
            return
        except Exception as e:
            if attempt < retry_attempts - 1:
                logger.warning(f"Database initialization failed (attempt {attempt+1}/{retry_attempts}): {str(e)}")
                time.sleep(2 * (attempt + 1))  # Exponential backoff
            else:
                logger.error(f"Database initialization failed after {retry_attempts} attempts: {str(e)}")
                raise

# Get database session
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database session context manager
def db_session():
    """Database session context manager."""
    session = SessionLocal()
    try:
        return session
    except Exception as e:
        session.rollback()
        raise e

def get_session():
    """
    Get a session context manager.

    This function returns a context manager for database sessions,
    ensuring they are properly closed after use.

    Example:
        with get_session() as session:
            result = session.query(Model).all()
    """
    return DBSessionContext()


class DBSessionContext:
    """Context manager for database sessions."""

    def __init__(self):
        self.session = SessionLocal()

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
        self.session.close()