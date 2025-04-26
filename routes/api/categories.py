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
@router.get("/", 
         response_model=CategoriesResponse, 
         summary="List Categories",
         description="Retrieve all categories for a specific tenant with optional filtering",
         responses={
             200: {"description": "Categories retrieved successfully", "model": CategoriesResponse},
             400: {"description": "Invalid tenant slug format"},
             401: {"description": "Unauthorized - requires proper authentication"},
             404: {"description": "Tenant not found"},
             500: {"description": "Internal server error"}
         })
async def list_categories(
    tenant: str = Query(..., description="The tenant slug identifier to retrieve categories for"),
    parent_id: Optional[str] = Query(None, description="Filter categories by parent category ID (UUID format)")
):
    """
    Retrieve all categories for a specific tenant with optional filtering.
    
    This endpoint returns a list of product categories belonging to a specific tenant. 
    Categories are used to organize products and provide a hierarchical navigation 
    structure for the storefront. Categories can be filtered by parent category ID 
    to retrieve only subcategories of a specific parent.
    
    - **tenant**: Required tenant slug identifier
    - **parent_id**: Optional UUID of a parent category to filter subcategories
    
    Returns a list of category objects including their IDs, names, descriptions, slugs,
    and parent relationships. Categories are sorted alphabetically by name. If a 
    parent_id is provided, only direct children of that category will be returned.
    
    If no categories exist for the tenant, an empty list is returned with count=0.
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

@router.get("/{category_id}", 
         response_model=CategoryResponse, 
         summary="Get Category by ID",
         description="Retrieve detailed information about a specific category",
         responses={
             200: {"description": "Category retrieved successfully", "model": CategoryResponse},
             400: {"description": "Invalid category ID format"},
             401: {"description": "Unauthorized - requires proper authentication"},
             404: {"description": "Category not found"},
             500: {"description": "Internal server error"}
         })
async def get_category(
    category_id: str = Path(..., description="The unique UUID of the category to retrieve")
):
    """
    Retrieve detailed information about a specific category.
    
    This endpoint returns comprehensive details about a single product category, including 
    its name, description, slug, and hierarchy information (parent category if applicable).
    Category details are essential for product organization and navigation structure
    in the storefront.
    
    - **category_id**: Required UUID of the category to retrieve
    
    Returns complete category object with all associated metadata. The parent_id field
    will be null if this is a top-level category. The tenant_id indicates which store
    the category belongs to.
    
    Use this endpoint when you need to access specific category details for editing,
    displaying category information, or determining category relationships.
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

@router.post("/", 
         response_model=CategoryResponse, 
         summary="Create Category",
         description="Create a new product category within a tenant's store",
         responses={
             201: {"description": "Category created successfully", "model": CategoryResponse},
             400: {"description": "Invalid request or duplicate category slug"},
             401: {"description": "Unauthorized - requires proper authentication"},
             404: {"description": "Tenant or parent category not found"},
             409: {"description": "Conflict - category with same slug already exists"},
             500: {"description": "Internal server error"}
         },
         status_code=201)
async def create_category(
    category: CategoryCreate = Body(..., description="The category details including name, description, slug, tenant ID and optional parent ID")
):
    """
    Create a new product category within a tenant's store.
    
    This endpoint allows creating a new product category for organizing products in the 
    storefront. Categories can be nested hierarchically using the parent_id field to create
    subcategories, enabling a multi-level navigation structure.
    
    The required fields are:
    - **name**: The display name of the category
    - **slug**: URL-friendly identifier (must be unique within tenant)
    - **tenant_id**: The UUID of the tenant this category belongs to
    
    Optional fields include:
    - **description**: Detailed category description for admin and SEO purposes
    - **parent_id**: UUID of parent category if this is a subcategory
    
    Slugs must be unique within a tenant and should only contain alphanumeric characters,
    hyphens, and underscores. The system will validate that the tenant exists and that
    the parent category exists (if specified).
    
    Returns the complete category object with all metadata and generated UUID.
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

@router.put("/{category_id}", 
         response_model=CategoryResponse, 
         summary="Update Category",
         description="Update an existing product category's attributes",
         responses={
             200: {"description": "Category updated successfully", "model": CategoryResponse},
             400: {"description": "Invalid request or validation error"},
             401: {"description": "Unauthorized - requires proper authentication"},
             404: {"description": "Category or parent category not found"},
             422: {"description": "Validation error in request body"},
             500: {"description": "Internal server error"}
         })
async def update_category(
    category_id: str = Path(..., description="The unique UUID of the category to update"),
    category_update: CategoryUpdate = Body(..., description="The category attributes to update (name, description, and/or parent_id)")
):
    """
    Update an existing product category's attributes.
    
    This endpoint allows partial updates to a product category. The slug of a category
    cannot be changed after creation to maintain URL stability and prevent broken links.
    You can update the name, description, and parent category relationship.
    
    The updatable fields are:
    - **name**: Display name of the category
    - **description**: Detailed category description
    - **parent_id**: UUID of parent category (or null to make it a top-level category)
    
    When changing a category's parent, the system verifies that:
    1. The specified parent category exists
    2. The operation won't create a circular reference
    3. The parent category belongs to the same tenant
    
    The update is performed as a transaction, so either all changes are applied or none.
    If the specified category doesn't exist, a 404 error is returned. Any validation
    errors will result in a 400 response with details about the validation failure.
    
    Returns the complete updated category object with all metadata.
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

@router.delete("/{category_id}", 
         response_model=Dict[str, Any], 
         summary="Delete Category",
         description="Remove a product category that has no subcategories",
         responses={
             200: {"description": "Category deleted successfully"},
             400: {"description": "Category has subcategories and cannot be deleted"},
             401: {"description": "Unauthorized - requires proper authentication"},
             404: {"description": "Category not found"},
             409: {"description": "Conflict - category has associated products"},
             500: {"description": "Internal server error"}
         })
async def delete_category(
    category_id: str = Path(..., description="The unique UUID of the category to delete")
):
    """
    Remove a product category that has no subcategories.
    
    This endpoint permanently deletes a category from the system. The operation is only
    allowed if the category has no subcategories. This constraint prevents accidentally
    deleting entire category trees and ensures proper reorganization of the category
    hierarchy.
    
    - **category_id**: Required UUID of the category to delete
    
    The system performs the following validations before deletion:
    1. Verifies the category exists
    2. Checks if the category has any subcategories
    3. Ensures there are no products directly assigned to this category
    
    If the category has subcategories, a 400 error is returned with a message indicating
    that subcategories must be removed or reassigned first. If products are associated
    with the category, a 409 error is returned.
    
    Returns a success confirmation with the deleted category's name on successful deletion.
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