"""
Models package for PyCommerce.

This package contains all the SQLAlchemy models used by PyCommerce.
"""

# Import models here to register them with SQLAlchemy
from .order import Order, OrderStatus
from .order_note import OrderNote
from .order_item import OrderItem
from .shipment import Shipment, ShipmentItem, ShipmentStatus
from .return_request import ReturnRequest, ReturnItem, ReturnStatus, ReturnReason

# Import estimate models
try:
    from .estimate import Estimate, EstimateMaterial, EstimateLabor
except ImportError:
    # The estimate module might not exist during initial import
    pass