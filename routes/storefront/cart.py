"""
Storefront routes for cart management.

This module contains all the routes for cart management in the storefront.
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

# Template setup will be passed from main app
templates = None

# Initialize logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["cart"])

# Import models and managers
try:
    from pycommerce.models.cart import CartManager
    from pycommerce.models.product import ProductManager
    
    # Initialize managers
    cart_manager = CartManager()
    product_manager = ProductManager()
except ImportError as e:
    logger.error(f"Error importing cart modules: {str(e)}")

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

@router.get("/cart", response_class=HTMLResponse)
async def view_cart(request: Request):
    """
    Render the cart page with the current cart contents.
    """
    # Get cart from session
    cart, cart_data, cart_totals = get_session_cart(request)
    
    return templates.TemplateResponse(
        "cart.html",
        {
            "request": request,
            "cart": cart_data,
            "cart_totals": cart_totals,
            "cart_item_count": cart_data["total_quantity"]
        }
    )

@router.post("/cart/add", response_class=RedirectResponse)
async def add_to_cart(
    request: Request,
    product_id: str = Form(...),
    quantity: int = Form(1)
):
    """
    Add an item to the cart.
    """
    # Get cart from session
    session = request.session
    cart_id = session.get("cart_id")
    
    try:
        if not cart_id:
            # Create new cart
            cart = cart_manager.create()
            session["cart_id"] = str(cart.id)
            cart_id = str(cart.id)
        
        # Get product to check if it exists
        product = product_manager.get(product_id)
        
        # Add item to cart
        cart_manager.add_item(cart_id, product_id, quantity)
        
        # Redirect back to products page
        referer = request.headers.get("referer")
        return RedirectResponse(url=referer or "/products", status_code=303)
        
    except Exception as e:
        logger.error(f"Error adding item to cart: {str(e)}")
        # Redirect to products page
        return RedirectResponse(url="/products", status_code=303)

@router.post("/cart/update", response_class=RedirectResponse)
async def update_cart_item(
    request: Request,
    product_id: str = Form(...),
    quantity: int = Form(1)
):
    """
    Update the quantity of an item in the cart.
    """
    # Get cart from session
    session = request.session
    cart_id = session.get("cart_id")
    
    try:
        if cart_id:
            # Update item quantity
            cart_manager.update_item(cart_id, product_id, quantity)
        
        # Redirect back to cart page
        return RedirectResponse(url="/cart", status_code=303)
        
    except Exception as e:
        logger.error(f"Error updating cart item: {str(e)}")
        # Redirect to cart page
        return RedirectResponse(url="/cart", status_code=303)

@router.post("/cart/remove", response_class=RedirectResponse)
async def remove_from_cart(
    request: Request,
    product_id: str = Form(...)
):
    """
    Remove an item from the cart.
    """
    # Get cart from session
    session = request.session
    cart_id = session.get("cart_id")
    
    try:
        if cart_id:
            # Remove item from cart
            cart_manager.remove_item(cart_id, product_id)
        
        # Redirect back to cart page
        return RedirectResponse(url="/cart", status_code=303)
        
    except Exception as e:
        logger.error(f"Error removing item from cart: {str(e)}")
        # Redirect to cart page
        return RedirectResponse(url="/cart", status_code=303)

@router.post("/cart/clear", response_class=RedirectResponse)
async def clear_cart(request: Request):
    """
    Clear all items from the cart.
    """
    # Get cart from session
    session = request.session
    cart_id = session.get("cart_id")
    
    try:
        if cart_id:
            # Clear cart
            cart_manager.clear(cart_id)
        
        # Redirect back to cart page
        return RedirectResponse(url="/cart", status_code=303)
        
    except Exception as e:
        logger.error(f"Error clearing cart: {str(e)}")
        # Redirect to cart page
        return RedirectResponse(url="/cart", status_code=303)

def setup_routes(app_templates):
    """
    Set up routes with the given templates.
    
    Args:
        app_templates: Jinja2Templates instance from the main app
    """
    global templates
    templates = app_templates
    return router