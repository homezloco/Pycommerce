"""
Checkout routes for the PyCommerce storefront.

This module defines the routes for checkout process and payment handling.
"""
import logging
import json
from typing import Optional, Dict, List, Any
from uuid import UUID
from fastapi import APIRouter, Request, Depends, Query, Body, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from pycommerce.models.tenant import TenantManager
from pycommerce.models.product import ProductManager
from pycommerce.models.cart import CartManager
# Import OrderManager lazily to avoid circular imports
# from pycommerce.models.order import OrderManager
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
# Initialize order_manager later to avoid circular imports
order_manager = None

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
        
        # Prepare the base URL for redirect URLs
        base_url = str(request.base_url).rstrip('/')
        
        # Process payment with plugin
        plugin_registry = get_plugin_registry()
        payment_plugin = plugin_registry.get_payment_plugin(payment_method_id)
        
        if not payment_plugin:
            return JSONResponse(
                status_code=400,
                content={"error": f"Payment method {payment_method_id} not available"}
            )
        
        # Build payment data specific to the plugin type
        payment_data = {
            "amount": order.total,
            "currency": "USD",
            "return_url": f"{base_url}/checkout/payment/{order_id}/complete",
            "cancel_url": f"{base_url}/checkout/payment/{order_id}/cancel",
            "metadata": {
                "customer_email": order.customer.get("email"),
                "customer_name": f"{order.customer.get('first_name')} {order.customer.get('last_name')}"
            }
        }
        
        # Add payment method data based on the payment method type
        if payment_method_id == "stripe_payment":
            payment_data["payment_method"] = payment_token
        elif payment_method_id == "paypal_payment":
            # PayPal doesn't need a token at this stage
            pass
        else:
            payment_data["token"] = payment_token
            
        # Call the async method properly with await
        try:
            payment_result = await payment_plugin.process_payment(UUID(order_id), payment_data)
            
            # Check for PayPal approval URL
            if payment_method_id == "paypal_payment" and payment_result.get("approval_url"):
                # Store payment ID in session for later completion
                request.session["paypal_payment_id"] = payment_result.get("payment_id")
                
                # Redirect to PayPal for approval
                return RedirectResponse(url=payment_result["approval_url"], status_code=303)
            
            # For immediate payment methods (like Stripe)
            if payment_result.get("status") in ["succeeded", "COMPLETED", "complete", "authorized"]:
                # Update order with payment information
                order_manager.update(order_id, {
                    "status": "PAID", 
                    "payment_id": payment_result.get("payment_id"),
                    "payment_status": payment_result.get("status")
                })
                
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
            elif payment_result.get("status") in ["requires_action", "requires_confirmation"]:
                # Payment needs additional action (like 3D Secure)
                return templates.TemplateResponse(
                    "payment_action.html", 
                    {
                        "request": request, 
                        "order": {
                            "id": str(order.id),
                            "total": order.total
                        },
                        "payment_result": payment_result,
                        "client_secret": payment_result.get("client_secret"),
                        "payment_method": {
                            "id": payment_method_id,
                            "client_key": payment_plugin.get_client_key() if hasattr(payment_plugin, "get_client_key") else None
                        }
                    }
                )
            else:
                # Payment failed or is pending
                error_message = payment_result.get("message", f"Payment failed with status: {payment_result.get('status', 'unknown')}")
                logger.error(f"Payment failed: {error_message}")
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
                
        except Exception as payment_error:
            logger.error(f"Payment processing error: {str(payment_error)}")
            return templates.TemplateResponse(
                "payment.html", 
                {
                    "request": request, 
                    "order": {
                        "id": str(order.id),
                        "total": order.total
                    },
                    "payment_method": {"id": payment_method_id},
                    "error": f"Payment error: {str(payment_error)}"
                },
                status_code=400
            )
    
    except Exception as e:
        logger.error(f"Error processing payment: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to process payment: {str(e)}"}
        )

@router.get("/checkout/payment/{order_id}/complete")
async def payment_complete(request: Request, order_id: str, token: Optional[str] = None, PayerID: Optional[str] = None):
    """Complete payment after external payment provider approval (like PayPal)."""
    try:
        # Get order
        order = order_manager.get(order_id)
        
        if not order:
            return JSONResponse(
                status_code=404,
                content={"error": "Order not found"}
            )
        
        # Check if PayPal payment needs to be captured
        if order.payment_method == "paypal_payment" and PayerID and token:
            # Get payment ID from session
            payment_id = request.session.get("paypal_payment_id")
            
            if not payment_id:
                logger.error(f"PayPal payment ID not found in session for order {order_id}")
                return templates.TemplateResponse(
                    "payment.html", 
                    {
                        "request": request, 
                        "order": {
                            "id": str(order.id),
                            "total": order.total
                        },
                        "payment_method": {"id": "paypal_payment"},
                        "error": "Payment session expired or invalid. Please try again."
                    },
                    status_code=400
                )
            
            # Capture the PayPal payment
            try:
                plugin_registry = get_plugin_registry()
                payment_plugin = plugin_registry.get_payment_plugin("paypal_payment")
                
                if not payment_plugin:
                    raise Exception("PayPal payment plugin not available")
                
                # Call the async capture method
                capture_result = await payment_plugin.capture_payment(payment_id)
                
                if capture_result.get("status") in ["COMPLETED", "CAPTURED"]:
                    # Update order status
                    order_manager.update(order_id, {
                        "status": "PAID", 
                        "payment_id": payment_id,
                        "payment_status": capture_result.get("status"),
                        "payment_details": {
                            "payer_id": PayerID,
                            "capture_id": capture_result.get("capture_id")
                        }
                    })
                    
                    # Clear cart
                    cart_id = order.metadata.get("cart_id")
                    if cart_id:
                        cart = cart_manager.get(cart_id)
                        cart.clear()
                        
                        # Clear cart from session
                        if request.session.get("cart_id") == cart_id:
                            del request.session["cart_id"]
                    
                    # Clear PayPal payment ID from session
                    if "paypal_payment_id" in request.session:
                        del request.session["paypal_payment_id"]
                    
                    # Redirect to confirmation page
                    return RedirectResponse(url=f"/checkout/confirmation/{order_id}", status_code=303)
                else:
                    # Payment capture failed
                    error_message = f"PayPal payment could not be completed. Status: {capture_result.get('status')}"
                    logger.error(error_message)
                    return templates.TemplateResponse(
                        "payment.html", 
                        {
                            "request": request, 
                            "order": {
                                "id": str(order.id),
                                "total": order.total
                            },
                            "payment_method": {"id": "paypal_payment"},
                            "error": error_message
                        },
                        status_code=400
                    )
            
            except Exception as capture_error:
                logger.error(f"Error capturing PayPal payment: {str(capture_error)}")
                return templates.TemplateResponse(
                    "payment.html", 
                    {
                        "request": request, 
                        "order": {
                            "id": str(order.id),
                            "total": order.total
                        },
                        "payment_method": {"id": "paypal_payment"},
                        "error": f"Error completing payment: {str(capture_error)}"
                    },
                    status_code=400
                )
        
        # For other payment methods
        return RedirectResponse(url=f"/checkout/confirmation/{order_id}", status_code=303)
    
    except Exception as e:
        logger.error(f"Error completing payment: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to complete payment: {str(e)}"}
        )

@router.get("/checkout/payment/{order_id}/cancel")
async def payment_cancel(request: Request, order_id: str):
    """Handle payment cancellation from external payment providers."""
    try:
        # Get order
        order = order_manager.get(order_id)
        
        if not order:
            return RedirectResponse(url="/")
        
        # Clear PayPal payment ID from session if it exists
        if "paypal_payment_id" in request.session:
            del request.session["paypal_payment_id"]
        
        # Return to payment page with a cancellation message
        return templates.TemplateResponse(
            "payment.html", 
            {
                "request": request, 
                "order": {
                    "id": str(order.id),
                    "customer": order.customer,
                    "items": order.items,
                    "subtotal": order.subtotal,
                    "shipping_cost": order.shipping_cost,
                    "tax": order.tax,
                    "total": order.total,
                    "payment_method": {"id": order.payment_method},
                    "shipping_method": order.shipping_method,
                    "status": order.status
                },
                "payment_cancelled": True,
                "message": "Your payment was cancelled. Please try again or choose a different payment method."
            }
        )
    
    except Exception as e:
        logger.error(f"Error handling payment cancellation: {str(e)}")
        return RedirectResponse(url="/")

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
            "created_at": order.created_at if hasattr(order, 'created_at') else None,
            "payment_id": getattr(order, "payment_id", None),
            "payment_status": getattr(order, "payment_status", None)
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
    global templates, tenant_manager, product_manager, cart_manager, order_manager
    templates = app_templates
    
    # Try to load Flask app managers to replace SDK managers
    try:
        # Always use the SDK implementations to avoid circular imports
        from pycommerce.models.tenant import TenantManager as SDKTenantManager
        tenant_manager = SDKTenantManager()
        logger.info("Initialized SDK TenantManager")
        
        from pycommerce.models.product import ProductManager as SDKProductManager
        product_manager = SDKProductManager()
        logger.info("Initialized SDK ProductManager")
        
        from pycommerce.models.cart import CartManager as SDKCartManager
        cart_manager = SDKCartManager()
        logger.info("Initialized SDK CartManager")
        
        # Import order manager separately to avoid circular imports
        global order_manager
        if order_manager is None:
            from pycommerce.models.order import OrderManager
            order_manager = OrderManager()
            logger.info("Initialized SDK OrderManager")
            
        logger.info("Finished loading Flask app managers")
    except Exception as e:
        logger.error(f"General error loading Flask app managers: {e}")
        # We'll keep using the SDK managers as fallback
        
    return router