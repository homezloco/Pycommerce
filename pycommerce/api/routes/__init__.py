"""
API routes package initialization.

This package contains API route definitions for the PyCommerce platform.
"""

from fastapi import APIRouter

# Create main API router
api_router = APIRouter(prefix="/api")

# Import routers
try:
    from pycommerce.api.routes.market_analysis import router as market_analysis_router
    from pycommerce.api.routes.recommendations import router as recommendations_router
    # Register routers
    api_router.include_router(market_analysis_router)
    api_router.include_router(recommendations_router)
except ImportError as e:
    print(f"Error importing API routes: {str(e)}")

# Function to register API routes with the FastAPI app
def register_api_routes(app):
    """
    Register all API routes with the FastAPI application.
    
    Args:
        app: FastAPI application
    """
    app.include_router(api_router)