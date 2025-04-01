"""
Stripe payment plugin for PyCommerce SDK.

This module implements a payment plugin for processing payments
using the Stripe payment gateway.
"""

import logging
import os
from typing import Dict, Any, Optional
from uuid import UUID
import httpx
from fastapi import APIRouter, Depends, HTTPException

from pycommerce.plugins.payment.base import PaymentPlugin
from pycommerce.core.exceptions import PaymentError

logger = logging.getLogger("pycommerce.plugins.payment.stripe")


class StripePaymentPlugin(PaymentPlugin):
    """
    Payment plugin for processing payments using Stripe.
    """
    
    @property
    def name(self) -> str:
        return "stripe_payment"
    
    @property
    def version(self) -> str:
        return "0.1.0"
    
    @property
    def description(self) -> str:
        return "Process payments using Stripe payment gateway"
    
    def __init__(self):
        """Initialize the Stripe payment plugin."""
        self.api_key = os.getenv("STRIPE_API_KEY", "")
        if not self.api_key:
            logger.warning("STRIPE_API_KEY environment variable not set")
    
    def initialize(self) -> None:
        """Initialize the plugin."""
        logger.info("Initializing Stripe payment plugin")
    
    def get_router(self) -> APIRouter:
        """Create and return a FastAPI router for Stripe-specific endpoints."""
        router = APIRouter()
        
        @router.post("/webhook", tags=["stripe"])
        async def stripe_webhook(payload: Dict[str, Any]):
            """Handle Stripe webhook events."""
            try:
                event_type = payload.get("type")
                logger.info(f"Received Stripe webhook event: {event_type}")
                
                # Process different event types
                if event_type == "payment_intent.succeeded":
                    # Handle successful payment
                    return {"status": "success"}
                elif event_type == "payment_intent.payment_failed":
                    # Handle failed payment
                    return {"status": "failed"}
                
                return {"status": "ignored"}
            except Exception as e:
                logger.error(f"Error processing Stripe webhook: {str(e)}")
                raise HTTPException(status_code=500, detail="Error processing webhook")
        
        return router
    
    async def process_payment(self, order_id: UUID, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a payment using Stripe.
        
        Args:
            order_id: The ID of the order being paid for
            payment_data: Dictionary containing payment information
                - amount: Amount to charge (in the smallest currency unit, e.g., cents)
                - currency: Three-letter currency code (e.g., 'usd')
                - payment_method: Stripe payment method ID or token
                - customer_email: Customer's email address
                
        Returns:
            Dictionary containing payment result information
                - payment_id: Stripe payment ID
                - status: Payment status
                - amount: Amount charged
                - currency: Currency used
                
        Raises:
            PaymentError: If payment processing fails
        """
        try:
            if not self.api_key:
                raise PaymentError("Stripe API key not configured")
            
            # Validate required fields
            required_fields = ["amount", "currency", "payment_method"]
            for field in required_fields:
                if field not in payment_data:
                    raise PaymentError(f"Missing required payment field: {field}")
            
            # Create payment intent
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.stripe.com/v1/payment_intents",
                    auth=(self.api_key, ""),
                    data={
                        "amount": payment_data["amount"],
                        "currency": payment_data["currency"],
                        "payment_method": payment_data["payment_method"],
                        "confirm": True,
                        "return_url": f"https://example.com/orders/{order_id}/confirmation",
                        "metadata": {"order_id": str(order_id)}
                    }
                )
            
            if response.status_code >= 400:
                error_data = response.json()
                logger.error(f"Stripe payment error: {error_data}")
                raise PaymentError(f"Payment failed: {error_data.get('error', {}).get('message', 'Unknown error')}")
            
            payment_data = response.json()
            
            return {
                "payment_id": payment_data["id"],
                "status": payment_data["status"],
                "amount": payment_data["amount"],
                "currency": payment_data["currency"]
            }
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during payment processing: {str(e)}")
            raise PaymentError(f"Payment failed due to network error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error during payment processing: {str(e)}")
            raise PaymentError(f"Payment failed due to unexpected error: {str(e)}")
    
    async def refund_payment(self, payment_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """
        Refund a payment processed by Stripe.
        
        Args:
            payment_id: The ID of the payment to refund
            amount: Optional amount to refund (if not provided, refunds the full amount)
            
        Returns:
            Dictionary containing refund result information
                - refund_id: Stripe refund ID
                - status: Refund status
                - amount: Amount refunded
                
        Raises:
            PaymentError: If refund processing fails
        """
        try:
            if not self.api_key:
                raise PaymentError("Stripe API key not configured")
            
            # Prepare refund data
            refund_data = {"payment_intent": payment_id}
            if amount is not None:
                refund_data["amount"] = int(amount)
            
            # Process refund
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.stripe.com/v1/refunds",
                    auth=(self.api_key, ""),
                    data=refund_data
                )
            
            if response.status_code >= 400:
                error_data = response.json()
                logger.error(f"Stripe refund error: {error_data}")
                raise PaymentError(f"Refund failed: {error_data.get('error', {}).get('message', 'Unknown error')}")
            
            refund_data = response.json()
            
            return {
                "refund_id": refund_data["id"],
                "status": refund_data["status"],
                "amount": refund_data["amount"]
            }
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during refund processing: {str(e)}")
            raise PaymentError(f"Refund failed due to network error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error during refund processing: {str(e)}")
            raise PaymentError(f"Refund failed due to unexpected error: {str(e)}")
    
    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Get the status of a Stripe payment.
        
        Args:
            payment_id: The ID of the payment to check
            
        Returns:
            Dictionary containing payment status information
                - payment_id: Stripe payment ID
                - status: Payment status
                - amount: Amount charged
                - currency: Currency used
                
        Raises:
            PaymentError: If status retrieval fails
        """
        try:
            if not self.api_key:
                raise PaymentError("Stripe API key not configured")
            
            # Retrieve payment intent
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.stripe.com/v1/payment_intents/{payment_id}",
                    auth=(self.api_key, "")
                )
            
            if response.status_code >= 400:
                error_data = response.json()
                logger.error(f"Stripe payment status error: {error_data}")
                raise PaymentError(f"Status check failed: {error_data.get('error', {}).get('message', 'Unknown error')}")
            
            payment_data = response.json()
            
            return {
                "payment_id": payment_data["id"],
                "status": payment_data["status"],
                "amount": payment_data["amount"],
                "currency": payment_data["currency"]
            }
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during payment status check: {str(e)}")
            raise PaymentError(f"Status check failed due to network error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error during payment status check: {str(e)}")
            raise PaymentError(f"Status check failed due to unexpected error: {str(e)}")
