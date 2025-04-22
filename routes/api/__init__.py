"""
API routes for PyCommerce.

This module initializes and configures the API routes for the PyCommerce platform.
"""

import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create API router
api_router = APIRouter(prefix="/api")

# Import API endpoints
try:
    # System endpoints
    from .system import router as system_router
    api_router.include_router(system_router)
    logger.info("System API routes registered")
except ImportError as e:
    logger.warning(f"Failed to register system API routes: {str(e)}")

try:
    # Tenant endpoints
    from .tenants import router as tenants_router
    api_router.include_router(tenants_router)
    logger.info("Tenant API routes registered")
except ImportError as e:
    logger.warning(f"Failed to register tenant API routes: {str(e)}")

try:
    # Product endpoints
    from .products import router as products_router
    api_router.include_router(products_router)
    logger.info("Product API routes registered")
except ImportError as e:
    logger.warning(f"Failed to register product API routes: {str(e)}")

try:
    # Order endpoints
    from .orders import router as orders_router
    api_router.include_router(orders_router)
    logger.info("Order API routes registered")
except ImportError as e:
    logger.warning(f"Failed to register order API routes: {str(e)}")

try:
    # Category endpoints
    from .categories import router as categories_router
    api_router.include_router(categories_router)
    logger.info("Category API routes registered")
except ImportError as e:
    logger.warning(f"Failed to register category API routes: {str(e)}")

try:
    # User endpoints
    from .users import router as users_router
    api_router.include_router(users_router)
    logger.info("User API routes registered")
except ImportError as e:
    logger.warning(f"Failed to register user API routes: {str(e)}")

# Root API endpoint
@api_router.get("/", include_in_schema=True, tags=["System"])
async def api_root(request: Request) -> Dict[str, Any]:
    """
    API root endpoint returning information about available endpoints.
    
    Args:
        request: The request object
        
    Returns:
        Information about the API and available endpoints
    """
    root_path = request.scope.get("root_path", "").rstrip("/")
    
    return {
        "name": "PyCommerce API",
        "version": "1.0.0",
        "description": "API for the PyCommerce multi-tenant ecommerce platform",
        "endpoints": {
            "documentation": {
                "swagger": f"{root_path}/api/docs",
                "redoc": f"{root_path}/api/redoc",
                "openapi_json": f"{root_path}/api/openapi.json"
            },
            "system": {
                "health": f"{root_path}/api/system/health"
            },
            "tenants": f"{root_path}/api/tenants",
            "products": f"{root_path}/api/products",
            "orders": f"{root_path}/api/orders",
            "categories": f"{root_path}/api/categories",
            "users": f"{root_path}/api/users"
        }
    }