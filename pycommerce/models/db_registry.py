"""
Database registry for PyCommerce.

This module centralizes all SQLAlchemy model imports to avoid circular dependencies
and model declaration conflicts.
"""

import logging
from sqlalchemy import MetaData

logger = logging.getLogger(__name__)

# Create a unified metadata instance
metadata = MetaData()

# Import all models here to ensure they're registered
# These will be imported by other modules when needed
from pycommerce.models.db_tenant import Tenant
from pycommerce.models.db_product import Product