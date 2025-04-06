"""
Database configuration for PyCommerce.

This module defines the SQLAlchemy database connection and base model.
"""

import logging
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Create the SQLAlchemy database object
db = SQLAlchemy(model_class=Base)