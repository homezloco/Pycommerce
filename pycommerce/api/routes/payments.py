"""
API routes for payment operations.

This module defines the API routes for processing payments using various 
payment providers through the PyCommerce plugin system.
"""

import logging
from typing import Dict, List, Any, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query

from pydantic import BaseModel, Field

from pycommerce.plugins.payment import PaymentPlugin, StripePaymentPlugin, PaypalPaymentPlugin
from pycommerce.core.exceptions import PaymentError


logger = logging.getLogger("pycommerce.api.routes.payments")

router = APIRouter()


class PaymentRequest(BaseModel):
    """Model for payment processing requests."""
    order_id: str
    amount: float
    currency: str = "USD"
    payment_method: str
    return_url: Optional[str] = None
    cancel_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PaymentResponse(BaseModel):
    """Model for payment processing responses."""
    payment_id: str
    status: str
    provider: str
    approval_url: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    error: Optional[str] = None


class RefundRequest(BaseModel):
    """Model for refund processing requests."""
    payment_id: str
    amount: Optional[float] = None
    reason: Optional[str] = None


class RefundResponse(BaseModel):
    """Model for refund processing responses."""
    refund_id: str
    status: str
    provider: str
    amount: Optional[float] = None
    error: Optional[str] = None


class PaymentStatusResponse(BaseModel):
    """Model for payment status responses."""
    payment_id: str
    status: str
    provider: str
    amount: Optional[float] = None
    currency: Optional[str] = None
    error: Optional[str] = None


class PaymentManager:
    """
    Manager class for payment operations.
    
    This class handles payment processing, refunds, and status checks
    using the appropriate payment plugin.
    """
    
    def __init__(self):
        """Initialize payment plugins."""
        self._stripe_plugin = StripePaymentPlugin()
        self._paypal_plugin = PayPalPaymentPlugin()
        self._plugins = {
            "stripe": self._stripe_plugin,
            "paypal": self._paypal_plugin
        }
        
        # Initialize plugins
        for plugin in self._plugins.values():
            plugin.initialize()
    
    def get_plugin(self, provider: str) -> PaymentPlugin:
        """
        Get the payment plugin for the specified provider.
        
        Args:
            provider: The payment provider name
            
        Returns:
            The payment plugin instance
            
        Raises:
            ValueError: If the provider is not supported
        """
        if provider not in self._plugins:
            raise ValueError(f"Unsupported payment provider: {provider}")
        
        return self._plugins[provider]
    
    def get_available_providers(self) -> List[str]:
        """
        Get a list of available payment providers.
        
        Returns:
            List of payment provider names
        """
        return list(self._plugins.keys())


# Global payment manager instance
payment_manager = PaymentManager()


@router.get("/providers", response_model=List[str], tags=["payments"])
async def get_payment_providers():
    """
    Get a list of available payment providers.
    
    Returns:
        List of payment provider names
    """
    try:
        return payment_manager.get_available_providers()
    except Exception as e:
        logger.error(f"Error getting payment providers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting payment providers: {str(e)}")


@router.post("/process", response_model=PaymentResponse, tags=["payments"])
async def process_payment(payment_request: PaymentRequest, provider: str = Query(..., description="Payment provider (e.g., 'stripe', 'paypal')")):
    """
    Process a payment using the specified provider.
    
    Args:
        payment_request: Payment processing request
        provider: Payment provider name
        
    Returns:
        Payment processing response
    """
    try:
        # Get the payment plugin for the provider
        plugin = payment_manager.get_plugin(provider.lower())
        
        # Prepare payment data
        payment_data = {
            "amount": payment_request.amount,
            "currency": payment_request.currency.lower(),
            "payment_method": payment_request.payment_method,
            **payment_request.metadata
        }
        
        # Add return and cancel URLs for PayPal
        if provider.lower() == "paypal":
            if not payment_request.return_url or not payment_request.cancel_url:
                raise HTTPException(
                    status_code=400, 
                    detail="PayPal payments require return_url and cancel_url"
                )
            payment_data["return_url"] = payment_request.return_url
            payment_data["cancel_url"] = payment_request.cancel_url
        
        # Process the payment
        result = await plugin.process_payment(
            UUID(payment_request.order_id),
            payment_data
        )
        
        # For PayPal, check if we need to capture the payment
        if provider.lower() == "paypal" and result.get("status") == "APPROVED":
            capture_result = await plugin.capture_payment(result["payment_id"])
            result.update(capture_result)
        
        # Create response
        response = PaymentResponse(
            payment_id=result.get("payment_id", ""),
            status=result.get("status", "unknown"),
            provider=provider,
            approval_url=result.get("approval_url"),
            amount=result.get("amount"),
            currency=result.get("currency")
        )
        
        return response
    
    except PaymentError as e:
        logger.error(f"Payment error: {str(e)}")
        return PaymentResponse(
            payment_id="",
            status="error",
            provider=provider,
            error=str(e)
        )
    
    except ValueError as e:
        logger.error(f"Invalid payment provider: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected payment processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Payment processing failed: {str(e)}")


@router.post("/refund", response_model=RefundResponse, tags=["payments"])
async def refund_payment(refund_request: RefundRequest, provider: str = Query(..., description="Payment provider (e.g., 'stripe', 'paypal')")):
    """
    Refund a payment using the specified provider.
    
    Args:
        refund_request: Refund processing request
        provider: Payment provider name
        
    Returns:
        Refund processing response
    """
    try:
        # Get the payment plugin for the provider
        plugin = payment_manager.get_plugin(provider.lower())
        
        # Process the refund
        result = await plugin.refund_payment(
            refund_request.payment_id,
            refund_request.amount
        )
        
        # Create response
        response = RefundResponse(
            refund_id=result.get("refund_id", ""),
            status=result.get("status", "unknown"),
            provider=provider,
            amount=result.get("amount")
        )
        
        return response
    
    except PaymentError as e:
        logger.error(f"Refund error: {str(e)}")
        return RefundResponse(
            refund_id="",
            status="error",
            provider=provider,
            error=str(e)
        )
    
    except ValueError as e:
        logger.error(f"Invalid payment provider: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected refund processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Refund processing failed: {str(e)}")


@router.get("/status/{payment_id}", response_model=PaymentStatusResponse, tags=["payments"])
async def get_payment_status(payment_id: str, provider: str = Query(..., description="Payment provider (e.g., 'stripe', 'paypal')")):
    """
    Get the status of a payment.
    
    Args:
        payment_id: Payment ID to check
        provider: Payment provider name
        
    Returns:
        Payment status response
    """
    try:
        # Get the payment plugin for the provider
        plugin = payment_manager.get_plugin(provider.lower())
        
        # Get the payment status
        result = await plugin.get_payment_status(payment_id)
        
        # Create response
        response = PaymentStatusResponse(
            payment_id=result.get("payment_id", payment_id),
            status=result.get("status", "unknown"),
            provider=provider,
            amount=result.get("amount"),
            currency=result.get("currency")
        )
        
        return response
    
    except PaymentError as e:
        logger.error(f"Payment status error: {str(e)}")
        return PaymentStatusResponse(
            payment_id=payment_id,
            status="error",
            provider=provider,
            error=str(e)
        )
    
    except ValueError as e:
        logger.error(f"Invalid payment provider: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected payment status error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Payment status check failed: {str(e)}")