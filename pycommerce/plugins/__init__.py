"""
Plugin packages for PyCommerce SDK.

This package contains built-in plugins for the PyCommerce SDK,
organized by functionality type.
"""

# Import built-in plugins for easier access
from pycommerce.plugins.payment.stripe import StripePaymentPlugin
from pycommerce.plugins.shipping.standard import StandardShippingPlugin

__all__ = [
    "StripePaymentPlugin",
    "StandardShippingPlugin",
]
