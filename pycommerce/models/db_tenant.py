"""
Tenant database model for PyCommerce.

This module defines the SQLAlchemy Tenant model for database interactions.
"""

import uuid
import logging
from datetime import datetime

from sqlalchemy import Column, String, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship

from pycommerce.core.db import Base

logger = logging.getLogger(__name__)


# Import from central registry to avoid circular imports
from pycommerce.models.db_registry import Tenant