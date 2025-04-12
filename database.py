"""
Database configuration for PyCommerce.

This module defines the SQLAlchemy database connection and base model.
"""

import logging
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Create the SQLAlchemy database object
db = SQLAlchemy(model_class=Base)

# Database URL from environment variable or default
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/pycommerce")

# Create async engine
async_engine = create_async_engine(DATABASE_URL)
async_session_maker = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# Function to get database session for FastAPI
async def get_db():
    """
    Get database session for dependency injection in FastAPI routes.
    Used as a dependency in FastAPI route handlers.
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()