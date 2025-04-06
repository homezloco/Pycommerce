"""
Custom exceptions for the PyCommerce SDK.

This module defines all the custom exceptions used throughout the SDK
to provide specific error types for different kinds of failures.
"""

class PyCommerceError(Exception):
    """Base exception for all PyCommerce errors."""
    
    def __init__(self, message: str = "An error occurred in PyCommerce"):
        self.message = message
        super().__init__(self.message)


class ProductError(PyCommerceError):
    """Exception raised for errors in product operations."""
    
    def __init__(self, message: str = "An error occurred with product operations"):
        super().__init__(message)


class CartError(PyCommerceError):
    """Exception raised for errors in cart operations."""
    
    def __init__(self, message: str = "An error occurred with cart operations"):
        super().__init__(message)


class OrderError(PyCommerceError):
    """Exception raised for errors in order operations."""
    
    def __init__(self, message: str = "An error occurred with order operations"):
        super().__init__(message)


class PaymentError(PyCommerceError):
    """Base exception for all payment processing errors."""
    
    def __init__(self, message: str = "An error occurred with payment processing", error_code: str = "payment_error"):
        self.error_code = error_code
        super().__init__(message)


class PaymentAuthenticationError(PaymentError):
    """Exception raised when payment provider authentication fails."""
    
    def __init__(self, message: str = "Failed to authenticate with payment provider"):
        super().__init__(message, error_code="payment_auth_error")


class PaymentConfigError(PaymentError):
    """Exception raised when payment provider configuration is invalid or missing."""
    
    def __init__(self, message: str = "Payment provider configuration is invalid or missing"):
        super().__init__(message, error_code="payment_config_error")


class PaymentProcessingError(PaymentError):
    """Exception raised when payment processing fails due to payment provider issues."""
    
    def __init__(self, message: str = "Payment processing failed", decline_reason: str = None):
        self.decline_reason = decline_reason
        super().__init__(message, error_code="payment_processing_error")


class PaymentValidationError(PaymentError):
    """Exception raised when payment data validation fails."""
    
    def __init__(self, message: str = "Payment data validation failed", invalid_fields: list = None):
        self.invalid_fields = invalid_fields or []
        super().__init__(message, error_code="payment_validation_error")


class PaymentRefundError(PaymentError):
    """Exception raised when payment refund fails."""
    
    def __init__(self, message: str = "Payment refund failed"):
        super().__init__(message, error_code="payment_refund_error")


class ShippingError(PyCommerceError):
    """Exception raised for errors in shipping operations."""
    
    def __init__(self, message: str = "An error occurred with shipping operations"):
        super().__init__(message)


class PluginError(PyCommerceError):
    """Exception raised for errors in plugin operations."""
    
    def __init__(self, message: str = "An error occurred with plugin operations"):
        super().__init__(message)


class ConfigError(PyCommerceError):
    """Exception raised for errors in configuration operations."""
    
    def __init__(self, message: str = "An error occurred with configuration operations"):
        super().__init__(message)
