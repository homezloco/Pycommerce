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
# Use the registry pattern here - don't redefine the model
# just import it from the central registry
from pycommerce.models.db_registry import InventoryRecord as InventoryRecordBase

logger = logging.getLogger(__name__)

# Extend the base inventory record if needed, but don't redefine the table
# InventoryRecord = InventoryRecordBase