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
    """Exception raised for errors in payment processing."""
    
    def __init__(self, message: str = "An error occurred with payment processing"):
        super().__init__(message)


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
