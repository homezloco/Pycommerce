"""
PayPal payment plugin for PyCommerce SDK.

This module implements a payment plugin for processing payments
using the PayPal payment gateway.
"""

import logging
import requests
from .base import PaymentPlugin, PaymentMethod, PaymentStatus
from .config import PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, PAYPAL_ENABLED, PAYPAL_SANDBOX

# Configure logging
logger = logging.getLogger(__name__)

class PayPalPaymentPlugin(PaymentPlugin):
    """
    Payment plugin for processing payments using PayPal.
    """

    @property
    def name(self) -> str:
        return "paypal_payment"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "Process payments using PayPal payment gateway"

    def __init__(self, client_id=None, client_secret=None, sandbox=None):
        """Initialize the PayPal payment plugin."""
        super().__init__(name="paypal", display_name="PayPal")

        self.client_id = client_id or PAYPAL_CLIENT_ID
        self.client_secret = client_secret or PAYPAL_CLIENT_SECRET
        self.sandbox = PAYPAL_SANDBOX if sandbox is None else sandbox

        if not (self.client_id and self.client_secret):
            logger.warning("PayPal client credentials not properly configured")
            self.enabled = False
        else:
            self.enabled = PAYPAL_ENABLED
            self.api_base_url = "https://api-m.sandbox.paypal.com" if self.sandbox else "https://api-m.paypal.com"

        logger.info("Initializing PayPal payment plugin")

    def initialize(self) -> None:
        """Initialize the plugin."""
        logger.info("Initializing PayPal payment plugin")

    async def _get_auth_token(self) -> str:
        """Get an OAuth 2.0 access token from PayPal."""
        try:
            if not self.client_id or not self.client_secret:
                raise PaymentError("PayPal credentials not configured")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/v1/oauth2/token",
                    auth=(self.client_id, self.client_secret),
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={"grant_type": "client_credentials"}
                )

            if response.status_code >= 400:
                error_data = response.json()
                logger.error(f"PayPal authentication error: {error_data}")
                raise PaymentError(f"PayPal authentication failed: {error_data.get('error_description', 'Unknown error')}")

            token_data = response.json()
            return token_data.get("access_token")

        except Exception as e:
            logger.error(f"Error obtaining PayPal auth token: {str(e)}")
            raise PaymentError(f"PayPal authentication failed: {str(e)}")

    def get_router(self) -> APIRouter:
        """Create and return a FastAPI router for PayPal-specific endpoints."""
        router = APIRouter()

        @router.post("/webhook", tags=["paypal"])
        async def paypal_webhook(payload: Dict[str, Any]):
            """Handle PayPal webhook events."""
            try:
                event_type = payload.get("event_type")
                logger.info(f"Received PayPal webhook event: {event_type}")

                # Process different event types
                if event_type == "PAYMENT.CAPTURE.COMPLETED":
                    # Handle successful payment
                    return {"status": "success"}
                elif event_type == "PAYMENT.CAPTURE.DENIED":
                    # Handle denied payment
                    return {"status": "failed"}

                return {"status": "ignored"}
            except Exception as e:
                logger.error(f"Error processing PayPal webhook: {str(e)}")
                raise HTTPException(status_code=500, detail="Error processing webhook")

        return router

    async def process_payment(self, order_id: UUID, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a payment using PayPal.

        Args:
            order_id: The ID of the order being paid for
            payment_data: Dictionary containing payment information
                - amount: Amount to charge
                - currency: Three-letter currency code (e.g., 'USD')
                - return_url: URL to redirect to after successful payment
                - cancel_url: URL to redirect to if payment is cancelled

        Returns:
            Dictionary containing payment result information
                - payment_id: PayPal payment ID
                - status: Payment status
                - approval_url: URL to redirect to for payment approval

        Raises:
            PaymentError: If payment processing fails
        """
        try:
            # Validate required fields
            required_fields = ["amount", "currency", "return_url", "cancel_url"]
            for field in required_fields:
                if field not in payment_data:
                    raise PaymentError(f"Missing required payment field: {field}")

            # Get auth token
            access_token = await self._get_auth_token()

            # Format amount to two decimal places
            amount = f"{float(payment_data['amount']):.2f}"

            # Create payment order
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/v2/checkout/orders",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {access_token}"
                    },
                    json={
                        "intent": "CAPTURE",
                        "purchase_units": [
                            {
                                "reference_id": str(order_id),
                                "amount": {
                                    "currency_code": payment_data["currency"].upper(),
                                    "value": amount
                                }
                            }
                        ],
                        "application_context": {
                            "return_url": payment_data["return_url"],
                            "cancel_url": payment_data["cancel_url"],
                            "brand_name": "PyCommerce Store",
                            "user_action": "PAY_NOW",
                            "shipping_preference": "SET_PROVIDED_ADDRESS"
                        }
                    }
                )

            if response.status_code >= 400:
                error_data = response.json()
                logger.error(f"PayPal order creation error: {error_data}")
                raise PaymentError(f"Payment failed: {json.dumps(error_data)}")

            order_data = response.json()

            # Extract the approval URL
            approval_url = next(
                (link["href"] for link in order_data.get("links", []) 
                 if link["rel"] == "approve"),
                None
            )

            if not approval_url:
                raise PaymentError("No approval URL found in PayPal response")

            return {
                "payment_id": order_data["id"],
                "status": order_data["status"],
                "approval_url": approval_url
            }

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during payment processing: {str(e)}")
            raise PaymentError(f"Payment failed due to network error: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error during payment processing: {str(e)}")
            raise PaymentError(f"Payment failed due to unexpected error: {str(e)}")

    async def capture_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Capture an authorized PayPal payment.

        Args:
            payment_id: The ID of the PayPal order to capture

        Returns:
            Dictionary containing capture result information
                - capture_id: PayPal capture ID
                - status: Capture status
                - amount: Amount captured
                - currency: Currency used

        Raises:
            PaymentError: If capture fails
        """
        try:
            # Get auth token
            access_token = await self._get_auth_token()

            # Capture the payment
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/v2/checkout/orders/{payment_id}/capture",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {access_token}"
                    }
                )

            if response.status_code >= 400:
                error_data = response.json()
                logger.error(f"PayPal capture error: {error_data}")
                raise PaymentError(f"Capture failed: {json.dumps(error_data)}")

            capture_data = response.json()

            # Extract the first capture from the purchase unit
            purchase_unit = capture_data.get("purchase_units", [{}])[0]
            payments = purchase_unit.get("payments", {})
            captures = payments.get("captures", [{}])[0]

            amount_data = captures.get("amount", {})

            return {
                "capture_id": captures.get("id"),
                "status": captures.get("status"),
                "amount": amount_data.get("value"),
                "currency": amount_data.get("currency_code")
            }

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during payment capture: {str(e)}")
            raise PaymentError(f"Capture failed due to network error: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error during payment capture: {str(e)}")
            raise PaymentError(f"Capture failed due to unexpected error: {str(e)}")

    async def refund_payment(self, payment_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """
        Refund a payment processed by PayPal.

        Args:
            payment_id: The ID of the capture to refund
            amount: Optional amount to refund (if not provided, refunds the full amount)

        Returns:
            Dictionary containing refund result information
                - refund_id: PayPal refund ID
                - status: Refund status
                - amount: Amount refunded

        Raises:
            PaymentError: If refund processing fails
        """
        try:
            # Get auth token
            access_token = await self._get_auth_token()

            # Prepare refund data
            refund_data = {}
            if amount is not None:
                # Format amount to two decimal places
                amount_str = f"{float(amount):.2f}"
                # Get currency from captured payment
                async with httpx.AsyncClient() as client:
                    capture_response = await client.get(
                        f"{self.api_base_url}/v2/payments/captures/{payment_id}",
                        headers={"Authorization": f"Bearer {access_token}"}
                    )

                if capture_response.status_code >= 400:
                    error_data = capture_response.json()
                    logger.error(f"PayPal capture details error: {error_data}")
                    raise PaymentError(f"Refund failed: Unable to get capture details")

                capture_data = capture_response.json()
                currency = capture_data.get("amount", {}).get("currency_code", "USD")

                refund_data = {
                    "amount": {
                        "value": amount_str,
                        "currency_code": currency
                    }
                }

            # Process refund
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/v2/payments/captures/{payment_id}/refund",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {access_token}"
                    },
                    json=refund_data
                )

            if response.status_code >= 400:
                error_data = response.json()
                logger.error(f"PayPal refund error: {error_data}")
                raise PaymentError(f"Refund failed: {json.dumps(error_data)}")

            refund_data = response.json()
            amount_data = refund_data.get("amount", {})

            return {
                "refund_id": refund_data.get("id"),
                "status": refund_data.get("status"),
                "amount": amount_data.get("value")
            }

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during refund processing: {str(e)}")
            raise PaymentError(f"Refund failed due to network error: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error during refund processing: {str(e)}")
            raise PaymentError(f"Refund failed due to unexpected error: {str(e)}")

    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Get the status of a PayPal payment order.

        Args:
            payment_id: The ID of the payment to check

        Returns:
            Dictionary containing payment status information
                - payment_id: PayPal payment order ID
                - status: Payment status
                - amount: Amount charged
                - currency: Currency used

        Raises:
            PaymentError: If status retrieval fails
        """
        try:
            # Get auth token
            access_token = await self._get_auth_token()

            # Retrieve order details
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/v2/checkout/orders/{payment_id}",
                    headers={"Authorization": f"Bearer {access_token}"}
                )

            if response.status_code >= 400:
                error_data = response.json()
                logger.error(f"PayPal payment status error: {error_data}")
                raise PaymentError(f"Status check failed: {json.dumps(error_data)}")

            order_data = response.json()
            purchase_unit = order_data.get("purchase_units", [{}])[0]
            amount_data = purchase_unit.get("amount", {})

            return {
                "payment_id": order_data.get("id"),
                "status": order_data.get("status"),
                "amount": amount_data.get("value"),
                "currency": amount_data.get("currency_code")
            }

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during payment status check: {str(e)}")
            raise PaymentError(f"Status check failed due to network error: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error during payment status check: {str(e)}")
            raise PaymentError(f"Status check failed due to unexpected error: {str(e)}")