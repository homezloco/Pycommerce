"""
Admin API routes for the PyCommerce admin panel.

This module provides general-purpose API endpoints used throughout the admin panel,
including endpoints for tenant verification, status checks, and utilities.
"""
import logging
from typing import Dict, Optional, List, Any

from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse

from pycommerce.models.tenant import TenantManager
from pycommerce.core.db import SessionLocal

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin/api", tags=["admin", "api"])

# Initialize managers
try:
    tenant_manager = TenantManager()
except Exception as e:
    logger.error(f"Error initializing TenantManager: {e}")
    tenant_manager = None

@router.get("/tenant-check", tags=["admin", "api"])
async def tenant_check(
    request: Request,
    slug: str = Query(..., description="Tenant slug to check")
):
    """
    Check if a tenant with the given slug exists.
    This endpoint is used by the page builder for tenant verification.
    """
    try:
        logger.info(f"Checking if tenant exists with slug: {slug}")
        
        if not tenant_manager:
            logger.error("TenantManager not available")
            return JSONResponse(
                status_code=500,
                content={"error": "Tenant manager not available"}
            )
        
        # Try to get the tenant by slug
        tenant = tenant_manager.get_by_slug(slug)
        
        if tenant:
            logger.info(f"Tenant found: {tenant.name} (ID: {tenant.id})")
            return {
                "exists": True,
                "tenant": {
                    "id": str(tenant.id),
                    "name": tenant.name,
                    "slug": tenant.slug
                }
            }
        else:
            logger.info(f"No tenant found with slug: {slug}")
            return {"exists": False}
            
    except Exception as e:
        logger.error(f"Error checking tenant: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error checking tenant: {str(e)}"}
        )

@router.get("/tenants/{tenant_id}", tags=["admin", "api"])
async def get_tenant(
    request: Request,
    tenant_id: str
):
    """
    Get tenant information by ID.
    This endpoint is used by the page builder and other admin components.
    """
    try:
        logger.info(f"Getting tenant with ID: {tenant_id}")
        
        if not tenant_manager:
            logger.error("TenantManager not available")
            return JSONResponse(
                status_code=500,
                content={"error": "Tenant manager not available"}
            )
        
        # Try to get the tenant by ID
        tenant = tenant_manager.get(tenant_id)
        
        if tenant:
            logger.info(f"Tenant found: {tenant.name} (ID: {tenant.id})")
            return {
                "id": str(tenant.id),
                "name": tenant.name,
                "slug": tenant.slug,
                "domain": tenant.domain if hasattr(tenant, "domain") else None
            }
        else:
            logger.info(f"No tenant found with ID: {tenant_id}")
            return JSONResponse(
                status_code=404,
                content={"error": f"Tenant with ID {tenant_id} not found"}
            )
            
    except Exception as e:
        logger.error(f"Error getting tenant: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error getting tenant: {str(e)}"}
        )

def setup_routes():
    """Set up the API routes."""
    return router