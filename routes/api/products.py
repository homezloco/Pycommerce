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
@router.get("/", response_model=ProductsResponse, 
         summary="List Products",
         description="Retrieves a list of products for a specific tenant with filtering options",
         responses={
             200: {"description": "List of products retrieved successfully", "model": ProductsResponse},
             400: {"description": "Invalid filter parameters"},
             404: {"description": "Tenant not found"},
             500: {"description": "Internal server error"}
         })
async def list_products(
    tenant: str = Query(..., description="Tenant slug identifier"),
    category: Optional[str] = Query(None, description="Filter products by category name"),
    min_price: Optional[float] = Query(None, description="Filter products with price greater than or equal to this value"),
    max_price: Optional[float] = Query(None, description="Filter products with price less than or equal to this value"),
    in_stock: Optional[bool] = Query(None, description="When true, only show products with stock > 0")
):
    """
    Retrieve products for a tenant with comprehensive filtering options.
    
    This endpoint returns products for a specific tenant with support for multiple filters.
    You can filter products by category, price range, and stock availability. The API returns 
    a paginated list of products matching the criteria, along with count information
    and a summary of the applied filters.
    
    - **tenant**: Required tenant slug identifier (string)
    - **category**: Optional category name to filter products by (string)
    - **min_price**: Optional minimum price threshold (number)
    - **max_price**: Optional maximum price threshold (number)
    - **in_stock**: Optional filter to show only products with available stock (boolean)
    
    Returns a structured response containing matching products, tenant identifier, 
    total count, and applied filters. If the tenant does not exist, a 404 error is returned.
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

@router.get("/{product_id}", response_model=ProductResponse, 
         summary="Get Product by ID",
         description="Retrieves detailed information about a specific product",
         responses={
             200: {"description": "Product details retrieved successfully", "model": ProductResponse},
             400: {"description": "Invalid product ID format"},
             404: {"description": "Product not found"},
             500: {"description": "Internal server error"}
         })
async def get_product(
    product_id: str = Path(..., description="The unique UUID of the product to retrieve")
):
    """
    Retrieve detailed information about a specific product by its unique ID.
    
    This endpoint returns comprehensive details about a specific product, including its name,
    description, price, SKU, stock level, and associated categories. The product ID should 
    be provided as a UUID string.
    
    - **product_id**: The unique identifier of the product (UUID format)
    
    Returns the product details if found, including associated tenant information.
    If the product does not exist or has been deleted, a 404 error is returned.
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

@router.post("/", response_model=ProductResponse, 
         summary="Create Product",
         description="Creates a new product in the specified tenant's catalog",
         status_code=201,
         responses={
             201: {"description": "Product created successfully", "model": ProductResponse},
             400: {"description": "Invalid request or product with same SKU already exists for this tenant"},
             401: {"description": "Unauthorized - requires proper authentication"},
             404: {"description": "Tenant not found"},
             500: {"description": "Internal server error"}
         })
async def create_product(
    product: ProductCreate = Body(..., description="The complete product details to create")
):
    """
    Create a new product in the inventory.
    
    This endpoint creates a new product in the specified tenant's catalog with the provided details. 
    Each product must have a unique SKU within its tenant. The product will be immediately available 
    for purchase if stock is greater than zero.
    
    - **product**: Complete product details including:
      - **name**: Product display name (required)
      - **description**: Detailed product description (optional)
      - **price**: Product price in the store's currency (required)
      - **sku**: Stock keeping unit - must be unique per tenant (required)
      - **stock**: Available inventory quantity (default: 0)
      - **categories**: List of category names for the product (optional)
      - **tenant_id**: ID of the tenant this product belongs to (required)
    
    Returns the created product with all fields including the generated UUID.
    Returns a 400 error if a product with the same SKU already exists for this tenant.
    Returns a 404 error if the specified tenant does not exist.
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

@router.put("/{product_id}", response_model=ProductResponse, 
         summary="Update Product",
         description="Updates an existing product's information",
         responses={
             200: {"description": "Product updated successfully", "model": ProductResponse},
             400: {"description": "Invalid product ID format or invalid data"},
             401: {"description": "Unauthorized - requires proper authentication"},
             404: {"description": "Product not found"},
             500: {"description": "Internal server error"}
         })
async def update_product(
    product_id: str = Path(..., description="The unique UUID of the product to update"),
    product_update: ProductUpdate = Body(..., description="The product fields to update (partial updates supported)")
):
    """
    Update an existing product's information.
    
    This endpoint allows for partial updates to product information. Only the fields
    provided in the request body will be updated; other fields will remain unchanged.
    The product's SKU and tenant association cannot be modified after creation.
    
    - **product_id**: The unique identifier of the product to update (UUID format)
    - **product_update**: The fields to update, which can include:
      - **name**: New product display name (optional)
      - **description**: New product description (optional)
      - **price**: New product price (optional)
      - **stock**: Updated inventory quantity (optional)
      - **categories**: New list of category associations (optional)
    
    Returns the complete updated product with all fields.
    Returns a 404 error if no product exists with the provided ID.
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

@router.delete("/{product_id}", 
         summary="Delete Product",
         description="Permanently removes a product from the catalog",
         responses={
             200: {"description": "Product deleted successfully", "content": {"application/json": {"example": {"success": True, "message": "Product Example Product deleted successfully"}}}},
             400: {"description": "Invalid product ID format"},
             401: {"description": "Unauthorized - requires proper authentication"},
             404: {"description": "Product not found"},
             500: {"description": "Internal server error"}
         })
async def delete_product(
    product_id: str = Path(..., description="The unique UUID of the product to delete")
):
    """
    Permanently delete a product from the catalog.
    
    This endpoint permanently removes a product from the database. This will affect
    the product's availability for purchase and will remove it from all category listings.
    However, the product will still be preserved in historical orders. This operation 
    cannot be undone.
    
    - **product_id**: The unique identifier of the product to delete (UUID format)
    
    Returns a success message if the product was deleted successfully.
    Returns a 404 error if no product exists with the provided ID.
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