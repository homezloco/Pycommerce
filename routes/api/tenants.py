"""
Tenants API endpoints for PyCommerce.

This module contains tenant-related API endpoints for creating, retrieving,
updating, and deleting tenants in the multi-tenant platform.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import logging
from uuid import UUID

from managers import TenantManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router with tag
router = APIRouter(prefix="/tenants", tags=["Tenants"])

# Response models
class TenantBase(BaseModel):
    """Base model for tenant data."""
    name: str
    slug: str
    domain: Optional[str] = None
    active: bool = True
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Fashion Store",
                "slug": "fashion",
                "domain": "fashion.example.com",
                "active": True
            }
        }

class TenantCreate(TenantBase):
    """Model for creating a new tenant."""
    pass

class TenantResponse(TenantBase):
    """Model for tenant responses with ID."""
    id: str
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Fashion Store",
                "slug": "fashion",
                "domain": "fashion.example.com",
                "active": True
            }
        }

class TenantsResponse(BaseModel):
    """Model for listing multiple tenants."""
    tenants: List[TenantResponse]
    count: int
    
    class Config:
        schema_extra = {
            "example": {
                "tenants": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Fashion Store",
                        "slug": "fashion",
                        "domain": "fashion.example.com",
                        "active": True
                    },
                    {
                        "id": "650e8400-e29b-41d4-a716-446655440000",
                        "name": "Electronics Shop",
                        "slug": "electronics",
                        "domain": "electronics.example.com",
                        "active": True
                    }
                ],
                "count": 2
            }
        }

class TenantUpdate(BaseModel):
    """Model for updating a tenant."""
    name: Optional[str] = None
    domain: Optional[str] = None
    active: Optional[bool] = None
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Fashion Store Updated",
                "domain": "fashion-new.example.com",
                "active": True
            }
        }

# API Routes
@router.get("/", response_model=TenantsResponse, summary="List All Tenants")
async def list_tenants(
    active_only: bool = Query(False, description="Only return active tenants")
):
    """
    Get a list of all tenants.
    
    Args:
        active_only: If True, only return active tenants
        
    Returns:
        A list of tenants with their details
    """
    tenant_manager = TenantManager()
    tenants = tenant_manager.get_all_tenants()
    
    if active_only:
        tenants = [t for t in tenants if t.active]
    
    return {
        "tenants": [
            {
                "id": str(t.id),
                "name": t.name,
                "slug": t.slug,
                "domain": t.domain,
                "active": t.active,
            }
            for t in tenants
        ],
        "count": len(tenants)
    }

@router.get("/{tenant_id}", response_model=TenantResponse, summary="Get Tenant by ID")
async def get_tenant(
    tenant_id: str = Path(..., description="The ID of the tenant to retrieve")
):
    """
    Get a single tenant by ID.
    
    Args:
        tenant_id: The unique identifier of the tenant
        
    Returns:
        The tenant details
        
    Raises:
        404: If the tenant is not found
    """
    tenant_manager = TenantManager()
    tenant = tenant_manager.get_tenant_by_id(tenant_id)
    
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant with id {tenant_id} not found")
    
    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "slug": tenant.slug,
        "domain": tenant.domain,
        "active": tenant.active,
    }

@router.get("/by-slug/{slug}", response_model=TenantResponse, summary="Get Tenant by Slug")
async def get_tenant_by_slug(
    slug: str = Path(..., description="The slug of the tenant to retrieve")
):
    """
    Get a single tenant by slug.
    
    Args:
        slug: The unique slug of the tenant
        
    Returns:
        The tenant details
        
    Raises:
        404: If the tenant is not found
    """
    tenant_manager = TenantManager()
    tenant = tenant_manager.get_tenant_by_slug(slug)
    
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant with slug {slug} not found")
    
    return {
        "id": str(tenant.id),
        "name": tenant.name,
        "slug": tenant.slug,
        "domain": tenant.domain,
        "active": tenant.active,
    }

@router.post("/", response_model=TenantResponse, summary="Create Tenant")
async def create_tenant(
    tenant: TenantCreate = Body(..., description="The tenant to create")
):
    """
    Create a new tenant.
    
    Args:
        tenant: The tenant details
        
    Returns:
        The created tenant with its ID
        
    Raises:
        400: If a tenant with the same slug already exists
    """
    tenant_manager = TenantManager()
    
    # Check if tenant with slug already exists
    existing = tenant_manager.get_tenant_by_slug(tenant.slug)
    if existing:
        raise HTTPException(status_code=400, detail=f"Tenant with slug {tenant.slug} already exists")
    
    # Create tenant
    new_tenant = tenant_manager.create_tenant(
        name=tenant.name,
        slug=tenant.slug,
        domain=tenant.domain,
        active=tenant.active
    )
    
    return {
        "id": str(new_tenant.id),
        "name": new_tenant.name,
        "slug": new_tenant.slug,
        "domain": new_tenant.domain,
        "active": new_tenant.active,
    }

@router.put("/{tenant_id}", response_model=TenantResponse, summary="Update Tenant")
async def update_tenant(
    tenant_id: str = Path(..., description="The ID of the tenant to update"),
    tenant_update: TenantUpdate = Body(..., description="The tenant updates")
):
    """
    Update an existing tenant.
    
    Args:
        tenant_id: The unique identifier of the tenant
        tenant_update: The fields to update
        
    Returns:
        The updated tenant
        
    Raises:
        404: If the tenant is not found
    """
    tenant_manager = TenantManager()
    
    # Check if tenant exists
    existing = tenant_manager.get_tenant_by_id(tenant_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Tenant with id {tenant_id} not found")
    
    # Prepare update data
    update_data = {}
    if tenant_update.name is not None:
        update_data["name"] = tenant_update.name
    if tenant_update.domain is not None:
        update_data["domain"] = tenant_update.domain
    if tenant_update.active is not None:
        update_data["active"] = tenant_update.active
    
    # Update tenant
    updated_tenant = tenant_manager.update_tenant(tenant_id, update_data)
    
    return {
        "id": str(updated_tenant.id),
        "name": updated_tenant.name,
        "slug": updated_tenant.slug,
        "domain": updated_tenant.domain,
        "active": updated_tenant.active,
    }

@router.delete("/{tenant_id}", response_model=Dict[str, Any], summary="Delete Tenant")
async def delete_tenant(
    tenant_id: str = Path(..., description="The ID of the tenant to delete")
):
    """
    Delete a tenant.
    
    Args:
        tenant_id: The unique identifier of the tenant
        
    Returns:
        A confirmation message
        
    Raises:
        404: If the tenant is not found
    """
    tenant_manager = TenantManager()
    
    # Check if tenant exists
    existing = tenant_manager.get_tenant_by_id(tenant_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Tenant with id {tenant_id} not found")
    
    # Delete tenant
    tenant_manager.delete_tenant(tenant_id)
    
    return {
        "success": True,
        "message": f"Tenant {existing.name} deleted successfully"
    }