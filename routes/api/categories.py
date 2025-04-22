"""
Categories API endpoints for PyCommerce.

This module contains category-related API endpoints for creating, retrieving,
updating, and managing product categories in the multi-tenant platform.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import logging
from uuid import UUID

from managers import TenantManager
from pycommerce.models.category import CategoryManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router with tag
router = APIRouter(prefix="/categories", tags=["Categories"])

# Response models
class CategoryBase(BaseModel):
    """Base model for category data."""
    name: str
    description: Optional[str] = None
    slug: str
    parent_id: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Electronics",
                "description": "Electronic devices and accessories",
                "slug": "electronics",
                "parent_id": None
            }
        }

class CategoryCreate(CategoryBase):
    """Model for creating a new category."""
    tenant_id: str
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Electronics",
                "description": "Electronic devices and accessories",
                "slug": "electronics",
                "parent_id": None,
                "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }

class CategoryResponse(CategoryBase):
    """Model for category responses with ID."""
    id: str
    tenant_id: str
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "650e8400-e29b-41d4-a716-446655440000",
                "name": "Electronics",
                "description": "Electronic devices and accessories",
                "slug": "electronics",
                "parent_id": None,
                "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }

class CategoriesResponse(BaseModel):
    """Model for listing multiple categories."""
    categories: List[CategoryResponse]
    tenant: str
    count: int
    
    class Config:
        schema_extra = {
            "example": {
                "categories": [
                    {
                        "id": "650e8400-e29b-41d4-a716-446655440000",
                        "name": "Electronics",
                        "description": "Electronic devices and accessories",
                        "slug": "electronics",
                        "parent_id": None,
                        "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
                    },
                    {
                        "id": "750e8400-e29b-41d4-a716-446655440000",
                        "name": "Smartphones",
                        "description": "Mobile phones and accessories",
                        "slug": "smartphones",
                        "parent_id": "650e8400-e29b-41d4-a716-446655440000",
                        "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
                    }
                ],
                "tenant": "electronics",
                "count": 2
            }
        }

class CategoryUpdate(BaseModel):
    """Model for updating a category."""
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Electronics and Gadgets",
                "description": "Updated description for electronics category",
                "parent_id": None
            }
        }

# API Routes
@router.get("/", response_model=CategoriesResponse, summary="List Categories")
async def list_categories(
    tenant: str = Query(..., description="Tenant slug"),
    parent_id: Optional[str] = Query(None, description="Filter by parent category ID")
):
    """
    Get categories for a tenant with optional filtering.
    
    Args:
        tenant: The tenant slug
        parent_id: Filter categories by parent ID (if None, return all categories)
        
    Returns:
        A list of categories matching the filters
        
    Raises:
        404: If the tenant is not found
    """
    tenant_manager = TenantManager()
    category_manager = CategoryManager()
    
    # Get tenant ID from slug
    tenant_obj = tenant_manager.get_tenant_by_slug(tenant)
    if not tenant_obj:
        raise HTTPException(
            status_code=404, detail=f"Tenant not found: {tenant}"
        )

    # Get categories
    if parent_id:
        categories = category_manager.get_subcategories(parent_id)
    else:
        categories = category_manager.get_categories_by_tenant(tenant_obj.id)
    
    return {
        "categories": [
            {
                "id": str(c.id),
                "name": c.name,
                "description": c.description,
                "slug": c.slug,
                "parent_id": str(c.parent_id) if c.parent_id else None,
                "tenant_id": str(c.tenant_id)
            }
            for c in categories
        ],
        "tenant": tenant,
        "count": len(categories)
    }

@router.get("/{category_id}", response_model=CategoryResponse, summary="Get Category by ID")
async def get_category(
    category_id: str = Path(..., description="The ID of the category to retrieve")
):
    """
    Get a single category by ID.
    
    Args:
        category_id: The unique identifier of the category
        
    Returns:
        The category details
        
    Raises:
        404: If the category is not found
    """
    category_manager = CategoryManager()
    category = category_manager.get_category_by_id(category_id)
    
    if not category:
        raise HTTPException(status_code=404, detail=f"Category with id {category_id} not found")
    
    return {
        "id": str(category.id),
        "name": category.name,
        "description": category.description,
        "slug": category.slug,
        "parent_id": str(category.parent_id) if category.parent_id else None,
        "tenant_id": str(category.tenant_id)
    }

@router.post("/", response_model=CategoryResponse, summary="Create Category")
async def create_category(
    category: CategoryCreate = Body(..., description="The category to create")
):
    """
    Create a new category.
    
    Args:
        category: The category details
        
    Returns:
        The created category with its ID
        
    Raises:
        404: If the tenant is not found
        404: If the parent category is not found
        400: If a category with the same slug already exists for this tenant
    """
    tenant_manager = TenantManager()
    category_manager = CategoryManager()
    
    # Check if tenant exists
    tenant = tenant_manager.get_tenant_by_id(category.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant with id {category.tenant_id} not found")
    
    # Check if parent category exists if provided
    if category.parent_id:
        parent = category_manager.get_category_by_id(category.parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail=f"Parent category with id {category.parent_id} not found")
    
    # Create category
    try:
        new_category = category_manager.create_category(
            tenant_id=category.tenant_id,
            name=category.name,
            description=category.description,
            slug=category.slug,
            parent_id=category.parent_id
        )
        
        return {
            "id": str(new_category.id),
            "name": new_category.name,
            "description": new_category.description,
            "slug": new_category.slug,
            "parent_id": str(new_category.parent_id) if new_category.parent_id else None,
            "tenant_id": str(new_category.tenant_id)
        }
    except Exception as e:
        logger.error(f"Error creating category: {e}")
        raise HTTPException(status_code=400, detail=f"Error creating category: {str(e)}")

@router.put("/{category_id}", response_model=CategoryResponse, summary="Update Category")
async def update_category(
    category_id: str = Path(..., description="The ID of the category to update"),
    category_update: CategoryUpdate = Body(..., description="The category updates")
):
    """
    Update an existing category.
    
    Args:
        category_id: The unique identifier of the category
        category_update: The fields to update
        
    Returns:
        The updated category
        
    Raises:
        404: If the category is not found
        404: If the parent category is not found
    """
    category_manager = CategoryManager()
    
    # Check if category exists
    existing = category_manager.get_category_by_id(category_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Category with id {category_id} not found")
    
    # Check if parent category exists if provided
    if category_update.parent_id:
        parent = category_manager.get_category_by_id(category_update.parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail=f"Parent category with id {category_update.parent_id} not found")
    
    # Prepare update data
    update_data = {}
    if category_update.name is not None:
        update_data["name"] = category_update.name
    if category_update.description is not None:
        update_data["description"] = category_update.description
    if category_update.parent_id is not None:
        update_data["parent_id"] = category_update.parent_id
    
    # Update category
    updated_category = category_manager.update_category(category_id, update_data)
    
    return {
        "id": str(updated_category.id),
        "name": updated_category.name,
        "description": updated_category.description,
        "slug": updated_category.slug,
        "parent_id": str(updated_category.parent_id) if updated_category.parent_id else None,
        "tenant_id": str(updated_category.tenant_id)
    }

@router.delete("/{category_id}", response_model=Dict[str, Any], summary="Delete Category")
async def delete_category(
    category_id: str = Path(..., description="The ID of the category to delete")
):
    """
    Delete a category.
    
    Args:
        category_id: The unique identifier of the category
        
    Returns:
        A confirmation message
        
    Raises:
        404: If the category is not found
        400: If the category has subcategories
    """
    category_manager = CategoryManager()
    
    # Check if category exists
    existing = category_manager.get_category_by_id(category_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Category with id {category_id} not found")
    
    # Check if category has subcategories
    subcategories = category_manager.get_subcategories(category_id)
    if subcategories:
        raise HTTPException(status_code=400, detail=f"Cannot delete category with subcategories")
    
    # Delete category
    category_manager.delete_category(category_id)
    
    return {
        "success": True,
        "message": f"Category {existing.name} deleted successfully"
    }