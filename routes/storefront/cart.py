"""
Cart routes for the PyCommerce storefront.

This module defines the routes for cart management including adding, updating, and removing items.
"""
import logging
from typing import Optional, Dict, List, Any
from fastapi import APIRouter, Request, Depends, Query, Body, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import cast

from pycommerce.models.tenant import TenantManager
from pycommerce.models.product import ProductManager
from pycommerce.models.cart import CartManager

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["cart"])

# Global variables initialized in setup_routes
templates = None
tenant_manager = TenantManager()
product_manager = ProductManager()
cart_manager = CartManager()

@router.get("/cart", response_class=HTMLResponse)
async def view_cart(request: Request):
    """View the current cart."""
    # Get cart from session
    cart_id = request.session.get("cart_id")
    cart_items = []
    cart_total = 0.0
    
    if cart_id:
        try:
            cart = cart_manager.get(cart_id)
            
            # Format cart items for template
            for item in cart.items:
                product = product_manager.get(item.product_id)
                if product:
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
    
    return templates.TemplateResponse(
        "cart.html", 
        {
            "request": request, 
            "cart_items": cart_items,
            "cart_total": cart_total,
            "cart_item_count": len(cart_items)
        }
    )

@router.post("/cart/add")
async def add_to_cart(
    request: Request,
    product_id: str = Form(...),
    quantity: int = Form(1)
):
    """Add a product to the cart."""
    # Get or create cart
    cart_id = request.session.get("cart_id")
    
    try:
        if not cart_id:
            # Create a new cart
            cart = cart_manager.create()
            cart_id = str(cart.id)
            request.session["cart_id"] = cart_id
        
        # Check if product exists
        product = product_manager.get(product_id)
        if not product:
            return JSONResponse(
                status_code=404,
                content={"error": "Product not found"}
            )
        
        # Check if item already in cart
        cart = cart_manager.get(cart_id)
        existing_item = None
        
        for item in cart.items:
            if item.product_id == product_id:
                existing_item = item
                break
        
        if existing_item:
            # Update quantity
            cart.update_item(
                str(existing_item.id),
                {"quantity": existing_item.quantity + quantity}
            )
        else:
            # Add new item
            cart.add_item({
                "product_id": product_id,
                "quantity": quantity
            })
        
        # Redirect back to product or referrer
        referer = request.headers.get("referer")
        if referer:
            return RedirectResponse(url=referer, status_code=303)
        return RedirectResponse(url=f"/products/{product_id}", status_code=303)
    
    except Exception as e:
        logger.error(f"Error adding item to cart: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to add item to cart: {str(e)}"}
        )

@router.post("/cart/update")
async def update_cart(
    request: Request,
    item_id: str = Form(...),
    quantity: int = Form(...)
):
    """Update the quantity of an item in the cart."""
    cart_id = request.session.get("cart_id")
    
    if not cart_id:
        return JSONResponse(
            status_code=400,
            content={"error": "No active cart found"}
        )
    
    try:
        # Get cart
        cart = cart_manager.get(cart_id)
        
        # Validate quantity
        if quantity <= 0:
            # Remove item if quantity is 0 or negative
            cart.remove_item(item_id)
        else:
            # Update quantity
            cart.update_item(item_id, {"quantity": quantity})
        
        # Redirect back to cart
        return RedirectResponse(url="/cart", status_code=303)
    
    except Exception as e:
        logger.error(f"Error updating cart: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to update cart: {str(e)}"}
        )

@router.post("/cart/remove")
async def remove_from_cart(
    request: Request,
    item_id: str = Form(...)
):
    """Remove an item from the cart."""
    cart_id = request.session.get("cart_id")
    
    if not cart_id:
        return JSONResponse(
            status_code=400,
            content={"error": "No active cart found"}
        )
    
    try:
        # Get cart
        cart = cart_manager.get(cart_id)
        
        # Remove item
        cart.remove_item(item_id)
        
        # Redirect back to cart
        return RedirectResponse(url="/cart", status_code=303)
    
    except Exception as e:
        logger.error(f"Error removing item from cart: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to remove item from cart: {str(e)}"}
        )

@router.post("/cart/clear")
async def clear_cart(request: Request):
    """Clear all items from the cart."""
    cart_id = request.session.get("cart_id")
    
    if cart_id:
        try:
            # Get cart
            cart = cart_manager.get(cart_id)
            
            # Clear cart
            cart.clear()
            
            # Redirect back to cart
            return RedirectResponse(url="/cart", status_code=303)
        
        except Exception as e:
            logger.error(f"Error clearing cart: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Failed to clear cart: {str(e)}"}
            )
    
    # No active cart, just redirect to cart page
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