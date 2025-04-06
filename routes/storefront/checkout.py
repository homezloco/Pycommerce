"""
Storefront routes for checkout process.

This module contains all the routes for the checkout process.
"""
import logging
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

# Template setup will be passed from main app
templates = None

# Initialize logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["checkout"])

# Import models and managers
try:
    from pycommerce.models.cart import CartManager
    from pycommerce.models.product import ProductManager
    from pycommerce.models.order import OrderManager
    from pycommerce.plugins import get_plugin_registry
    
    # Initialize managers
    cart_manager = CartManager()
    product_manager = ProductManager()
    order_manager = OrderManager()
    
    # Get plugin registry for payment processing
    plugin_registry = get_plugin_registry()
except ImportError as e:
    logger.error(f"Error importing checkout modules: {str(e)}")

# Helper function to get cart
def get_session_cart(request: Request):
    """
    Get or create a cart for the current session.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        The cart object and a dict with cart details for templates
    """
    session = request.session
    cart_id = session.get("cart_id")
    
    try:
        if cart_id:
            # Get existing cart
            cart = cart_manager.get(cart_id)
        else:
            # Create new cart
            cart = cart_manager.create()
            session["cart_id"] = str(cart.id)
        
        # Serialize cart items for template
        items = []
        for item in cart.items:
            # Get product details
            product = product_manager.get(item.product_id)
            items.append({
                "product_id": str(item.product_id),
                "product_name": product.name,
                "unit_price": product.price,
                "quantity": item.quantity,
                "total": product.price * item.quantity
            })
        
        # Calculate totals
        totals = cart_manager.calculate_totals(cart.id, product_manager)
        
        # Prepare cart for template
        cart_data = {
            "id": str(cart.id),
            "items": items,
            "item_count": len(items),
            "total_quantity": sum(item["quantity"] for item in items)
        }
        
        return cart, cart_data, totals
    
    except Exception as e:
        logger.error(f"Error getting session cart: {str(e)}")
        # Return empty cart if there was an error
        return None, {"id": None, "items": [], "item_count": 0, "total_quantity": 0}, {"subtotal": 0, "tax": 0, "total": 0}

@router.get("/checkout", response_class=HTMLResponse)
async def checkout(request: Request):
    """
    Render the checkout page.
    """
    # Get cart from session
    cart, cart_data, cart_totals = get_session_cart(request)
    
    # Add default shipping cost to cart totals
    cart_totals["shipping"] = 5.99
    
    return templates.TemplateResponse(
        "checkout.html",
        {
            "request": request,
            "cart": cart_data,
            "cart_totals": cart_totals,
            "cart_item_count": cart_data["total_quantity"]
        }
    )

@router.post("/checkout/process", response_class=RedirectResponse)
async def process_checkout(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    address_line1: str = Form(...),
    address_line2: Optional[str] = Form(None),
    city: str = Form(...),
    state: str = Form(...),
    postal_code: str = Form(...),
    country: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    shipping_method: str = Form(...),
    payment_method: str = Form(...)
):
    """
    Process the checkout and create an order.
    """
    # Get cart from session
    session = request.session
    cart_id = session.get("cart_id")
    
    try:
        if not cart_id:
            # No cart, redirect to products
            return RedirectResponse(url="/products", status_code=303)
        
        # Prepare shipping address
        shipping_address = {
            "first_name": first_name,
            "last_name": last_name,
            "address_line1": address_line1,
            "address_line2": address_line2,
            "city": city,
            "state": state,
            "postal_code": postal_code,
            "country": country,
            "phone": phone,
            "email": email
        }
        
        # Determine shipping cost
        shipping_cost = 5.99  # Standard shipping default
        if shipping_method == "express":
            shipping_cost = 12.99
        elif shipping_method == "overnight":
            shipping_cost = 24.99
        
        # Create order from cart
        order = order_manager.create_from_cart(
            cart_id,
            product_manager,
            cart_manager,
            shipping_address
        )
        
        # Add shipping cost and additional order details
        order.shipping_cost = shipping_cost
        order.total += shipping_cost
        
        # Store order ID in session
        session["order_id"] = str(order.id)
        
        # Clear the cart after successful order creation
        cart_manager.clear(cart_id)
        
        # Process payment based on selected method
        payment_id = None
        
        if payment_method == "stripe":
            # Use Stripe payment plugin if available
            stripe_plugin = plugin_registry.get_payment_plugin("stripe")
            if stripe_plugin:
                # TODO: Implement actual Stripe payment processing
                payment_id = f"STRIPE-{uuid4().hex[:8]}"
        elif payment_method == "paypal":
            # Use PayPal payment plugin if available
            paypal_plugin = plugin_registry.get_payment_plugin("paypal")
            if paypal_plugin:
                # TODO: Implement actual PayPal payment processing
                payment_id = f"PAYPAL-{uuid4().hex[:8]}"
        else:
            # Default mock payment ID
            payment_id = f"PAYMENT-{uuid4().hex[:8]}"
        
        # Update order with payment info
        if payment_id:
            order_manager.update_payment(order.id, payment_id)
        
        # Redirect to confirmation page
        return RedirectResponse(url="/confirmation", status_code=303)
        
    except Exception as e:
        logger.error(f"Error processing checkout: {str(e)}")
        # Redirect back to checkout page
        return RedirectResponse(url="/checkout", status_code=303)

@router.get("/confirmation", response_class=HTMLResponse)
async def order_confirmation(request: Request):
    """
    Render the order confirmation page.
    """
    # Get order from session
    session = request.session
    order_id = session.get("order_id")
    
    if not order_id:
        # No order, redirect to products
        return RedirectResponse(url="/products")
    
    try:
        # Get order
        order = order_manager.get(order_id)
        
        # Format order for template
        order_data = {
            "id": str(order.id),
            "status": order.status.value,
            "subtotal": order.subtotal,
            "tax": order.tax,
            "shipping_cost": order.shipping_cost,
            "total": order.total,
            "created_at": order.created_at,
            "payment_id": order.payment_id,
            "shipping_address": order.shipping_address,
            "items": order.items
        }
        
        return templates.TemplateResponse(
            "confirmation.html",
            {
                "request": request,
                "order": order_data,
                "cart_item_count": 0  # Clear cart count after order
            }
        )
        
    except Exception as e:
        logger.error(f"Error displaying order confirmation: {str(e)}")
        # Redirect to products page
        return RedirectResponse(url="/products")

def setup_routes(app_templates):
    """
    Set up routes with the given templates.
    
    Args:
        app_templates: Jinja2Templates instance from the main app
    """
    global templates
    templates = app_templates
    return router