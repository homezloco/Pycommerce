"""
API routes for PyCommerce SDK.

This package contains modules that define FastAPI routes
for different parts of the PyCommerce SDK.
"""

from fastapi import APIRouter

from pycommerce.api.routes import cart, checkout, payments, products, users

# Create a router that includes all API routes
router = APIRouter()

# Include all module routers
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(products.router, prefix="/products", tags=["products"])
router.include_router(cart.router, prefix="/cart", tags=["cart"])
router.include_router(checkout.router, prefix="/checkout", tags=["checkout"])
router.include_router(payments.router, prefix="/payments", tags=["payments"])

__all__ = ["router"]
