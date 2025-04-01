"""
Checkout API routes for PyCommerce SDK.

This module defines the FastAPI routes for checkout and order operations.
"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends

from pycommerce.models.order import Order, OrderStatus, OrderManager
from pycommerce.models.cart import CartManager
from pycommerce.models.product import ProductManager
from pycommerce.core.plugin import PluginManager

router = APIRouter()
logger = logging.getLogger("pycommerce.api.checkout")

# Storage for tenant-specific order managers
_order_managers = {}
_cart_manager = None
_product_manager = None
_plugin_manager = None

def set_order_manager(manager: OrderManager):
    """Set the OrderManager instance to use in routes for the default tenant."""
    global _order_managers
    _order_managers["default"] = manager

def set_order_manager_func(get_manager_func):
    """
    Set a function that will be called to get the OrderManager for a tenant.
    
    Args:
        get_manager_func: A function that takes a tenant_id and returns an OrderManager
    """
    global _get_manager_func
    _get_manager_func = get_manager_func

def get_order_manager(tenant_id: str = None) -> OrderManager:
    """
    Get the OrderManager instance for a tenant.
    
    Args:
        tenant_id: The tenant ID (optional, uses default if not provided)
    
    Returns:
        The OrderManager instance
        
    Raises:
        HTTPException: If the OrderManager is not initialized for the tenant
    """
    # Use default tenant if not specified
    if tenant_id is None:
        tenant_id = "default"
        
    # Check if we have a manager for this tenant
    if tenant_id in _order_managers:
        return _order_managers[tenant_id]
    
    # Try to get manager using the function if available
    if "_get_manager_func" in globals() and globals()["_get_manager_func"] is not None:
        try:
            manager = globals()["_get_manager_func"](tenant_id)
            _order_managers[tenant_id] = manager
            return manager
        except Exception as e:
            logger.error(f"Error getting order manager for tenant {tenant_id}: {str(e)}")
    
    # Fallback to default manager
    if "default" in _order_managers:
        return _order_managers["default"]
        
    logger.error(f"OrderManager not initialized for tenant {tenant_id}")
    raise HTTPException(
        status_code=500,
        detail="Order service not available"
    )

def get_cart_manager() -> Optional[CartManager]:
    """
    Get the CartManager instance.
    
    Returns:
        The CartManager instance or None if not initialized
    """
    return _cart_manager

def get_product_manager() -> Optional[ProductManager]:
    """
    Get the ProductManager instance.
    
    Returns:
        The ProductManager instance or None if not initialized
    """
    return _product_manager

def get_plugin_manager() -> Optional[PluginManager]:
    """
    Get the PluginManager instance.
    
    Returns:
        The PluginManager instance or None if not initialized
    """
    return _plugin_manager


@router.post("/orders", response_model=Order)
async def create_order(
    cart_id: str,
    shipping_address: Dict[str, Any],
    order_manager: OrderManager = Depends(get_order_manager),
    cart_manager: Optional[CartManager] = Depends(get_cart_manager),
    product_manager: Optional[ProductManager] = Depends(get_product_manager)
):
    """
    Create a new order from a cart.
    
    Args:
        cart_id: The ID of the cart to convert to an order
        shipping_address: Shipping address for the order
        
    Returns:
        The created order
        
    Raises:
        HTTPException: If order creation fails
    """
    try:
        if cart_manager is None:
            logger.error("CartManager not initialized")
            raise HTTPException(
                status_code=500,
                detail="Cart service not available"
            )
        
        if product_manager is None:
            logger.error("ProductManager not initialized")
            raise HTTPException(
                status_code=500,
                detail="Product service not available"
            )
        
        order = order_manager.create_from_cart(
            cart_id, 
            product_manager,
            cart_manager,
            shipping_address
        )
        
        logger.info(f"Created order: {order.id}")
        return order
    
    except Exception as e:
        logger.error(f"Error creating order from cart {cart_id}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/orders/{order_id}", response_model=Order)
async def get_order(
    order_id: str,
    order_manager: OrderManager = Depends(get_order_manager)
):
    """
    Get an order by ID.
    
    Args:
        order_id: The ID of the order to get
        
    Returns:
        The order
        
    Raises:
        HTTPException: If the order is not found
    """
    try:
        return order_manager.get(order_id)
    except Exception as e:
        logger.error(f"Error getting order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Order not found: {order_id}"
        )


@router.get("/orders", response_model=List[Order])
async def list_orders(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    order_manager: OrderManager = Depends(get_order_manager)
):
    """
    List orders with optional filtering.
    
    Args:
        user_id: Filter by user ID
        status: Filter by order status
        
    Returns:
        List of orders matching the filters
    """
    try:
        # Convert status string to enum if provided
        order_status = None
        if status:
            try:
                order_status = OrderStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid order status: {status}"
                )
        
        orders = order_manager.list(user_id, order_status)
        return orders
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing orders: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )


@router.put("/orders/{order_id}/status", response_model=Order)
async def update_order_status(
    order_id: str,
    status: str,
    order_manager: OrderManager = Depends(get_order_manager)
):
    """
    Update an order's status.
    
    Args:
        order_id: The ID of the order
        status: The new status
        
    Returns:
        The updated order
        
    Raises:
        HTTPException: If the order is not found or status is invalid
    """
    try:
        # Convert status string to enum
        try:
            order_status = OrderStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid order status: {status}"
            )
        
        order = order_manager.update_status(order_id, order_status)
        logger.info(f"Updated order {order_id} status to {status}")
        return order
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating order {order_id} status: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Order not found: {order_id}"
        )


@router.post("/orders/{order_id}/payment", response_model=Order)
async def process_payment(
    order_id: str,
    payment_data: Dict[str, Any],
    order_manager: OrderManager = Depends(get_order_manager),
    plugin_manager: Optional[PluginManager] = Depends(get_plugin_manager)
):
    """
    Process payment for an order.
    
    Args:
        order_id: The ID of the order
        payment_data: Payment details including:
            - plugin: Name of the payment plugin to use
            - ... other plugin-specific details
        
    Returns:
        The updated order
        
    Raises:
        HTTPException: If payment processing fails
    """
    try:
        # Ensure plugin manager is available
        if plugin_manager is None:
            logger.error("PluginManager not initialized")
            raise HTTPException(
                status_code=500,
                detail="Plugin service not available"
            )
        
        # Get the payment plugin
        plugin_name = payment_data.get("plugin")
        if not plugin_name:
            raise HTTPException(
                status_code=400,
                detail="Payment plugin not specified"
            )
        
        try:
            plugin = plugin_manager.get(plugin_name)
        except Exception as e:
            logger.error(f"Error getting payment plugin {plugin_name}: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Payment plugin not found: {plugin_name}"
            )
        
        # Get the order
        order = order_manager.get(order_id)
        
        # Process payment
        payment_result = await plugin.process_payment(order.id, payment_data)
        
        # Update order with payment info
        order = order_manager.update_payment(order_id, payment_result["payment_id"])
        
        logger.info(f"Processed payment for order {order_id}")
        return order
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing payment for order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Payment processing failed: {str(e)}"
        )


@router.post("/orders/{order_id}/cancel", response_model=Order)
async def cancel_order(
    order_id: str,
    order_manager: OrderManager = Depends(get_order_manager)
):
    """
    Cancel an order.
    
    Args:
        order_id: The ID of the order to cancel
        
    Returns:
        The cancelled order
        
    Raises:
        HTTPException: If the order is not found or cannot be cancelled
    """
    try:
        order = order_manager.cancel(order_id)
        logger.info(f"Cancelled order: {order_id}")
        return order
    except Exception as e:
        logger.error(f"Error cancelling order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel order: {str(e)}"
        )
