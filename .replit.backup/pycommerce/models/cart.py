"""
Cart-related models and management.

This module defines the Cart model and CartManager class for
managing shopping carts in the PyCommerce SDK.
"""

import logging
from typing import Dict, List, Optional, Union, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator
from datetime import datetime

from pycommerce.models.product import Product

logger = logging.getLogger("pycommerce.models.cart")


class CartItem(BaseModel):
    """
    Represents an item in a shopping cart.
    """
    product_id: UUID
    quantity: int
    added_at: datetime = Field(default_factory=datetime.now)
    
    @validator('quantity')
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v


class Cart(BaseModel):
    """
    Represents a shopping cart.
    """
    id: UUID = Field(default_factory=uuid4)
    user_id: Optional[UUID] = None
    items: List[CartItem] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class CartManager:
    """
    Manages cart operations.
    """
    
    def __init__(self):
        """Initialize a new CartManager."""
        self._carts: Dict[UUID, Cart] = {}
        self._user_carts: Dict[UUID, UUID] = {}  # Maps user_id to cart_id
    
    def create(self, user_id: Optional[UUID] = None) -> Cart:
        """
        Create a new cart.
        
        Args:
            user_id: Optional ID of the user who owns this cart
            
        Returns:
            The created cart
        """
        cart = Cart(user_id=user_id)
        self._carts[cart.id] = cart
        
        # Associate cart with user if provided
        if user_id:
            self._user_carts[user_id] = cart.id
        
        logger.debug(f"Created cart: {cart.id}")
        return cart
    
    def get(self, cart_id: Union[UUID, str]) -> Cart:
        """
        Get a cart by ID.
        
        Args:
            cart_id: The ID of the cart to get
            
        Returns:
            The cart
            
        Raises:
            CartError: If the cart is not found
        """
        from pycommerce.core.exceptions import CartError
        
        # Convert string ID to UUID if needed
        if isinstance(cart_id, str):
            try:
                cart_id = UUID(cart_id)
            except ValueError:
                raise CartError(f"Invalid cart ID: {cart_id}")
        
        if cart_id not in self._carts:
            raise CartError(f"Cart not found: {cart_id}")
        
        return self._carts[cart_id]
    
    def get_user_cart(self, user_id: Union[UUID, str]) -> Cart:
        """
        Get a cart by user ID.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            The user's cart
            
        Raises:
            CartError: If the user has no cart
        """
        from pycommerce.core.exceptions import CartError
        
        # Convert string ID to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                raise CartError(f"Invalid user ID: {user_id}")
        
        if user_id not in self._user_carts:
            # Create a new cart for this user
            return self.create(user_id)
        
        return self.get(self._user_carts[user_id])
    
    def add_item(self, cart_id: Union[UUID, str], 
                product_id: Union[UUID, str], 
                quantity: int = 1) -> Cart:
        """
        Add an item to a cart.
        
        Args:
            cart_id: The ID of the cart
            product_id: The ID of the product to add
            quantity: The quantity to add
            
        Returns:
            The updated cart
            
        Raises:
            CartError: If the cart is not found or the item cannot be added
            ProductError: If the product is not found
        """
        from pycommerce.core.exceptions import CartError, ProductError
        
        # Get the cart first
        cart = self.get(cart_id)
        
        # Convert product_id to UUID if needed
        if isinstance(product_id, str):
            try:
                product_id = UUID(product_id)
            except ValueError:
                raise ProductError(f"Invalid product ID: {product_id}")
        
        # Check if the product is already in the cart
        for item in cart.items:
            if item.product_id == product_id:
                # Update quantity
                item.quantity += quantity
                cart.updated_at = datetime.now()
                logger.debug(f"Updated item quantity in cart {cart.id}: product {product_id}, new quantity {item.quantity}")
                return cart
        
        # Add new item
        try:
            cart.items.append(CartItem(product_id=product_id, quantity=quantity))
            cart.updated_at = datetime.now()
            logger.debug(f"Added item to cart {cart.id}: product {product_id}, quantity {quantity}")
            return cart
        except ValueError as e:
            raise CartError(f"Failed to add item: {str(e)}")
    
    def update_item(self, cart_id: Union[UUID, str],
                   product_id: Union[UUID, str],
                   quantity: int) -> Cart:
        """
        Update an item's quantity in a cart.
        
        Args:
            cart_id: The ID of the cart
            product_id: The ID of the product to update
            quantity: The new quantity
            
        Returns:
            The updated cart
            
        Raises:
            CartError: If the cart is not found or the item is not in the cart
        """
        from pycommerce.core.exceptions import CartError
        
        # Get the cart first
        cart = self.get(cart_id)
        
        # Convert product_id to UUID if needed
        if isinstance(product_id, str):
            try:
                product_id = UUID(product_id)
            except ValueError:
                raise CartError(f"Invalid product ID: {product_id}")
        
        # Find and update the item
        for i, item in enumerate(cart.items):
            if item.product_id == product_id:
                if quantity <= 0:
                    # Remove the item
                    cart.items.pop(i)
                    logger.debug(f"Removed item from cart {cart.id}: product {product_id}")
                else:
                    # Update quantity
                    cart.items[i].quantity = quantity
                    logger.debug(f"Updated item in cart {cart.id}: product {product_id}, quantity {quantity}")
                
                cart.updated_at = datetime.now()
                return cart
        
        raise CartError(f"Item not found in cart: product {product_id}")
    
    def remove_item(self, cart_id: Union[UUID, str],
                   product_id: Union[UUID, str]) -> Cart:
        """
        Remove an item from a cart.
        
        Args:
            cart_id: The ID of the cart
            product_id: The ID of the product to remove
            
        Returns:
            The updated cart
            
        Raises:
            CartError: If the cart is not found or the item is not in the cart
        """
        return self.update_item(cart_id, product_id, 0)
    
    def clear(self, cart_id: Union[UUID, str]) -> Cart:
        """
        Clear all items from a cart.
        
        Args:
            cart_id: The ID of the cart
            
        Returns:
            The cleared cart
            
        Raises:
            CartError: If the cart is not found
        """
        # Get the cart first
        cart = self.get(cart_id)
        
        # Clear items
        cart.items = []
        cart.updated_at = datetime.now()
        
        logger.debug(f"Cleared cart: {cart.id}")
        return cart
    
    def delete(self, cart_id: Union[UUID, str]) -> None:
        """
        Delete a cart.
        
        Args:
            cart_id: The ID of the cart to delete
            
        Raises:
            CartError: If the cart is not found
        """
        # Get the cart first (this will validate the ID)
        cart = self.get(cart_id)
        
        # Remove from user index if associated with a user
        if cart.user_id and cart.user_id in self._user_carts:
            del self._user_carts[cart.user_id]
        
        # Remove the cart
        del self._carts[cart.id]
        
        logger.debug(f"Deleted cart: {cart.id}")
    
    def calculate_totals(self, cart_id: Union[UUID, str], 
                         product_manager) -> Dict[str, float]:
        """
        Calculate totals for a cart.
        
        Args:
            cart_id: The ID of the cart
            product_manager: A ProductManager instance to look up product prices
            
        Returns:
            Dictionary with subtotal, tax, and total
            
        Raises:
            CartError: If the cart is not found
            ProductError: If a product in the cart is not found
        """
        # Get the cart first
        cart = self.get(cart_id)
        
        subtotal = 0.0
        
        # Calculate subtotal
        for item in cart.items:
            product = product_manager.get(item.product_id)
            subtotal += product.price * item.quantity
        
        # Calculate tax (simple 10% example)
        tax = subtotal * 0.1
        
        # Calculate total
        total = subtotal + tax
        
        return {
            "subtotal": round(subtotal, 2),
            "tax": round(tax, 2),
            "total": round(total, 2)
        }
