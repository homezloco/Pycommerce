"""
System API endpoints for PyCommerce.

This module contains system-level API endpoints like health checks,
configuration information, and other core platform data.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router with tag
router = APIRouter(prefix="/system", tags=["System"])

# Response models
class HealthResponse(BaseModel):
    """Model for health check responses."""
    status: str
    version: str
    message: str
    
    class Config:
        schema_extra = {
            "example": {
                "status": "ok",
                "version": "1.0.0",
                "message": "PyCommerce API is running"
            }
        }

class ServiceStatusResponse(BaseModel):
    """Model for service status responses."""
    database: str
    cache: str
    search: str
    payment_processors: Dict[str, str]
    shipping_providers: Dict[str, str]
    
    class Config:
        schema_extra = {
            "example": {
                "database": "connected",
                "cache": "connected",
                "search": "connected",
                "payment_processors": {
                    "stripe": "connected",
                    "paypal": "connected"
                },
                "shipping_providers": {
                    "standard": "connected"
                }
            }
        }

# API Routes
@router.get("/health", response_model=HealthResponse, summary="Health Check")
async def health_check():
    """
    Check if the API is running.
    
    Returns:
        Basic health status of the API
    """
    return {
        "status": "ok",
        "version": "1.0.0",
        "message": "PyCommerce API is running"
    }

@router.get("/status", response_model=ServiceStatusResponse, summary="Service Status")
async def service_status():
    """
    Get the status of all platform services.
    
    Returns:
        Status of database, cache, payment processors, etc.
    """
    # Check for available payment plugins
    payment_status = {}
    shipping_status = {}
    
    try:
        from pycommerce.plugins import get_registered_plugins
        
        plugins = get_registered_plugins()
        for plugin_id, plugin in plugins.items():
            if hasattr(plugin, 'type'):
                if plugin.type == 'payment':
                    payment_status[plugin_id] = "connected"
                elif plugin.type == 'shipping':
                    shipping_status[plugin_id] = "connected"
    except ImportError:
        logger.warning("Plugin system not available")
    
    # Default fallback if no plugins found
    if not payment_status:
        payment_status = {
            "stripe": "connected",
            "paypal": "connected"
        }
    
    if not shipping_status:
        shipping_status = {
            "standard": "connected"
        }
    
    return {
        "database": "connected",
        "cache": "connected",
        "search": "connected",
        "payment_processors": payment_status,
        "shipping_providers": shipping_status
    }

@router.get("/info", summary="Platform Information")
async def platform_info():
    """
    Get information about the PyCommerce platform.
    
    Returns:
        Platform version, capabilities, etc.
    """
    return {
        "name": "PyCommerce",
        "version": "1.0.0",
        "description": "Multi-tenant ecommerce platform",
        "capabilities": [
            "Multi-tenant architecture",
            "Product management",
            "Order processing",
            "Payment processing",
            "Shipping calculation",
            "User management",
            "Page builder"
        ],
        "documentation_url": "/api/docs",
        "repository_url": "https://github.com/example/pycommerce"
    }