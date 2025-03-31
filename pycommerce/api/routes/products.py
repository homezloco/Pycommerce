"""
Product API routes for PyCommerce SDK.

This module defines the FastAPI routes for product operations.
"""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, Depends

from pycommerce.models.product import Product, ProductManager

router = APIRouter()
logger = logging.getLogger("pycommerce.api.products")

# Dependency to get the ProductManager instance
_product_manager = None

def set_product_manager(manager: ProductManager):
    """Set the ProductManager instance to use in routes."""
    global _product_manager
    _product_manager = manager

def get_product_manager() -> ProductManager:
    """
    Get the ProductManager instance.
    
    Returns:
        The ProductManager instance
        
    Raises:
        HTTPException: If the ProductManager is not initialized
    """
    if _product_manager is None:
        logger.error("ProductManager not initialized")
        raise HTTPException(
            status_code=500,
            detail="Product service not available"
        )
    return _product_manager


@router.get("", response_model=List[Product])
async def list_products(
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None,
    product_manager: ProductManager = Depends(get_product_manager)
):
    """
    List products with optional filtering.
    
    Args:
        category: Filter by category
        min_price: Filter by minimum price
        max_price: Filter by maximum price
        in_stock: Filter by stock availability
        
    Returns:
        List of products matching the filters
    """
    try:
        products = product_manager.list(
            category=category,
            min_price=min_price,
            max_price=max_price,
            in_stock=in_stock
        )
        return products
    except Exception as e:
        logger.error(f"Error listing products: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/search", response_model=List[Product])
async def search_products(
    q: str = Query(..., min_length=1),
    product_manager: ProductManager = Depends(get_product_manager)
):
    """
    Search for products.
    
    Args:
        q: The search query
        
    Returns:
        List of products matching the search query
    """
    try:
        products = product_manager.search(q)
        return products
    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/{product_id}", response_model=Product)
async def get_product(
    product_id: str,
    product_manager: ProductManager = Depends(get_product_manager)
):
    """
    Get a product by ID.
    
    Args:
        product_id: The ID of the product to get
        
    Returns:
        The product
        
    Raises:
        HTTPException: If the product is not found
    """
    try:
        return product_manager.get(product_id)
    except Exception as e:
        logger.error(f"Error getting product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Product not found: {product_id}"
        )


@router.post("", response_model=Product)
async def create_product(
    product_data: dict,
    product_manager: ProductManager = Depends(get_product_manager)
):
    """
    Create a new product.
    
    Args:
        product_data: Dictionary containing product data
        
    Returns:
        The created product
        
    Raises:
        HTTPException: If product creation fails
    """
    try:
        product = product_manager.create(product_data)
        logger.info(f"Created product: {product.id}")
        return product
    except ValueError as e:
        logger.error(f"Validation error creating product: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid product data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )


@router.put("/{product_id}", response_model=Product)
async def update_product(
    product_id: str,
    product_data: dict,
    product_manager: ProductManager = Depends(get_product_manager)
):
    """
    Update a product.
    
    Args:
        product_id: The ID of the product to update
        product_data: Dictionary containing updated product data
        
    Returns:
        The updated product
        
    Raises:
        HTTPException: If the product is not found or update fails
    """
    try:
        product = product_manager.update(product_id, product_data)
        logger.info(f"Updated product: {product.id}")
        return product
    except ValueError as e:
        logger.error(f"Validation error updating product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid product data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error updating product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Product not found: {product_id}"
        )


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    product_manager: ProductManager = Depends(get_product_manager)
):
    """
    Delete a product.
    
    Args:
        product_id: The ID of the product to delete
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If the product is not found
    """
    try:
        product_manager.delete(product_id)
        logger.info(f"Deleted product: {product_id}")
        return {"message": "Product deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Product not found: {product_id}"
        )
