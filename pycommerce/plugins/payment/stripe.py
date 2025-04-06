"""
Stripe payment plugin for PyCommerce SDK.

This module implements a payment plugin for processing payments
using the Stripe payment gateway.
"""

import logging
import stripe
from typing import Dict, Any, Optional
from uuid import UUID
import json
import httpx

from fastapi import APIRouter, HTTPException
from pycommerce.plugins.payment.base import PaymentPlugin, PaymentMethod, PaymentStatus
from pycommerce.plugins.payment.config import STRIPE_API_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_ENABLED, STRIPE_PUBLIC_KEY

logger = logging.getLogger(__name__)


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
        self.api_key = STRIPE_API_KEY
        if not self.api_key:
            logger.warning("Stripe API key not properly configured")
            self.enabled = False
        else:
            stripe.api_key = self.api_key
            self.enabled = STRIPE_ENABLED

        self.webhook_secret = STRIPE_WEBHOOK_SECRET
        self.api_base_url = "https://api.stripe.com/v1"
        logger.info("Initializing Stripe payment plugin")

    def initialize(self) -> None:
        """Initialize the plugin."""
        logger.info("Initializing Stripe payment plugin")
        
    def get_client_key(self) -> str:
        """
        Get the public API key for Stripe.
        
        Returns:
            str: The public API key for use in frontend code
        """
        return STRIPE_PUBLIC_KEY

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
                - amount: Amount to charge
                - currency: Three-letter currency code (e.g., 'USD')
                - payment_method: Stripe payment method ID or payment method type

        Returns:
            Dictionary containing payment result information
                - payment_id: Stripe payment intent ID
                - status: Payment status
                - client_secret: Client secret for frontend confirmation (if needed)

        Raises:
            PaymentError: If payment processing fails
        """
        try:
            # Validate required fields
            required_fields = ["amount", "currency", "payment_method"]
            for field in required_fields:
                if field not in payment_data:
                    raise PaymentError(f"Missing required payment field: {field}")

            # Convert amount to cents (Stripe requires integer in smallest currency unit)
            amount_cents = int(float(payment_data["amount"]) * 100)

            # Create payment intent
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/x-www-form-urlencoded"
            }

            request_data = {
                "amount": str(amount_cents),
                "currency": payment_data["currency"].lower(),
                "payment_method": payment_data["payment_method"],
                "metadata[order_id]": str(order_id),
                "confirm": "true",
                "return_url": payment_data.get("return_url", "")
            }

            # Add optional fields if provided
            if "description" in payment_data:
                request_data["description"] = payment_data["description"]

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/payment_intents",
                    headers=headers,
                    data=request_data
                )

            if response.status_code >= 400:
                error_data = response.json()
                logger.error(f"Stripe payment error: {error_data}")
                raise PaymentError(f"Payment failed: {json.dumps(error_data)}")

            payment_intent = response.json()

            status = payment_intent.get("status", "unknown")
            approval_url = None

            # If additional authentication is required, provide the URL
            if status == "requires_action" and payment_intent.get("next_action"):
                next_action = payment_intent["next_action"]
                if next_action.get("type") == "redirect_to_url":
                    approval_url = next_action.get("redirect_to_url", {}).get("url")

            return {
                "payment_id": payment_intent["id"],
                "status": status,
                "client_secret": payment_intent.get("client_secret"),
                "approval_url": approval_url
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
            payment_id: The ID of the payment intent to refund
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
            # Prepare refund data
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/x-www-form-urlencoded"
            }

            request_data = {
                "payment_intent": payment_id
            }

            # Add amount if specified
            if amount is not None:
                # Convert to cents
                amount_cents = int(float(amount) * 100)
                request_data["amount"] = str(amount_cents)

            # Process refund
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/refunds",
                    headers=headers,
                    data=request_data
                )

            if response.status_code >= 400:
                error_data = response.json()
                logger.error(f"Stripe refund error: {error_data}")
                raise PaymentError(f"Refund failed: {json.dumps(error_data)}")

            refund_data = response.json()

            # Convert amount from cents back to dollars
            refund_amount = float(refund_data.get("amount", 0)) / 100

            return {
                "refund_id": refund_data.get("id"),
                "status": refund_data.get("status"),
                "amount": refund_amount
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
            payment_id: The ID of the payment intent to check

        Returns:
            Dictionary containing payment status information
                - payment_id: Stripe payment intent ID
                - status: Payment status
                - amount: Amount charged (in dollars)
                - currency: Currency used

        Raises:
            PaymentError: If status retrieval fails
        """
        try:
            # Get payment intent details
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/x-www-form-urlencoded"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/payment_intents/{payment_id}",
                    headers=headers
                )

            if response.status_code >= 400:
                error_data = response.json()
                logger.error(f"Stripe payment status error: {error_data}")
                raise PaymentError(f"Status check failed: {json.dumps(error_data)}")

            payment_intent = response.json()

            # Convert amount from cents to dollars
            amount = float(payment_intent.get("amount", 0)) / 100

            return {
                "payment_id": payment_intent.get("id"),
                "status": payment_intent.get("status"),
                "amount": amount,
                "currency": payment_intent.get("currency", "").upper()
            }

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during payment status check: {str(e)}")
            raise PaymentError(f"Status check failed due to network error: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error during payment status check: {str(e)}")
            raise PaymentError(f"Status check failed due to unexpected error: {str(e)}")