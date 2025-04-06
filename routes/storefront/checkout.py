"""
Checkout routes for the PyCommerce storefront.

This module defines the routes for checkout process and payment handling.
"""
import logging
import json
from typing import Optional, Dict, List, Any
from fastapi import APIRouter, Request, Depends, Query, Body, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from pycommerce.models.tenant import TenantManager
from pycommerce.models.product import ProductManager
from pycommerce.models.cart import CartManager
from pycommerce.models.order import OrderManager
from pycommerce.plugins import get_plugin_registry

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["checkout"])

# Global variables initialized in setup_routes
templates = None
tenant_manager = TenantManager()
product_manager = ProductManager()
cart_manager = CartManager()
order_manager = OrderManager()

@router.get("/checkout", response_class=HTMLResponse)
async def checkout(request: Request):
    """Checkout page."""
    # Get cart from session
    cart_id = request.session.get("cart_id")
    cart_items = []
    cart_total = 0.0
    tenant_id = None
    
    if not cart_id:
        # Redirect to cart if no active cart
        return RedirectResponse(url="/cart")
    
    try:
        cart = cart_manager.get(cart_id)
        
        if not cart.items:
            # Redirect to cart if cart is empty
            return RedirectResponse(url="/cart")
        
        # Format cart items for template
        for item in cart.items:
            product = product_manager.get(item.product_id)
            if product:
                # Get tenant from the first product's metadata
                if not tenant_id and hasattr(product, 'metadata') and product.metadata.get('tenant_id'):
                    tenant_id = product.metadata.get('tenant_id')
                
                item_data = {
                    "id": str(item.id),
                    "product_id": str(item.product_id),
                    "name": product.name,
                    "price": product.price,
                    "quantity": item.quantity,
                    "subtotal": product.price * item.quantity
                }
                cart_items.append(item_data)
                cart_total += item_data["subtotal"]
    except Exception as e:
        logger.error(f"Error fetching cart: {str(e)}")
        return RedirectResponse(url="/cart")
    
    # Get available payment methods
    payment_methods = []
    try:
        plugin_registry = get_plugin_registry()
        
        for plugin_id, plugin in plugin_registry.get_payment_plugins().items():
            payment_methods.append({
                "id": plugin_id,
                "name": plugin.name,
                "description": plugin.description
            })
    except Exception as e:
        logger.error(f"Error fetching payment methods: {str(e)}")
    
    # Get shipping methods
    shipping_methods = []
    shipping_config = {}
    
    try:
        plugin_registry = get_plugin_registry()
        shipping_plugin = plugin_registry.get_shipping_plugin('standard')
        
        if shipping_plugin and tenant_id:
            # Get shipping config for tenant
            shipping_config = shipping_plugin.get_shipping_config(tenant_id)
            
            # Add standard shipping method
            shipping_methods.append({
                "id": "standard",
                "name": "Standard Shipping",
                "description": "5-7 business days",
                "price": shipping_config.get("flat_rate_domestic", 5.99)
            })
            
            # Add express shipping if available
            express_multiplier = shipping_config.get("express_multiplier", 1.75)
            if express_multiplier > 1:
                express_price = shipping_config.get("flat_rate_domestic", 5.99) * express_multiplier
                shipping_methods.append({
                    "id": "express",
                    "name": "Express Shipping",
                    "description": "1-2 business days",
                    "price": express_price
                })
    except Exception as e:
        logger.error(f"Error fetching shipping methods: {str(e)}")
        # Default shipping methods
        shipping_methods = [
            {
                "id": "standard",
                "name": "Standard Shipping",
                "description": "5-7 business days",
                "price": 5.99
            },
            {
                "id": "express",
                "name": "Express Shipping",
                "description": "1-2 business days",
                "price": 12.99
            }
        ]
    
    return templates.TemplateResponse(
        "checkout.html", 
        {
            "request": request, 
            "cart_items": cart_items,
            "cart_total": cart_total,
            "cart_item_count": len(cart_items),
            "payment_methods": payment_methods,
            "shipping_methods": shipping_methods
        }
    )

@router.post("/checkout/process")
async def process_checkout(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    postal_code: str = Form(...),
    country: str = Form(...),
    payment_method: str = Form(...),
    shipping_method: str = Form(...)
):
    """Process checkout and create order."""
    # Get cart from session
    cart_id = request.session.get("cart_id")
    
    if not cart_id:
        return JSONResponse(
            status_code=400,
            content={"error": "No active cart found"}
        )
    
    try:
        # Get cart and items
        cart = cart_manager.get(cart_id)
        
        if not cart.items:
            return JSONResponse(
                status_code=400,
                content={"error": "Cart is empty"}
            )
        
        # Calculate order total
        items = []
        subtotal = 0.0
        tenant_id = None
        
        for item in cart.items:
            product = product_manager.get(item.product_id)
            if product:
                # Get tenant from the first product's metadata
                if not tenant_id and hasattr(product, 'metadata') and product.metadata.get('tenant_id'):
                    tenant_id = product.metadata.get('tenant_id')
                
                item_data = {
                    "product_id": str(item.product_id),
                    "name": product.name,
                    "price": product.price,
                    "quantity": item.quantity,
                    "subtotal": product.price * item.quantity
                }
                items.append(item_data)
                subtotal += item_data["subtotal"]
        
        # Get shipping cost
        shipping_cost = 5.99  # Default
        
        try:
            plugin_registry = get_plugin_registry()
            shipping_plugin = plugin_registry.get_shipping_plugin('standard')
            
            if shipping_plugin and tenant_id:
                # Get shipping config for tenant
                shipping_config = shipping_plugin.get_shipping_config(tenant_id)
                
                if shipping_method == "standard":
                    shipping_cost = shipping_config.get("flat_rate_domestic", 5.99)
                elif shipping_method == "express":
                    express_multiplier = shipping_config.get("express_multiplier", 1.75)
                    shipping_cost = shipping_config.get("flat_rate_domestic", 5.99) * express_multiplier
        except Exception as e:
            logger.error(f"Error calculating shipping cost: {str(e)}")
        
        # Calculate tax (example: 8% sales tax)
        tax_rate = 0.08
        tax = subtotal * tax_rate
        
        # Calculate total
        total = subtotal + shipping_cost + tax
        
        # Create order
        order_data = {
            "customer": {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "address": address,
                "city": city,
                "state": state,
                "postal_code": postal_code,
                "country": country
            },
            "items": items,
            "subtotal": subtotal,
            "shipping_cost": shipping_cost,
            "tax": tax,
            "total": total,
            "payment_method": payment_method,
            "shipping_method": shipping_method,
            "status": "PENDING",
            "metadata": {
                "tenant_id": tenant_id,
                "cart_id": cart_id
            }
        }
        
        order = order_manager.create(order_data)
        
        # Store order ID in session
        request.session["order_id"] = str(order.id)
        
        # Redirect to payment page
        return RedirectResponse(url=f"/checkout/payment/{order.id}", status_code=303)
    
    except Exception as e:
        logger.error(f"Error processing checkout: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to process checkout: {str(e)}"}
        )

@router.get("/checkout/payment/{order_id}", response_class=HTMLResponse)
async def payment(request: Request, order_id: str):
    """Payment page for an order."""
    try:
        # Get order
        order = order_manager.get(order_id)
        
        if not order:
            return RedirectResponse(url="/cart")
        
        # Get payment method details
        payment_method_id = order.payment_method
        payment_method = None
        
        try:
            plugin_registry = get_plugin_registry()
            payment_plugin = plugin_registry.get_payment_plugin(payment_method_id)
            
            if payment_plugin:
                payment_method = {
                    "id": payment_method_id,
                    "name": payment_plugin.name,
                    "description": payment_plugin.description,
                    "client_key": payment_plugin.get_client_key() if hasattr(payment_plugin, 'get_client_key') else None
                }
        except Exception as e:
            logger.error(f"Error fetching payment method: {str(e)}")
        
        # Format order data for template
        order_data = {
            "id": str(order.id),
            "customer": order.customer,
            "items": order.items,
            "subtotal": order.subtotal,
            "shipping_cost": order.shipping_cost,
            "tax": order.tax,
            "total": order.total,
            "payment_method": payment_method,
            "shipping_method": order.shipping_method,
            "status": order.status
        }
        
        return templates.TemplateResponse(
            "payment.html", 
            {
                "request": request, 
                "order": order_data,
                "payment_method": payment_method
            }
        )
    
    except Exception as e:
        logger.error(f"Error retrieving order for payment: {str(e)}")
        return RedirectResponse(url="/cart")

@router.post("/checkout/payment/{order_id}/process")
async def process_payment(
    request: Request,
    order_id: str,
    payment_token: str = Form(...),
    payment_method_id: str = Form(...)
):
    """Process payment for an order."""
    try:
        # Get order
        order = order_manager.get(order_id)
        
        if not order:
            return JSONResponse(
                status_code=404,
                content={"error": "Order not found"}
            )
        
        # Process payment with plugin
        plugin_registry = get_plugin_registry()
        payment_plugin = plugin_registry.get_payment_plugin(payment_method_id)
        
        if not payment_plugin:
            return JSONResponse(
                status_code=400,
                content={"error": f"Payment method {payment_method_id} not available"}
            )
        
        payment_result = payment_plugin.process_payment({
            "order_id": order_id,
            "amount": order.total,
            "currency": "USD",
            "token": payment_token,
            "metadata": {
                "customer_email": order.customer.get("email"),
                "customer_name": f"{order.customer.get('first_name')} {order.customer.get('last_name')}"
            }
        })
        
        if payment_result.get("success"):
            # Update order status
            order_manager.update(order_id, {"status": "PAID"})
            
            # Clear cart
            cart_id = order.metadata.get("cart_id")
            if cart_id:
                cart = cart_manager.get(cart_id)
                cart.clear()
                
                # Clear cart from session
                if request.session.get("cart_id") == cart_id:
                    del request.session["cart_id"]
            
            # Redirect to confirmation page
            return RedirectResponse(url=f"/checkout/confirmation/{order_id}", status_code=303)
        else:
            # Payment failed
            error_message = payment_result.get("message", "Payment failed")
            return templates.TemplateResponse(
                "payment.html", 
                {
                    "request": request, 
                    "order": {
                        "id": str(order.id),
                        "total": order.total
                    },
                    "payment_method": {"id": payment_method_id},
                    "error": error_message
                },
                status_code=400
            )
    
    except Exception as e:
        logger.error(f"Error processing payment: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to process payment: {str(e)}"}
        )

@router.get("/checkout/confirmation/{order_id}", response_class=HTMLResponse)
async def confirmation(request: Request, order_id: str):
    """Order confirmation page."""
    try:
        # Get order
        order = order_manager.get(order_id)
        
        if not order:
            return RedirectResponse(url="/")
        
        # Format order data for template
        order_data = {
            "id": str(order.id),
            "customer": order.customer,
            "items": order.items,
            "subtotal": order.subtotal,
            "shipping_cost": order.shipping_cost,
            "tax": order.tax,
            "total": order.total,
            "payment_method": order.payment_method,
            "shipping_method": order.shipping_method,
            "status": order.status,
            "created_at": order.created_at if hasattr(order, 'created_at') else None
        }
        
        return templates.TemplateResponse(
            "confirmation.html", 
            {
                "request": request, 
                "order": order_data
            }
        )
    
    except Exception as e:
        logger.error(f"Error retrieving order for confirmation: {str(e)}")
        return RedirectResponse(url="/")

def setup_routes(app_templates):
    """
    Set up routes with the given templates.
    
    Args:
        app_templates: Jinja2Templates instance from the main app
    """
    global templates
    templates = app_templates
    return router