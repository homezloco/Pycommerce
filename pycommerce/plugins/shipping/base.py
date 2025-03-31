"""
Base shipping plugin for PyCommerce SDK.

This module defines the base ShippingPlugin class that all shipping
plugins must inherit from.
"""

import logging
from abc import abstractmethod
from typing import Dict, Any, List
from uuid import UUID

from pycommerce.core.plugin import Plugin
from pycommerce.core.exceptions import ShippingError

logger = logging.getLogger("pycommerce.plugins.shipping")


class ShippingPlugin(Plugin):
    """
    Base class for shipping plugins.
    
    All shipping plugins must inherit from this class and implement
    the required methods.
    """
    
    @property
    def description(self) -> str:
        return "Shipping calculation and processing plugin"
    
    @abstractmethod
    def calculate_rates(self, items: List[Dict[str, Any]], destination: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calculate shipping rates for an order.
        
        Args:
            items: List of items in the order
                Each item should have at least:
                - product_id: Product ID
                - quantity: Quantity
                - weight: Weight in kg (optional)
                - dimensions: Dict with width, height, length in cm (optional)
            destination: Shipping destination
                Should have at least:
                - country: Country code
                - postal_code: Postal/ZIP code
                - state: State/province (optional)
                - city: City (optional)
            
        Returns:
            List of available shipping options, each containing at least:
            - id: Shipping option ID
            - name: Shipping option name
            - description: Shipping option description
            - price: Shipping price
            - estimated_days: Estimated delivery time in days
            
        Raises:
            ShippingError: If rate calculation fails
        """
        pass
    
    @abstractmethod
    def create_shipment(self, order_id: UUID, shipping_option_id: str, shipping_address: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a shipment for an order.
        
        Args:
            order_id: The ID of the order to create shipment for
            shipping_option_id: The ID of the selected shipping option
            shipping_address: The shipping address
            
        Returns:
            Dictionary containing shipment information
                - shipment_id: Shipment ID
                - tracking_number: Tracking number (if available)
                - label_url: URL to shipping label (if available)
                - carrier: Carrier name
                - shipping_method: Shipping method name
            
        Raises:
            ShippingError: If shipment creation fails
        """
        pass
    
    @abstractmethod
    def get_shipment_status(self, shipment_id: str) -> Dict[str, Any]:
        """
        Get the status of a shipment.
        
        Args:
            shipment_id: The ID of the shipment to check
            
        Returns:
            Dictionary containing shipment status information
                - shipment_id: Shipment ID
                - status: Shipment status
                - tracking_number: Tracking number
                - tracking_url: URL to track the shipment
                - updated_at: Timestamp of the last status update
            
        Raises:
            ShippingError: If status retrieval fails
        """
        pass
