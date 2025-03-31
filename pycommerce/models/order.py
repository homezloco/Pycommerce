"""
Order-related models and management.

This module defines the Order model and OrderManager class for
managing orders in the PyCommerce SDK.
"""

import logging
from typing import Dict, List, Optional, Union, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

logger = logging.getLogger("pycommerce.models.order")


class OrderStatus(str, Enum):
    """
    Possible statuses for an order.
    """
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class OrderItem(BaseModel):
    """
    Represents an item in an order.
    """
    product_id: UUID
    product_name: str
    product_sku: str
    quantity: int
    unit_price: float
    total_price: float
    
    @validator('quantity')
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v
    
    @validator('unit_price', 'total_price')
    def price_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError('Price must be non-negative')
        return v


class ShippingAddress(BaseModel):
    """
    Represents a shipping address.
    """
    first_name: str
    last_name: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str
    phone: Optional[str] = None


class Order(BaseModel):
    """
    Represents an order.
    """
    id: UUID = Field(default_factory=uuid4)
    user_id: Optional[UUID] = None
    items: List[OrderItem] = Field(default_factory=list)
    subtotal: float
    tax: float
    shipping_cost: float = 0.0
    total: float
    status: OrderStatus = OrderStatus.PENDING
    shipping_address: Optional[ShippingAddress] = None
    payment_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @validator('subtotal', 'tax', 'shipping_cost', 'total')
    def price_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError('Amount must be non-negative')
        return v


class OrderManager:
    """
    Manages order operations.
    """
    
    def __init__(self):
        """Initialize a new OrderManager."""
        self._orders: Dict[UUID, Order] = {}
        self._user_orders: Dict[UUID, List[UUID]] = {}  # Maps user_id to list of order_ids
    
    def create_from_cart(self, cart_id: Union[UUID, str], 
                        product_manager, cart_manager,
                        shipping_address: Optional[Dict[str, Any]] = None) -> Order:
        """
        Create a new order from a cart.
        
        Args:
            cart_id: The ID of the cart to convert to an order
            product_manager: A ProductManager instance to look up products
            cart_manager: A CartManager instance to get the cart
            shipping_address: Optional shipping address for the order
            
        Returns:
            The created order
            
        Raises:
            OrderError: If order creation fails
            CartError: If the cart is not found
            ProductError: If a product in the cart is not found
        """
        from pycommerce.core.exceptions import OrderError
        
        # Get the cart first
        cart = cart_manager.get(cart_id)
        
        # Calculate totals
        totals = cart_manager.calculate_totals(cart_id, product_manager)
        
        # Create order items
        items = []
        for cart_item in cart.items:
            product = product_manager.get(cart_item.product_id)
            item_total = product.price * cart_item.quantity
            
            items.append(OrderItem(
                product_id=product.id,
                product_name=product.name,
                product_sku=product.sku,
                quantity=cart_item.quantity,
                unit_price=product.price,
                total_price=item_total
            ))
        
        # Create shipping address if provided
        shipping_addr = None
        if shipping_address:
            try:
                shipping_addr = ShippingAddress(**shipping_address)
            except ValueError as e:
                raise OrderError(f"Invalid shipping address: {str(e)}")
        
        # Create the order
        try:
            order = Order(
                user_id=cart.user_id,
                items=items,
                subtotal=totals["subtotal"],
                tax=totals["tax"],
                total=totals["total"],
                shipping_address=shipping_addr
            )
            
            self._orders[order.id] = order
            
            # Associate order with user if available
            if order.user_id:
                if order.user_id not in self._user_orders:
                    self._user_orders[order.user_id] = []
                self._user_orders[order.user_id].append(order.id)
            
            logger.debug(f"Created order: {order.id}")
            return order
        
        except ValueError as e:
            raise OrderError(f"Failed to create order: {str(e)}")
    
    def get(self, order_id: Union[UUID, str]) -> Order:
        """
        Get an order by ID.
        
        Args:
            order_id: The ID of the order to get
            
        Returns:
            The order
            
        Raises:
            OrderError: If the order is not found
        """
        from pycommerce.core.exceptions import OrderError
        
        # Convert string ID to UUID if needed
        if isinstance(order_id, str):
            try:
                order_id = UUID(order_id)
            except ValueError:
                raise OrderError(f"Invalid order ID: {order_id}")
        
        if order_id not in self._orders:
            raise OrderError(f"Order not found: {order_id}")
        
        return self._orders[order_id]
    
    def list(self, user_id: Optional[Union[UUID, str]] = None,
            status: Optional[OrderStatus] = None) -> List[Order]:
        """
        List orders with optional filtering.
        
        Args:
            user_id: Filter by user ID
            status: Filter by order status
            
        Returns:
            List of orders matching the filters
        """
        # Convert user_id to UUID if needed
        if user_id and isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                logger.warning(f"Invalid user ID for order filtering: {user_id}")
                return []
        
        # Get orders
        if user_id and user_id in self._user_orders:
            # Get orders for specific user
            orders = [self._orders[order_id] for order_id in self._user_orders[user_id]]
        else:
            # Get all orders
            orders = list(self._orders.values())
        
        # Apply status filter
        if status:
            orders = [order for order in orders if order.status == status]
        
        return orders
    
    def update_status(self, order_id: Union[UUID, str], 
                     status: OrderStatus) -> Order:
        """
        Update an order's status.
        
        Args:
            order_id: The ID of the order
            status: The new status
            
        Returns:
            The updated order
            
        Raises:
            OrderError: If the order is not found
        """
        # Get the order first
        order = self.get(order_id)
        
        # Update status
        order.status = status
        order.updated_at = datetime.now()
        
        logger.debug(f"Updated order {order.id} status to {status}")
        return order
    
    def update_payment(self, order_id: Union[UUID, str],
                      payment_id: str) -> Order:
        """
        Update an order with payment information.
        
        Args:
            order_id: The ID of the order
            payment_id: The payment reference ID
            
        Returns:
            The updated order
            
        Raises:
            OrderError: If the order is not found
        """
        # Get the order first
        order = self.get(order_id)
        
        # Update payment info
        order.payment_id = payment_id
        order.status = OrderStatus.PAID
        order.updated_at = datetime.now()
        
        logger.debug(f"Updated order {order.id} with payment ID {payment_id}")
        return order
    
    def cancel(self, order_id: Union[UUID, str]) -> Order:
        """
        Cancel an order.
        
        Args:
            order_id: The ID of the order
            
        Returns:
            The updated order
            
        Raises:
            OrderError: If the order is not found or cannot be cancelled
        """
        from pycommerce.core.exceptions import OrderError
        
        # Get the order first
        order = self.get(order_id)
        
        # Check if order can be cancelled
        if order.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            raise OrderError(f"Cannot cancel order in {order.status} status")
        
        # Update status
        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.now()
        
        logger.debug(f"Cancelled order: {order.id}")
        return order
