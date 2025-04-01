"""
Product API routes for PyCommerce SDK.

This module defines the FastAPI routes for product operations.
"""

import logging
from typing import List, Optional, Dict
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, Depends, Request

from pycommerce.models.product import Product, ProductManager

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


@router.get("", response_model=List[Product])
async def list_products(
    request: Request,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    List products with optional filtering.
    
    Args:
        request: The FastAPI request object
        category: Filter by category
        min_price: Filter by minimum price
        max_price: Filter by maximum price
        in_stock: Filter by stock availability
        tenant_id: The tenant ID
        
    Returns:
        List of products matching the filters
    """
    try:
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


@router.get("/search", response_model=List[Product])
async def search_products(
    q: str = Query(..., min_length=1),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Search for products.
    
    Args:
        q: The search query
        tenant_id: The tenant ID
        
    Returns:
        List of products matching the search query
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


@router.get("/{product_id}", response_model=Product)
async def get_product(
    product_id: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Get a product by ID.
    
    Args:
        product_id: The ID of the product to get
        tenant_id: The tenant ID
        
    Returns:
        The product
        
    Raises:
        HTTPException: If the product is not found
    """
    try:
        product_manager = get_product_manager(tenant_id)
        return product_manager.get(product_id)
    except Exception as e:
        logger.error(f"Error getting product {product_id} for tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Product not found: {product_id}"
        )


@router.post("", response_model=Product)
async def create_product(
    product_data: dict,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Create a new product.
    
    Args:
        product_data: Dictionary containing product data
        tenant_id: The tenant ID
        
    Returns:
        The created product
        
    Raises:
        HTTPException: If product creation fails
    """
    try:
        product_manager = get_product_manager(tenant_id)
        product = product_manager.create(product_data)
        logger.info(f"Created product: {product.id} for tenant {tenant_id}")
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


@router.put("/{product_id}", response_model=Product)
async def update_product(
    product_id: str,
    product_data: dict,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Update a product.
    
    Args:
        product_id: The ID of the product to update
        product_data: Dictionary containing updated product data
        tenant_id: The tenant ID
        
    Returns:
        The updated product
        
    Raises:
        HTTPException: If the product is not found or update fails
    """
    try:
        product_manager = get_product_manager(tenant_id)
        product = product_manager.update(product_id, product_data)
        logger.info(f"Updated product: {product.id} for tenant {tenant_id}")
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


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Delete a product.
    
    Args:
        product_id: The ID of the product to delete
        tenant_id: The tenant ID
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If the product is not found
    """
    try:
        product_manager = get_product_manager(tenant_id)
        product_manager.delete(product_id)
        logger.info(f"Deleted product: {product_id} for tenant {tenant_id}")
        return {"message": "Product deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting product {product_id} for tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Product not found: {product_id}"
        )