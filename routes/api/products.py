"""
Products API endpoints for PyCommerce.

This module contains product-related API endpoints for creating, retrieving,
updating, and deleting products in the multi-tenant platform.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import logging
from uuid import UUID

from managers import ProductManager, TenantManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router with tag
router = APIRouter(prefix="/products", tags=["Products"])

# Response models
class ProductBase(BaseModel):
    """Base model for product data."""
    name: str
    description: Optional[str] = None
    price: float
    sku: str
    stock: int = 0
    categories: List[str] = Field(default_factory=list)
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Premium Wireless Headphones",
                "description": "High-quality noise-cancelling wireless headphones with 20-hour battery life",
                "price": 199.99,
                "sku": "TECH-AUDIO-001",
                "stock": 25,
                "categories": ["Audio", "Electronics"]
            }
        }

class ProductCreate(ProductBase):
    """Model for creating a new product."""
    tenant_id: str
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Premium Wireless Headphones",
                "description": "High-quality noise-cancelling wireless headphones with 20-hour battery life",
                "price": 199.99,
                "sku": "TECH-AUDIO-001",
                "stock": 25,
                "categories": ["Audio", "Electronics"],
                "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }

class ProductResponse(ProductBase):
    """Model for product responses with ID."""
    id: str
    tenant_id: str
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "650e8400-e29b-41d4-a716-446655440000",
                "name": "Premium Wireless Headphones",
                "description": "High-quality noise-cancelling wireless headphones with 20-hour battery life",
                "price": 199.99,
                "sku": "TECH-AUDIO-001",
                "stock": 25,
                "categories": ["Audio", "Electronics"],
                "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }

class ProductsResponse(BaseModel):
    """Model for listing multiple products."""
    products: List[ProductResponse]
    tenant: str
    count: int
    filters: Dict[str, Any] = {}
    
    class Config:
        schema_extra = {
            "example": {
                "products": [
                    {
                        "id": "650e8400-e29b-41d4-a716-446655440000",
                        "name": "Premium Wireless Headphones",
                        "description": "High-quality noise-cancelling wireless headphones with 20-hour battery life",
                        "price": 199.99,
                        "sku": "TECH-AUDIO-001",
                        "stock": 25,
                        "categories": ["Audio", "Electronics"],
                        "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
                    },
                    {
                        "id": "750e8400-e29b-41d4-a716-446655440000",
                        "name": "Ultra HD Smart TV",
                        "description": "65-inch Ultra HD Smart TV with built-in streaming apps",
                        "price": 1299.99,
                        "sku": "TECH-TV-001",
                        "stock": 10,
                        "categories": ["TV", "Electronics"],
                        "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
                    }
                ],
                "tenant": "electronics",
                "count": 2,
                "filters": {"category": "Electronics"}
            }
        }

class ProductUpdate(BaseModel):
    """Model for updating a product."""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    categories: Optional[List[str]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Premium Wireless Headphones - 2023 Edition",
                "price": 249.99,
                "stock": 50,
                "categories": ["Audio", "Electronics", "Featured"]
            }
        }

# API Routes
@router.get("/", response_model=ProductsResponse, summary="List Products")
async def list_products(
    tenant: str = Query(..., description="Tenant slug"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock availability")
):
    """
    Get products for a tenant with optional filtering.
    
    Args:
        tenant: The tenant slug
        category: Filter products by category
        min_price: Filter products by minimum price
        max_price: Filter products by maximum price
        in_stock: Filter products that are in stock
        
    Returns:
        A list of products matching the filters
        
    Raises:
        404: If the tenant is not found
    """
    tenant_manager = TenantManager()
    product_manager = ProductManager()
    
    # Get tenant ID from slug
    tenant_obj = tenant_manager.get_tenant_by_slug(tenant)
    if not tenant_obj:
        raise HTTPException(
            status_code=404, detail=f"Tenant not found: {tenant}"
        )

    # Build filters
    filters = {}
    if category:
        filters["category"] = category
    if min_price is not None:
        filters["min_price"] = min_price
    if max_price is not None:
        filters["max_price"] = max_price
    if in_stock is not None:
        filters["in_stock"] = in_stock
    
    # Get products with filters
    products = product_manager.get_products_by_tenant(tenant_obj.id, filters)
    
    return {
        "products": [
            {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "sku": p.sku,
                "stock": p.stock,
                "categories": p.categories,
                "tenant_id": str(p.tenant_id),
            }
            for p in products
        ],
        "tenant": tenant,
        "count": len(products),
        "filters": filters
    }

@router.get("/{product_id}", response_model=ProductResponse, summary="Get Product by ID")
async def get_product(
    product_id: str = Path(..., description="The ID of the product to retrieve")
):
    """
    Get a single product by ID.
    
    Args:
        product_id: The unique identifier of the product
        
    Returns:
        The product details
        
    Raises:
        404: If the product is not found
    """
    product_manager = ProductManager()
    product = product_manager.get_product_by_id(product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found")
    
    return {
        "id": str(product.id),
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "sku": product.sku,
        "stock": product.stock,
        "categories": product.categories,
        "tenant_id": str(product.tenant_id),
    }

@router.post("/", response_model=ProductResponse, summary="Create Product")
async def create_product(
    product: ProductCreate = Body(..., description="The product to create")
):
    """
    Create a new product.
    
    Args:
        product: The product details
        
    Returns:
        The created product with its ID
        
    Raises:
        404: If the tenant is not found
        400: If a product with the same SKU already exists for this tenant
    """
    tenant_manager = TenantManager()
    product_manager = ProductManager()
    
    # Check if tenant exists
    tenant = tenant_manager.get_tenant_by_id(product.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant with id {product.tenant_id} not found")
    
    # Create product
    new_product = product_manager.create_product(
        tenant_id=product.tenant_id,
        name=product.name,
        description=product.description,
        price=product.price,
        sku=product.sku,
        stock=product.stock,
        categories=product.categories
    )
    
    return {
        "id": str(new_product.id),
        "name": new_product.name,
        "description": new_product.description,
        "price": new_product.price,
        "sku": new_product.sku,
        "stock": new_product.stock,
        "categories": new_product.categories,
        "tenant_id": str(new_product.tenant_id),
    }

@router.put("/{product_id}", response_model=ProductResponse, summary="Update Product")
async def update_product(
    product_id: str = Path(..., description="The ID of the product to update"),
    product_update: ProductUpdate = Body(..., description="The product updates")
):
    """
    Update an existing product.
    
    Args:
        product_id: The unique identifier of the product
        product_update: The fields to update
        
    Returns:
        The updated product
        
    Raises:
        404: If the product is not found
    """
    product_manager = ProductManager()
    
    # Check if product exists
    existing = product_manager.get_product_by_id(product_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found")
    
    # Prepare update data
    update_data = {}
    if product_update.name is not None:
        update_data["name"] = product_update.name
    if product_update.description is not None:
        update_data["description"] = product_update.description
    if product_update.price is not None:
        update_data["price"] = product_update.price
    if product_update.stock is not None:
        update_data["stock"] = product_update.stock
    if product_update.categories is not None:
        update_data["categories"] = product_update.categories
    
    # Update product
    updated_product = product_manager.update_product(product_id, update_data)
    
    return {
        "id": str(updated_product.id),
        "name": updated_product.name,
        "description": updated_product.description,
        "price": updated_product.price,
        "sku": updated_product.sku,
        "stock": updated_product.stock,
        "categories": updated_product.categories,
        "tenant_id": str(updated_product.tenant_id),
    }

@router.delete("/{product_id}", response_model=Dict[str, Any], summary="Delete Product")
async def delete_product(
    product_id: str = Path(..., description="The ID of the product to delete")
):
    """
    Delete a product.
    
    Args:
        product_id: The unique identifier of the product
        
    Returns:
        A confirmation message
        
    Raises:
        404: If the product is not found
    """
    product_manager = ProductManager()
    
    # Check if product exists
    existing = product_manager.get_product_by_id(product_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found")
    
    # Delete product
    product_manager.delete_product(product_id)
    
    return {
        "success": True,
        "message": f"Product {existing.name} deleted successfully"
    }