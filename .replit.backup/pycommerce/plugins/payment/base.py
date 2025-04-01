"""
Base payment plugin for PyCommerce SDK.

This module defines the base PaymentPlugin class that all payment
plugins must inherit from.
"""

import logging
from abc import abstractmethod
from typing import Dict, Any, Optional
from uuid import UUID

from pycommerce.core.plugin import Plugin
from pycommerce.core.exceptions import PaymentError

logger = logging.getLogger("pycommerce.plugins.payment")


class PaymentPlugin(Plugin):
    """
    Base class for payment plugins.
    
    All payment plugins must inherit from this class and implement
    the required methods.
    """
    
    @property
    def description(self) -> str:
        return "Payment processing plugin"
    
    @abstractmethod
    async def process_payment(self, order_id: UUID, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a payment for an order.
        
        Args:
            order_id: The ID of the order to process payment for
            payment_data: Dictionary containing payment information
            
        Returns:
            Dictionary containing payment result information
            
        Raises:
            PaymentError: If payment processing fails
        """
        pass
    
    @abstractmethod
    async def refund_payment(self, payment_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """
        Refund a payment.
        
        Args:
            payment_id: The ID of the payment to refund
            amount: Optional amount to refund (if not provided, refunds the full amount)
            
        Returns:
            Dictionary containing refund result information
            
        Raises:
            PaymentError: If refund processing fails
        """
        pass
    
    @abstractmethod
    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Get the status of a payment.
        
        Args:
            payment_id: The ID of the payment to check
            
        Returns:
            Dictionary containing payment status information
            
        Raises:
            PaymentError: If status retrieval fails
        """
        pass
