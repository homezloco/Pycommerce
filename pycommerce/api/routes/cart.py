"""
Cart API routes for PyCommerce SDK.

This module defines the FastAPI routes for cart operations.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends

from pycommerce.models.cart import Cart, CartItem, CartManager
from pycommerce.models.product import ProductManager

router = APIRouter()
logger = logging.getLogger("pycommerce.api.cart")

# Dependencies to get manager instances
_cart_manager = None
_product_manager = None

def set_cart_manager(manager: CartManager):
    """Set the CartManager instance to use in routes."""
    global _cart_manager
    _cart_manager = manager

def get_cart_manager() -> CartManager:
    """
    Get the CartManager instance.
    
    Returns:
        The CartManager instance
        
    Raises:
        HTTPException: If the CartManager is not initialized
    """
    if _cart_manager is None:
        logger.error("CartManager not initialized")
        raise HTTPException(
            status_code=500,
            detail="Cart service not available"
        )
    return _cart_manager

def get_product_manager() -> Optional[ProductManager]:
    """
    Get the ProductManager instance.
    
    Returns:
        The ProductManager instance or None if not initialized
    """
    return _product_manager


@router.post("", response_model=Cart)
async def create_cart(
    user_id: Optional[str] = None,
    cart_manager: CartManager = Depends(get_cart_manager)
):
    """
    Create a new cart.
    
    Args:
        user_id: Optional ID of the user who owns this cart
        
    Returns:
        The created cart
    """
    try:
        cart = cart_manager.create(user_id)
        logger.info(f"Created cart: {cart.id}")
        return cart
    except Exception as e:
        logger.error(f"Error creating cart: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/{cart_id}", response_model=Cart)
async def get_cart(
    cart_id: str,
    cart_manager: CartManager = Depends(get_cart_manager)
):
    """
    Get a cart by ID.
    
    Args:
        cart_id: The ID of the cart to get
        
    Returns:
        The cart
        
    Raises:
        HTTPException: If the cart is not found
    """
    try:
        return cart_manager.get(cart_id)
    except Exception as e:
        logger.error(f"Error getting cart {cart_id}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Cart not found: {cart_id}"
        )


@router.get("/user/{user_id}", response_model=Cart)
async def get_user_cart(
    user_id: str,
    cart_manager: CartManager = Depends(get_cart_manager)
):
    """
    Get a cart by user ID.
    
    Args:
        user_id: The ID of the user
        
    Returns:
        The user's cart
    """
    try:
        return cart_manager.get_user_cart(user_id)
    except Exception as e:
        logger.error(f"Error getting cart for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )


@router.post("/{cart_id}/items", response_model=Cart)
async def add_item_to_cart(
    cart_id: str,
    product_id: str,
    quantity: int = 1,
    cart_manager: CartManager = Depends(get_cart_manager)
):
    """
    Add an item to a cart.
    
    Args:
        cart_id: The ID of the cart
        product_id: The ID of the product to add
        quantity: The quantity to add
        
    Returns:
        The updated cart
        
    Raises:
        HTTPException: If the cart is not found or the item cannot be added
    """
    try:
        cart = cart_manager.add_item(cart_id, product_id, quantity)
        logger.info(f"Added item to cart {cart_id}: product {product_id}, quantity {quantity}")
        return cart
    except Exception as e:
        logger.error(f"Error adding item to cart {cart_id}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"An error occurred: {str(e)}"
        )


@router.put("/{cart_id}/items/{product_id}", response_model=Cart)
async def update_cart_item(
    cart_id: str,
    product_id: str,
    quantity: int,
    cart_manager: CartManager = Depends(get_cart_manager)
):
    """
    Update an item's quantity in a cart.
    
    Args:
        cart_id: The ID of the cart
        product_id: The ID of the product to update
        quantity: The new quantity
        
    Returns:
        The updated cart
        
    Raises:
        HTTPException: If the cart is not found or the item is not in the cart
    """
    try:
        cart = cart_manager.update_item(cart_id, product_id, quantity)
        logger.info(f"Updated item in cart {cart_id}: product {product_id}, quantity {quantity}")
        return cart
    except Exception as e:
        logger.error(f"Error updating item in cart {cart_id}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"An error occurred: {str(e)}"
        )


@router.delete("/{cart_id}/items/{product_id}", response_model=Cart)
async def remove_cart_item(
    cart_id: str,
    product_id: str,
    cart_manager: CartManager = Depends(get_cart_manager)
):
    """
    Remove an item from a cart.
    
    Args:
        cart_id: The ID of the cart
        product_id: The ID of the product to remove
        
    Returns:
        The updated cart
        
    Raises:
        HTTPException: If the cart is not found or the item is not in the cart
    """
    try:
        cart = cart_manager.remove_item(cart_id, product_id)
        logger.info(f"Removed item from cart {cart_id}: product {product_id}")
        return cart
    except Exception as e:
        logger.error(f"Error removing item from cart {cart_id}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"An error occurred: {str(e)}"
        )


@router.delete("/{cart_id}/items", response_model=Cart)
async def clear_cart(
    cart_id: str,
    cart_manager: CartManager = Depends(get_cart_manager)
):
    """
    Clear all items from a cart.
    
    Args:
        cart_id: The ID of the cart
        
    Returns:
        The cleared cart
        
    Raises:
        HTTPException: If the cart is not found
    """
    try:
        cart = cart_manager.clear(cart_id)
        logger.info(f"Cleared cart: {cart_id}")
        return cart
    except Exception as e:
        logger.error(f"Error clearing cart {cart_id}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Cart not found: {cart_id}"
        )


@router.get("/{cart_id}/totals")
async def get_cart_totals(
    cart_id: str,
    cart_manager: CartManager = Depends(get_cart_manager),
    product_manager: Optional[ProductManager] = Depends(get_product_manager)
):
    """
    Calculate totals for a cart.
    
    Args:
        cart_id: The ID of the cart
        
    Returns:
        Dictionary with subtotal, tax, and total
        
    Raises:
        HTTPException: If the cart is not found or totals cannot be calculated
    """
    try:
        if product_manager is None:
            logger.error("ProductManager not initialized")
            raise HTTPException(
                status_code=500,
                detail="Product service not available"
            )
        
        totals = cart_manager.calculate_totals(cart_id, product_manager)
        return totals
    except Exception as e:
        logger.error(f"Error calculating totals for cart {cart_id}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"An error occurred: {str(e)}"
        )
