"""
Product API routes for PyCommerce SDK.

This module defines the FastAPI routes for product operations with comprehensive
documentation, proper validation, and optimized response handling.
"""

import logging
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, Depends, Request, Path, Body, status
from fastapi.responses import JSONResponse

from pycommerce.models.product import Product, ProductManager
# Import enhanced query optimizer functions
try:
    from pycommerce.services.enhanced_query_optimizer import (
        get_products_by_tenant, 
        get_product_with_details,
        invalidate_product_cache
    )
    ENHANCED_OPTIMIZER_AVAILABLE = True
except ImportError:
    logger = logging.getLogger("pycommerce.api.products")
    logger.warning("Enhanced query optimizer not available, using standard methods")
    ENHANCED_OPTIMIZER_AVAILABLE = False

router = APIRouter()
logger = logging.getLogger("pycommerce.api.products")

# Storage for tenant-specific product managers
_product_managers: Dict[str, ProductManager] = {}


def set_product_manager(manager: ProductManager):
    """
    Set the ProductManager instance to use in routes for the default tenant.
    
    Args:
        manager: The ProductManager instance
    """
    global _product_managers
    _product_managers["default"] = manager

def set_product_manager_func(get_manager_func):
    """
    Set a function that will be called to get the ProductManager for a tenant.
    
    Args:
        get_manager_func: A function that takes a tenant_id and returns a ProductManager
    """
    global _get_manager_func
    _get_manager_func = get_manager_func


def get_product_manager(tenant_id: str = None) -> ProductManager:
    """
    Get the ProductManager instance for a tenant.
    
    Args:
        tenant_id: The tenant ID (optional, uses default if not provided)
    
    Returns:
        The ProductManager instance
        
    Raises:
        HTTPException: If the ProductManager is not initialized for the tenant
    """
    # Use default tenant if not specified
    if tenant_id is None:
        tenant_id = "default"
        
    # Check if we have a manager for this tenant
    if tenant_id in _product_managers:
        return _product_managers[tenant_id]
    
    # Try to get manager using the function if available
    if "_get_manager_func" in globals() and globals()["_get_manager_func"] is not None:
        try:
            manager = globals()["_get_manager_func"](tenant_id)
            _product_managers[tenant_id] = manager
            return manager
        except Exception as e:
            logger.error(f"Error getting product manager for tenant {tenant_id}: {str(e)}")
    
    # Fallback to default manager
    if "default" in _product_managers:
        return _product_managers["default"]
        
    logger.error(f"ProductManager not initialized for tenant {tenant_id}")
    raise HTTPException(
        status_code=500,
        detail="Product service not available"
    )


async def get_tenant_id(request: Request) -> str:
    """
    Extract the tenant ID from the request.
    
    This function is meant to be used as a FastAPI dependency.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        The tenant ID
    """
    # Check for tenant ID in request state (set by middleware)
    if hasattr(request.state, "tenant_id"):
        return request.state.tenant_id
    
    # Check for tenant ID in headers
    tenant_id = request.headers.get("X-Tenant-ID")
    if tenant_id:
        return tenant_id
    
    # Extract tenant from host
    host = request.headers.get("host", "")
    if "." in host:
        subdomain = host.split(".")[0]
        # Could lookup tenant by subdomain here
        if subdomain != "www":
            return subdomain
    
    # Default tenant
    return "default"


@router.get("", response_model=List[Product], tags=["Products"], 
         summary="List products",
         responses={
             200: {"description": "List of products", "model": List[Product]},
             400: {"description": "Bad request"},
             401: {"description": "Unauthorized"},
             500: {"description": "Internal server error"}
         })
async def list_products(
    request: Request,
    category: Optional[str] = Query(None, description="Filter products by category name"),
    min_price: Optional[float] = Query(None, description="Filter products with price greater than or equal to this value", ge=0),
    max_price: Optional[float] = Query(None, description="Filter products with price less than or equal to this value", ge=0),
    in_stock: Optional[bool] = Query(None, description="Filter by products that are in stock (true) or out of stock (false)"),
    limit: int = Query(100, description="Maximum number of products to return", ge=1, le=1000),
    offset: int = Query(0, description="Pagination offset", ge=0),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    List products with optional filtering.
    
    Retrieves a list of products for the specified tenant with optional filtering
    by category, price range, and stock availability. The results are paginated
    using the limit and offset parameters.
    
    - **category**: Filter products by category name (optional)
    - **min_price**: Filter products with price greater than or equal to this value (optional)
    - **max_price**: Filter products with price less than or equal to this value (optional)
    - **in_stock**: Filter by products that are in stock (true) or out of stock (false) (optional)
    - **limit**: Maximum number of products to return (default: 100)
    - **offset**: Pagination offset (default: 0)
    - **tenant_id**: The tenant ID (derived from header, subdomain, or URL)
    
    Returns a list of products matching the filter criteria.
    """
    try:
        # Use enhanced query optimizer if available
        if ENHANCED_OPTIMIZER_AVAILABLE:
            logger.info(f"Using enhanced query optimizer for tenant {tenant_id}")
            result = get_products_by_tenant(
                tenant_id=tenant_id,
                category=category,
                min_price=min_price,
                max_price=max_price,
                in_stock=in_stock,
                limit=limit,
                offset=offset
            )
            return result.get("products", [])
        else:
            # Fall back to standard method
            logger.info(f"Using standard query method for tenant {tenant_id}")
            product_manager = get_product_manager(tenant_id)
            products = product_manager.list(
                category=category,
                min_price=min_price,
                max_price=max_price,
                in_stock=in_stock
            )
            return products
    except Exception as e:
        logger.error(f"Error listing products for tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/search", response_model=List[Product], tags=["Products"], 
         summary="Search products",
         responses={
             200: {"description": "List of products matching search query", "model": List[Product]},
             400: {"description": "Bad request"},
             401: {"description": "Unauthorized"},
             500: {"description": "Internal server error"}
         })
async def search_products(
    q: str = Query(..., min_length=1, description="Search query for product name, description, or SKU"),
    limit: int = Query(100, description="Maximum number of products to return", ge=1, le=1000),
    offset: int = Query(0, description="Pagination offset", ge=0),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Search for products by name, description, or SKU.
    
    Performs a text search across product attributes (name, description, and SKU)
    and returns matching products for the specified tenant. The search is case-insensitive
    and matches partial text.
    
    - **q**: Search query string (required, minimum length 1)
    - **limit**: Maximum number of products to return (default: 100)
    - **offset**: Pagination offset (default: 0)
    - **tenant_id**: The tenant ID (derived from header, subdomain, or URL)
    
    Returns a list of products matching the search query.
    """
    try:
        product_manager = get_product_manager(tenant_id)
        products = product_manager.search(q)
        return products
    except Exception as e:
        logger.error(f"Error searching products for tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/{product_id}", response_model=Product, tags=["Products"], 
         summary="Get product by ID",
         responses={
             200: {"description": "Product details", "model": Product},
             404: {"description": "Product not found"},
             500: {"description": "Internal server error"}
         })
async def get_product(
    product_id: str = Path(..., description="Unique identifier of the product to retrieve"),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Get detailed information about a specific product by its ID.
    
    Retrieves comprehensive product information including name, description,
    price, stock status, and category assignments. The product must belong to
    the specified tenant.
    
    - **product_id**: Unique identifier of the product (required)
    - **tenant_id**: The tenant ID (derived from header, subdomain, or URL)
    
    Returns the product details if found, or a 404 error if the product does not exist
    or does not belong to the specified tenant.
    """
    try:
        # Use enhanced query optimizer if available
        if ENHANCED_OPTIMIZER_AVAILABLE:
            logger.info(f"Using enhanced query optimizer to get product {product_id}")
            product = get_product_with_details(product_id)
            if product is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product not found: {product_id}"
                )
            return product
        else:
            # Fall back to standard method
            logger.info(f"Using standard query method to get product {product_id}")
            product_manager = get_product_manager(tenant_id)
            return product_manager.get(product_id)
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting product {product_id} for tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Product not found: {product_id}"
        )


@router.post("", response_model=Product, tags=["Products"], 
         summary="Create new product",
         status_code=201,
         responses={
             201: {"description": "Product created successfully", "model": Product},
             400: {"description": "Invalid product data"},
             401: {"description": "Unauthorized"},
             500: {"description": "Internal server error"}
         })
async def create_product(
    product_data: dict = Body(..., description="Product data including name, price, description, etc."),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Create a new product in the specified tenant's catalog.
    
    Creates a new product with the provided data and associates it with
    the specified tenant. The product data should include essential fields
    like name, price, and SKU, as well as optional fields like description,
    stock level, and category assignments.
    
    - **product_data**: Product data object (required) with the following fields:
      - **name**: Product name (required)
      - **price**: Product price (required)
      - **sku**: Stock keeping unit (required, must be unique per tenant)
      - **description**: Product description (optional)
      - **stock**: Quantity in stock (optional, defaults to 0)
      - **categories**: List of category IDs (optional)
      - **cost_price**: Cost price for profit calculation (optional)
      - **is_material**: Whether this is a material item (optional)
      - **is_labor**: Whether this represents labor (optional)
    - **tenant_id**: The tenant ID (derived from header, subdomain, or URL)
    
    Returns the created product with its assigned ID and creation timestamp.
    Returns a 400 error if the product data is invalid or the SKU is already in use.
    """
    try:
        product_manager = get_product_manager(tenant_id)
        product = product_manager.create(product_data)
        product_id = str(product.id)
        logger.info(f"Created product: {product_id} for tenant {tenant_id}")
        
        # Invalidate cache if using enhanced query optimizer
        if ENHANCED_OPTIMIZER_AVAILABLE:
            invalidate_product_cache(tenant_id=tenant_id)
            logger.info(f"Invalidated product cache for tenant {tenant_id}")
            
        return product
    except ValueError as e:
        logger.error(f"Validation error creating product for tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid product data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error creating product for tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )


@router.put("/{product_id}", response_model=Product, tags=["Products"], 
         summary="Update existing product",
         responses={
             200: {"description": "Product updated successfully", "model": Product},
             400: {"description": "Invalid product data"},
             401: {"description": "Unauthorized"},
             404: {"description": "Product not found"},
             500: {"description": "Internal server error"}
         })
async def update_product(
    product_id: str = Path(..., description="Unique identifier of the product to update"),
    product_data: dict = Body(..., description="Updated product data fields"),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Update an existing product with new values.
    
    Updates the specified product with the provided data. Only the fields
    included in the request body will be updated; other fields will remain
    unchanged. The product must belong to the specified tenant.
    
    - **product_id**: Unique identifier of the product to update (required)
    - **product_data**: Updated product data (required), which may include:
      - **name**: Product name
      - **price**: Product price
      - **sku**: Stock keeping unit (must be unique per tenant)
      - **description**: Product description
      - **stock**: Quantity in stock
      - **categories**: List of category IDs
      - **cost_price**: Cost price for profit calculation
      - **is_material**: Whether this is a material item
      - **is_labor**: Whether this represents labor
    - **tenant_id**: The tenant ID (derived from header, subdomain, or URL)
    
    Returns the updated product with all current values.
    Returns a 404 error if the product does not exist or does not belong to the tenant.
    Returns a 400 error if the updated data is invalid or the SKU conflicts with another product.
    """
    try:
        product_manager = get_product_manager(tenant_id)
        product = product_manager.update(product_id, product_data)
        logger.info(f"Updated product: {product.id} for tenant {tenant_id}")
        
        # Invalidate cache if using enhanced query optimizer
        if ENHANCED_OPTIMIZER_AVAILABLE:
            # Invalidate both tenant-wide cache and specific product cache
            invalidate_product_cache(tenant_id=tenant_id)
            invalidate_product_cache(product_id=product_id)
            logger.info(f"Invalidated cache for product {product_id} and tenant {tenant_id}")
            
        return product
    except ValueError as e:
        logger.error(f"Validation error updating product {product_id} for tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid product data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error updating product {product_id} for tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Product not found: {product_id}"
        )


@router.delete("/{product_id}", tags=["Products"], 
         summary="Delete product",
         responses={
             200: {"description": "Product deleted successfully", "content": {"application/json": {"example": {"message": "Product deleted successfully"}}}},
             401: {"description": "Unauthorized"},
             404: {"description": "Product not found"},
             500: {"description": "Internal server error"}
         })
async def delete_product(
    product_id: str = Path(..., description="Unique identifier of the product to delete"),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Permanently delete a product from the catalog.
    
    Deletes the specified product from the tenant's catalog. This operation cannot
    be undone, and all associated data will be permanently removed. The product
    must belong to the specified tenant.
    
    - **product_id**: Unique identifier of the product to delete (required)
    - **tenant_id**: The tenant ID (derived from header, subdomain, or URL)
    
    Returns a success message if the product was deleted successfully.
    Returns a 404 error if the product does not exist or does not belong to the tenant.
    """
    try:
        product_manager = get_product_manager(tenant_id)
        product_manager.delete(product_id)
        logger.info(f"Deleted product: {product_id} for tenant {tenant_id}")
        
        # Invalidate cache if using enhanced query optimizer
        if ENHANCED_OPTIMIZER_AVAILABLE:
            # Invalidate both tenant-wide cache and specific product cache
            invalidate_product_cache(tenant_id=tenant_id)
            invalidate_product_cache(product_id=product_id)
            logger.info(f"Invalidated cache for product {product_id} and tenant {tenant_id}")
            
        return {"message": "Product deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting product {product_id} for tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Product not found: {product_id}"
        )