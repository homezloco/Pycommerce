"""
Checkout API routes for PyCommerce SDK.

This module defines the FastAPI routes for checkout and order operations.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request

from pycommerce.models.order import Order, OrderStatus, OrderManager
from pycommerce.models.cart import CartManager
from pycommerce.models.product import ProductManager
from pycommerce.core.plugin import PluginManager
from pycommerce.services.mail_service import get_email_service, init_email_service, EmailConfig

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


from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class OrderResponse(BaseModel):
    id: str
    status: str
    total: float
    items: Optional[List[Dict[str, Any]]] = None
    customer_id: Optional[str] = None

    class Config:
        orm_mode = True

@router.post("/orders", response_model=OrderResponse)
async def create_order(
    request: Request,
    cart_id: str,
    shipping_address: Dict[str, Any],
    customer_email: Optional[str] = None,
    order_manager: OrderManager = Depends(get_order_manager),
    cart_manager: Optional[CartManager] = Depends(get_cart_manager),
    product_manager: Optional[ProductManager] = Depends(get_product_manager),
    plugin_manager: Optional[PluginManager] = Depends(get_plugin_manager)
):
    """
    Create a new order from a cart.

    Args:
        request: The FastAPI request object
        cart_id: The ID of the cart to convert to an order
        shipping_address: Shipping address for the order
        customer_email: Customer email for order confirmation (optional)

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

        # Create the order
        order = order_manager.create_from_cart(
            cart_id, 
            product_manager,
            cart_manager,
            shipping_address
        )

        # Get email from shipping address if not provided
        if not customer_email and shipping_address and "email" in shipping_address:
            customer_email = shipping_address["email"]

        # Send order confirmation email if email is available
        if customer_email:
            # Try to initialize email service if needed
            email_service = get_email_service()
            if email_service is None:
                # Initialize with default settings or environment variables
                email_config = EmailConfig(
                    smtp_host=os.environ.get("SMTP_HOST", "smtp.gmail.com"),
                    smtp_port=int(os.environ.get("SMTP_PORT", "587")),
                    smtp_username=os.environ.get("SMTP_USERNAME"),
                    smtp_password=os.environ.get("SMTP_PASSWORD"),
                    default_sender=os.environ.get("SMTP_SENDER", "noreply@pycommerce.example.com"),
                    enabled=bool(os.environ.get("SMTP_ENABLED", "False").lower() == "true")
                )
                email_service = init_email_service(email_config)

                # Enable test mode if credentials are missing
                if not email_config.enabled:
                    email_service.enable_test_mode()
                    logger.info("Email service running in test mode (no emails will be sent)")

            # Get store information (tenant) for the email
            store_name = "PyCommerce Store"
            store_url = str(request.base_url)
            store_logo_url = None
            contact_email = os.environ.get("CONTACT_EMAIL", email_service.config.default_sender)

            # Try to get tenant information if plugin manager is available
            if plugin_manager:
                try:
                    tenant_plugin = plugin_manager.get("tenant")
                    if tenant_plugin:
                        tenant = tenant_plugin.get_current_tenant()
                        if tenant:
                            store_name = tenant.name
                            # Use tenant domain if available, otherwise use request base URL
                            if tenant.domain:
                                store_url = f"https://{tenant.domain}"
                            # Get logo URL from theme settings if available
                            if hasattr(tenant, "settings") and tenant.settings and "logo_url" in tenant.settings:
                                store_logo_url = tenant.settings["logo_url"]
                except Exception as e:
                    logger.warning(f"Error getting tenant info for email: {str(e)}")

            # Send the confirmation email
            try:
                email_sent = email_service.send_order_confirmation(
                    order=order,
                    to_email=customer_email,
                    store_name=store_name,
                    store_url=store_url,
                    store_logo_url=store_logo_url,
                    contact_email=contact_email
                )

                if email_sent:
                    logger.info(f"Order confirmation email sent to {customer_email} for order {order.id}")
                else:
                    logger.warning(f"Failed to send order confirmation email to {customer_email} for order {order.id}")

            except Exception as e:
                logger.error(f"Error sending order confirmation email: {str(e)}")

        logger.info(f"Created order: {order.id}")
        return order

    except Exception as e:
        logger.error(f"Error creating order from cart {cart_id}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/orders/{order_id}", response_model=None)
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
        order = order_manager.get(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Convert order to dictionary for API response
        if hasattr(order, "to_dict"):
            return order.to_dict()
        else:
            # Fallback to dictionary serialization
            from pydantic import BaseModel
            from datetime import datetime

            class OrderResponse(BaseModel):
                id: str
                status: str
                total: float
                created_at: datetime
                customer_name: str = None
                customer_email: str = None

                class Config:
                    from_attributes = True

            return OrderResponse.model_validate(order).model_dump()
    except Exception as e:
        logger.error(f"Error getting order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Order not found: {order_id}"
        )


@router.get("/orders", response_model=None)
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
        
        # Convert orders to a serializable format
        serialized_orders = []
        for order in orders:
            if hasattr(order, "to_dict"):
                serialized_orders.append(order.to_dict())
            else:
                # Basic serialization if to_dict is not available
                order_dict = {
                    "id": str(order.id),
                    "status": order.status,
                    "total": float(order.total),
                    "created_at": order.created_at.isoformat() if hasattr(order, "created_at") else None,
                    "customer_name": getattr(order, "customer_name", None),
                    "customer_email": getattr(order, "customer_email", None)
                }
                serialized_orders.append(order_dict)
                
        return serialized_orders

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing orders: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )


@router.put("/orders/{order_id}/status", response_model=None)
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
        
        # Convert order to serializable format
        if hasattr(order, "to_dict"):
            return order.to_dict()
        else:
            # Basic serialization if to_dict is not available
            order_dict = {
                "id": str(order.id),
                "status": order.status,
                "total": float(order.total),
                "created_at": order.created_at.isoformat() if hasattr(order, "created_at") else None,
                "customer_name": getattr(order, "customer_name", None),
                "customer_email": getattr(order, "customer_email", None)
            }
            return order_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating order {order_id} status: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Order not found: {order_id}"
        )


@router.post("/orders/{order_id}/payment", response_model=None)
async def process_payment(
    request: Request,
    order_id: str,
    payment_data: Dict[str, Any],
    order_manager: OrderManager = Depends(get_order_manager),
    plugin_manager: Optional[PluginManager] = Depends(get_plugin_manager)
):
    """
    Process payment for an order.

    Args:
        request: The FastAPI request object
        order_id: The ID of the order
        payment_data: Payment details including:
            - plugin: Name of the payment plugin to use
            - customer_email: Email for order confirmation (optional)
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

        # Process payment - this can be a synchronous or asynchronous call
        # depending on the plugin implementation
        if hasattr(plugin, 'process_payment'):
            # Use await only if the method is a coroutine
            if asyncio.iscoroutinefunction(plugin.process_payment):
                payment_result = await plugin.process_payment(order.id, payment_data)
            else:
                payment_result = plugin.process_payment(order.id, payment_data)
        else:
            # Fallback to synchronous method if process_payment is not available
            payment_result = plugin.process_payment_sync(order.id, payment_data)

        # Update order with payment info
        order = order_manager.update_payment(order_id, payment_result["payment_id"])

        # Get customer email from payment data or order metadata
        customer_email = payment_data.get("customer_email")
        if not customer_email and order.metadata and "customer_email" in order.metadata:
            customer_email = order.metadata["customer_email"]

        # If we have shipping address, try to get email from there
        if not customer_email and order.shipping_address and hasattr(order.shipping_address, "email"):
            customer_email = order.shipping_address.email

        # Send payment confirmation email if we have an email
        if customer_email:
            email_service = get_email_service()
            if email_service is None:
                # Initialize with default settings or environment variables
                email_config = EmailConfig(
                    smtp_host=os.environ.get("SMTP_HOST", "smtp.gmail.com"),
                    smtp_port=int(os.environ.get("SMTP_PORT", "587")),
                    smtp_username=os.environ.get("SMTP_USERNAME"),
                    smtp_password=os.environ.get("SMTP_PASSWORD"),
                    default_sender=os.environ.get("SMTP_SENDER", "noreply@pycommerce.example.com"),
                    enabled=bool(os.environ.get("SMTP_ENABLED", "False").lower() == "true")
                )
                email_service = init_email_service(email_config)

                # Enable test mode if credentials are missing
                if not email_config.enabled:
                    email_service.enable_test_mode()
                    logger.info("Email service running in test mode (no emails will be sent)")

            # Get store information (tenant) for the email
            store_name = "PyCommerce Store"
            store_url = str(request.base_url)
            store_logo_url = None
            contact_email = os.environ.get("CONTACT_EMAIL", email_service.config.default_sender)

            # Try to get tenant information
            try:
                tenant_plugin = plugin_manager.get("tenant")
                if tenant_plugin:
                    tenant = tenant_plugin.get_current_tenant()
                    if tenant:
                        store_name = tenant.name
                        # Use tenant domain if available, otherwise use request base URL
                        if tenant.domain:
                            store_url = f"https://{tenant.domain}"
                        # Get logo URL from theme settings if available
                        if hasattr(tenant, "settings") and tenant.settings and "logo_url" in tenant.settings:
                            store_logo_url = tenant.settings["logo_url"]
            except Exception as e:
                logger.warning(f"Error getting tenant info for email: {str(e)}")

            # Send the confirmation email
            try:
                email_sent = email_service.send_order_confirmation(
                    order=order,
                    to_email=customer_email,
                    store_name=store_name,
                    store_url=store_url,
                    store_logo_url=store_logo_url,
                    contact_email=contact_email
                )

                if email_sent:
                    logger.info(f"Payment confirmation email sent to {customer_email} for order {order.id}")
                else:
                    logger.warning(f"Failed to send payment confirmation email to {customer_email} for order {order.id}")

            except Exception as e:
                logger.error(f"Error sending payment confirmation email: {str(e)}")

        logger.info(f"Processed payment for order {order_id}")
        
        # Convert order to serializable format
        if hasattr(order, "to_dict"):
            return order.to_dict()
        else:
            # Basic serialization if to_dict is not available
            order_dict = {
                "id": str(order.id),
                "status": order.status,
                "total": float(order.total),
                "created_at": order.created_at.isoformat() if hasattr(order, "created_at") else None,
                "customer_name": getattr(order, "customer_name", None),
                "customer_email": getattr(order, "customer_email", None)
            }
            return order_dict

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