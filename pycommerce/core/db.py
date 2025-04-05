"""
Database configuration for PyCommerce.

This module configures the SQLAlchemy engine and session for the application.
"""

import os
from typing import Any, Optional
import logging
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

logger = logging.getLogger(__name__)

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

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/pycommerce")

# Initialize SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true",
    pool_pre_ping=True
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create thread-local session
db_session = scoped_session(SessionLocal)


def get_db() -> scoped_session:
    """Get a database session."""
    return db_session


def init_db() -> None:
    """Initialize the database by creating all tables."""
    try:
        logger.info("Initializing database...")

        # Import all models to ensure they are registered with Base
        from pycommerce import models

        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def close_db() -> None:
    """Close the database session."""
    db_session.remove()


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