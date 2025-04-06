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
from pycommerce.core.exceptions import (
    PaymentError, PaymentConfigError, PaymentAuthenticationError,
    PaymentProcessingError, PaymentValidationError, PaymentRefundError
)

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
            try:
                stripe.api_key = self.api_key
                self.enabled = STRIPE_ENABLED
            except Exception as e:
                logger.error(f"Error initializing Stripe API: {str(e)}")
                self.enabled = False
                raise PaymentConfigError(f"Failed to initialize Stripe API: {str(e)}")

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
            PaymentValidationError: If payment data is invalid or missing required fields
            PaymentConfigError: If plugin is not properly configured
            PaymentProcessingError: If payment processing fails
            PaymentAuthenticationError: If authentication with Stripe fails
            PaymentError: For other general payment errors
        """
        # First verify plugin is enabled
        if not self.enabled:
            raise PaymentConfigError("Stripe payment plugin is not enabled or properly configured")

        # Ensure we have an API key
        if not self.api_key:
            raise PaymentConfigError("Stripe API key is not configured")

        try:
            # Validate required fields
            missing_fields = []
            required_fields = ["amount", "currency", "payment_method"]
            for field in required_fields:
                if field not in payment_data:
                    missing_fields.append(field)
            
            if missing_fields:
                missing_fields_str = ", ".join(missing_fields)
                raise PaymentValidationError(
                    f"Missing required payment fields: {missing_fields_str}",
                    invalid_fields=missing_fields
                )

            # Validate amount and currency
            try:
                # Convert amount to cents (Stripe requires integer in smallest currency unit)
                amount_cents = int(float(payment_data["amount"]) * 100)
                if amount_cents <= 0:
                    raise PaymentValidationError(
                        "Payment amount must be greater than zero",
                        invalid_fields=["amount"]
                    )
            except (ValueError, TypeError):
                raise PaymentValidationError(
                    "Invalid payment amount format",
                    invalid_fields=["amount"]
                )

            # Validate currency (must be 3-letter code)
            currency = payment_data["currency"].upper()
            if not currency or len(currency) != 3:
                raise PaymentValidationError(
                    "Invalid currency code format. Must be a 3-letter code (e.g., USD)",
                    invalid_fields=["currency"]
                )

            # Create payment intent
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/x-www-form-urlencoded"
            }

            request_data = {
                "amount": str(amount_cents),
                "currency": currency.lower(),
                "payment_method": payment_data["payment_method"],
                "metadata[order_id]": str(order_id),
                "confirm": "true",
                "return_url": payment_data.get("return_url", "")
            }

            # Add optional fields if provided
            if "description" in payment_data:
                request_data["description"] = payment_data["description"]

            # Process payment with Stripe API
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.api_base_url}/payment_intents",
                        headers=headers,
                        data=request_data
                    )
            except httpx.RequestError as e:
                logger.error(f"HTTP request error during payment processing: {str(e)}")
                raise PaymentProcessingError(f"Failed to connect to Stripe API: {str(e)}")

            # Handle HTTP error responses
            if response.status_code == 401:
                logger.error("Stripe authentication failed - invalid API key")
                raise PaymentAuthenticationError("Invalid Stripe API credentials")
                
            elif response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_type = error_data.get("error", {}).get("type", "")
                    error_code = error_data.get("error", {}).get("code", "")
                    error_message = error_data.get("error", {}).get("message", "Unknown error")
                    
                    logger.error(f"Stripe payment error: {error_type}/{error_code} - {error_message}")
                    
                    # Card declined errors
                    if error_type == "card_error" or error_code in ["card_declined", "expired_card", "incorrect_cvc"]:
                        decline_reason = error_data.get("error", {}).get("decline_code", error_code)
                        raise PaymentProcessingError(
                            f"Card payment failed: {error_message}",
                            decline_reason=decline_reason
                        )
                    # Configuration errors
                    elif error_type in ["invalid_request_error", "api_connection_error"]:
                        raise PaymentConfigError(f"Stripe configuration error: {error_message}")
                    # Authentication errors
                    elif error_type == "authentication_error":
                        raise PaymentAuthenticationError(f"Stripe authentication failed: {error_message}")
                    # Other errors
                    else:
                        raise PaymentProcessingError(f"Payment failed: {error_message}")
                except ValueError:
                    raise PaymentProcessingError(f"Payment failed with status {response.status_code}")

            # Parse the successful payment response
            try:
                payment_intent = response.json()
            except ValueError:
                raise PaymentProcessingError("Invalid response from Stripe API")

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

        except (PaymentValidationError, PaymentConfigError, 
                PaymentProcessingError, PaymentAuthenticationError):
            # Re-raise specific payment errors unchanged
            raise

        except Exception as e:
            logger.error(f"Unexpected error during payment processing: {str(e)}")
            raise PaymentProcessingError(f"Payment failed due to unexpected error: {str(e)}")

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
            PaymentConfigError: If plugin is not properly configured
            PaymentRefundError: If refund processing fails
            PaymentAuthenticationError: If authentication with Stripe fails
            PaymentError: For other general payment errors
        """
        # First verify plugin is enabled
        if not self.enabled:
            raise PaymentConfigError("Stripe payment plugin is not enabled or properly configured")

        # Ensure we have an API key
        if not self.api_key:
            raise PaymentConfigError("Stripe API key is not configured")

        # Validate payment ID
        if not payment_id:
            raise PaymentValidationError("Payment ID is required for refund")

        try:
            # Validate amount if provided
            if amount is not None:
                try:
                    if float(amount) <= 0:
                        raise PaymentValidationError(
                            "Refund amount must be greater than zero",
                            invalid_fields=["amount"]
                        )
                except (ValueError, TypeError):
                    raise PaymentValidationError(
                        "Invalid refund amount format",
                        invalid_fields=["amount"]
                    )

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
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.api_base_url}/refunds",
                        headers=headers,
                        data=request_data
                    )
            except httpx.RequestError as e:
                logger.error(f"HTTP request error during refund processing: {str(e)}")
                raise PaymentRefundError(f"Failed to connect to Stripe API for refund: {str(e)}")

            # Handle HTTP error responses
            if response.status_code == 401:
                logger.error("Stripe authentication failed during refund - invalid API key")
                raise PaymentAuthenticationError("Invalid Stripe API credentials")
                
            elif response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_type = error_data.get("error", {}).get("type", "")
                    error_code = error_data.get("error", {}).get("code", "")
                    error_message = error_data.get("error", {}).get("message", "Unknown error")
                    
                    logger.error(f"Stripe refund error: {error_type}/{error_code} - {error_message}")
                    
                    # Configuration errors
                    if error_type in ["invalid_request_error", "api_connection_error"]:
                        if "amount" in error_message.lower():
                            raise PaymentRefundError(f"Refund amount error: {error_message}")
                        else:
                            raise PaymentConfigError(f"Stripe configuration error: {error_message}")
                    # Authentication errors
                    elif error_type == "authentication_error":
                        raise PaymentAuthenticationError(f"Stripe authentication failed: {error_message}")
                    # Payment Intent not found
                    elif error_code == "resource_missing":
                        raise PaymentRefundError(f"Payment not found: {error_message}")
                    # Other errors
                    else:
                        raise PaymentRefundError(f"Refund failed: {error_message}")
                except ValueError:
                    raise PaymentRefundError(f"Refund failed with status {response.status_code}")

            # Parse the successful refund response
            try:
                refund_data = response.json()
            except ValueError:
                raise PaymentRefundError("Invalid response from Stripe API")

            # Convert amount from cents back to dollars
            refund_amount = float(refund_data.get("amount", 0)) / 100

            return {
                "refund_id": refund_data.get("id"),
                "status": refund_data.get("status"),
                "amount": refund_amount
            }

        except (PaymentValidationError, PaymentConfigError, 
                PaymentRefundError, PaymentAuthenticationError):
            # Re-raise specific payment errors unchanged
            raise

        except Exception as e:
            logger.error(f"Unexpected error during refund processing: {str(e)}")
            raise PaymentRefundError(f"Refund failed due to unexpected error: {str(e)}")

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
            PaymentConfigError: If plugin is not properly configured
            PaymentValidationError: If payment ID is invalid
            PaymentAuthenticationError: If authentication with Stripe fails
            PaymentError: For other general payment errors
        """
        # First verify plugin is enabled
        if not self.enabled:
            raise PaymentConfigError("Stripe payment plugin is not enabled or properly configured")

        # Ensure we have an API key
        if not self.api_key:
            raise PaymentConfigError("Stripe API key is not configured")

        # Validate payment ID
        if not payment_id:
            raise PaymentValidationError("Payment ID is required to check status")

        try:
            # Get payment intent details
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/x-www-form-urlencoded"
            }

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.api_base_url}/payment_intents/{payment_id}",
                        headers=headers
                    )
            except httpx.RequestError as e:
                logger.error(f"HTTP request error during payment status check: {str(e)}")
                raise PaymentError(f"Failed to connect to Stripe API for status check: {str(e)}")

            # Handle HTTP error responses
            if response.status_code == 401:
                logger.error("Stripe authentication failed during status check - invalid API key")
                raise PaymentAuthenticationError("Invalid Stripe API credentials")
                
            elif response.status_code == 404:
                logger.error(f"Payment not found: {payment_id}")
                raise PaymentValidationError(f"Payment not found with ID: {payment_id}", 
                                            invalid_fields=["payment_id"])
                
            elif response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_type = error_data.get("error", {}).get("type", "")
                    error_message = error_data.get("error", {}).get("message", "Unknown error")
                    
                    logger.error(f"Stripe payment status error: {error_type} - {error_message}")
                    
                    # Authentication errors
                    if error_type == "authentication_error":
                        raise PaymentAuthenticationError(f"Stripe authentication failed: {error_message}")
                    # Resource not found
                    elif error_type == "invalid_request_error" and "no such payment_intent" in error_message.lower():
                        raise PaymentValidationError(f"Payment not found: {error_message}", 
                                                   invalid_fields=["payment_id"])
                    # Other errors
                    else:
                        raise PaymentError(f"Status check failed: {error_message}")
                except ValueError:
                    raise PaymentError(f"Status check failed with status {response.status_code}")

            # Parse the successful payment intent response
            try:
                payment_intent = response.json()
            except ValueError:
                raise PaymentError("Invalid response from Stripe API")

            # Convert amount from cents to dollars
            amount = float(payment_intent.get("amount", 0)) / 100

            return {
                "payment_id": payment_intent.get("id"),
                "status": payment_intent.get("status"),
                "amount": amount,
                "currency": payment_intent.get("currency", "").upper()
            }

        except (PaymentValidationError, PaymentConfigError, PaymentAuthenticationError):
            # Re-raise specific payment errors unchanged
            raise

        except Exception as e:
            logger.error(f"Unexpected error during payment status check: {str(e)}")
            raise PaymentError(f"Status check failed due to unexpected error: {str(e)}")