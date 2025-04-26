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
@router.get("/", response_model=TenantsResponse, 
         summary="List All Tenants",
         description="Retrieves a complete list of all tenants with pagination support",
         responses={
             200: {"description": "List of tenants retrieved successfully", "model": TenantsResponse},
             401: {"description": "Unauthorized"},
             500: {"description": "Internal server error"}
         })
async def list_tenants(
    active_only: bool = Query(False, description="Only return active tenants")
):
    """
    Retrieve a complete list of all tenants in the system.
    
    This endpoint returns all tenants registered in the system. By default, it returns
    both active and inactive tenants. Use the active_only parameter to filter results
    to only active tenants. This endpoint requires admin permissions in a production
    environment.
    
    - **active_only**: Filter results to only include active tenants (default: false)
    
    Returns a list of tenants with their complete details and a count of the total results.
    Each tenant includes its unique ID, name, slug, domain (if set), and active status.
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

@router.get("/{tenant_id}", response_model=TenantResponse, 
         summary="Get Tenant by ID",
         description="Retrieves detailed information about a specific tenant",
         responses={
             200: {"description": "Tenant details retrieved successfully", "model": TenantResponse},
             400: {"description": "Invalid tenant ID format"},
             404: {"description": "Tenant not found"},
             500: {"description": "Internal server error"}
         })
async def get_tenant(
    tenant_id: str = Path(..., description="The ID of the tenant to retrieve")
):
    """
    Retrieve detailed information about a specific tenant by its unique ID.
    
    This endpoint returns comprehensive details about a specific tenant, including its name,
    slug, domain configuration, and active status. The tenant ID should be provided as a 
    UUID string. This endpoint requires appropriate permissions in a production environment.
    
    - **tenant_id**: The unique identifier of the tenant (UUID format)
    
    Returns the tenant details if found, including its ID, name, slug, domain (if configured),
    and active status. If the tenant does not exist, a 404 error is returned.
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

@router.get("/by-slug/{slug}", response_model=TenantResponse, 
         summary="Get Tenant by Slug",
         description="Retrieves tenant information using the URL-friendly slug identifier",
         responses={
             200: {"description": "Tenant details retrieved successfully", "model": TenantResponse},
             404: {"description": "Tenant not found"},
             500: {"description": "Internal server error"}
         })
async def get_tenant_by_slug(
    slug: str = Path(..., description="The URL slug of the tenant to retrieve")
):
    """
    Retrieve tenant information using its URL-friendly slug identifier.
    
    This endpoint retrieves comprehensive tenant details by looking up the tenant's
    unique slug. The slug is the URL-friendly identifier used in routes and
    domain configurations. This method is particularly useful for storefront operations
    and tenant identification in multi-tenant environments.
    
    - **slug**: The unique slug identifier for the tenant (URL-friendly string)
    
    Returns the tenant details if found, including its ID, name, slug, domain (if configured),
    and active status. If no tenant exists with the provided slug, a 404 error is returned.
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

@router.post("/", response_model=TenantResponse, 
         summary="Create Tenant",
         description="Creates a new tenant in the multi-tenant environment",
         status_code=201,
         responses={
             201: {"description": "Tenant created successfully", "model": TenantResponse},
             400: {"description": "Invalid request or tenant with same slug already exists"},
             401: {"description": "Unauthorized - requires admin privileges"},
             500: {"description": "Internal server error"}
         })
async def create_tenant(
    tenant: TenantCreate = Body(..., description="The tenant data including name, slug, domain, and active status")
):
    """
    Create a new tenant in the multi-tenant environment.
    
    This endpoint creates a new tenant (store) with the provided details. Each tenant 
    represents a separate store with its own products, orders, settings, and domain 
    configuration. The tenant slug must be unique and URL-friendly as it may be used 
    in route paths and subdomain names.
    
    - **tenant**: Complete tenant details including:
      - **name**: Display name for the tenant/store (required)
      - **slug**: URL-friendly unique identifier (required, lowercase letters, numbers, and hyphens only)
      - **domain**: Custom domain name for the tenant (optional)
      - **active**: Whether the tenant is active and accessible (default: true)
    
    Returns the created tenant with all fields including the generated UUID.
    Returns a 400 error if a tenant with the same slug already exists or if the data is invalid.
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

@router.put("/{tenant_id}", response_model=TenantResponse, 
         summary="Update Tenant",
         description="Updates an existing tenant's information",
         responses={
             200: {"description": "Tenant updated successfully", "model": TenantResponse},
             400: {"description": "Invalid tenant ID format or invalid data"},
             401: {"description": "Unauthorized - requires admin privileges"},
             404: {"description": "Tenant not found"},
             500: {"description": "Internal server error"}
         })
async def update_tenant(
    tenant_id: str = Path(..., description="The ID of the tenant to update"),
    tenant_update: TenantUpdate = Body(..., description="The tenant fields to update (partial updates supported)")
):
    """
    Update an existing tenant's information.
    
    This endpoint allows for partial updates to tenant information. Only the fields
    provided in the request body will be updated; other fields will remain unchanged.
    The tenant slug cannot be modified after creation to maintain URL consistency and
    prevent breaking existing links.
    
    - **tenant_id**: The unique identifier of the tenant to update (UUID format)
    - **tenant_update**: The fields to update, which can include:
      - **name**: New display name for the tenant/store (optional)
      - **domain**: New custom domain configuration (optional)
      - **active**: Whether the tenant should be active and accessible (optional)
    
    Returns the updated tenant with all fields.
    Returns a 404 error if no tenant exists with the provided ID.
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

@router.delete("/{tenant_id}", 
         summary="Delete Tenant",
         description="Permanently removes a tenant and all associated data",
         responses={
             200: {"description": "Tenant deleted successfully", "content": {"application/json": {"example": {"success": True, "message": "Tenant Example Store deleted successfully"}}}},
             400: {"description": "Invalid tenant ID format"},
             401: {"description": "Unauthorized - requires admin privileges"},
             404: {"description": "Tenant not found"},
             500: {"description": "Internal server error"}
         })
async def delete_tenant(
    tenant_id: str = Path(..., description="The ID of the tenant to delete")
):
    """
    Permanently delete a tenant and all its associated data.
    
    This endpoint permanently removes a tenant and all of its associated data from the system,
    including products, orders, pages, media, and settings. This operation cannot be undone.
    This is a destructive action that requires appropriate authorization in a production
    environment.
    
    - **tenant_id**: The unique identifier of the tenant to delete (UUID format)
    
    Returns a success message if the tenant was deleted successfully.
    Returns a 404 error if no tenant exists with the provided ID.
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