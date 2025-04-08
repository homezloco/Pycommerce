"""
Product database model for PyCommerce.

This module defines the SQLAlchemy Product model for database interactions.
"""

import uuid
import logging
from datetime import datetime

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship

from pycommerce.core.db import Base
# Import from central registry to avoid circular imports
from pycommerce.models.db_registry import Product

logger = logging.getLogger(__name__)