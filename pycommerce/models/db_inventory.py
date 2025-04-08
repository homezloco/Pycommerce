"""
Inventory database model for PyCommerce.

This module defines the SQLAlchemy InventoryRecord model for tracking product inventory.
"""

import uuid
import logging
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from pycommerce.core.db import Base
# Import from central registry to avoid circular imports
from pycommerce.models.db_registry import InventoryRecord

logger = logging.getLogger(__name__)