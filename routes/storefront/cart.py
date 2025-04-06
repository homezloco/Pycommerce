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
tenant_manager = None
product_manager = None
cart_manager = None

# Will initialize these in setup_routes to avoid circular imports

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
                # Try to get product from SDK manager first
                product = None
                try:
                    product = product_manager.get(item.product_id)
                except Exception as e:
                    logger.warning(f"SDK product manager failed to find product {item.product_id}: {str(e)}")
                
                # If product not found in SDK manager, try the database directly
                if not product:
                    try:
                        # Import directly to avoid circular imports
                        from models import Product
                        from app import app
                        
                        logger.info(f"Looking up product {item.product_id} directly in database")
                        with app.app_context():
                            db_product = Product.query.filter_by(id=item.product_id).first()
                            
                        if db_product:
                            # Convert SQLAlchemy model to SDK format
                            from pycommerce.models.product import Product as SDKProduct
                            
                            logger.info(f"Found product in database: {db_product.name}")
                            product = SDKProduct(
                                id=db_product.id,
                                name=db_product.name,
                                sku=db_product.sku,
                                description=db_product.description or "",
                                price=db_product.price,
                                stock=db_product.stock,
                                categories=db_product.categories or []
                            )
                            
                            # Add to SDK manager for future use
                            try:
                                # Store the product in the SDK manager's cache
                                product_manager._products[product.id] = product
                                product_manager._sku_index[product.sku] = product.id
                                logger.info(f"Added product {product.id} to SDK manager cache")
                            except Exception as cache_error:
                                logger.warning(f"Failed to cache product in SDK manager: {str(cache_error)}")
                    except Exception as db_error:
                        logger.error(f"Error accessing database for product: {str(db_error)}")
                
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
        
        # Check if product exists - first try the SDK manager
        product = None
        try:
            product = product_manager.get(product_id)
        except Exception as e:
            logger.warning(f"SDK product manager failed to find product {product_id}: {str(e)}")
            
        # If product not found in SDK manager, try the database directly
        if not product:
            try:
                # Import directly to avoid circular imports
                from models import Product
                from app import app
                
                logger.info(f"Looking up product {product_id} directly in database")
                with app.app_context():
                    db_product = Product.query.filter_by(id=product_id).first()
                    
                if db_product:
                    # Convert SQLAlchemy model to SDK format
                    from pycommerce.models.product import Product as SDKProduct
                    
                    logger.info(f"Found product in database: {db_product.name}")
                    product = SDKProduct(
                        id=db_product.id,
                        name=db_product.name,
                        sku=db_product.sku,
                        description=db_product.description or "",
                        price=db_product.price,
                        stock=db_product.stock,
                        categories=db_product.categories or []
                    )
                    
                    # Add to SDK manager for future use
                    try:
                        # Store the product in the SDK manager's cache
                        product_manager._products[product.id] = product
                        product_manager._sku_index[product.sku] = product.id
                        logger.info(f"Added product {product.id} to SDK manager cache")
                    except Exception as cache_error:
                        logger.warning(f"Failed to cache product in SDK manager: {str(cache_error)}")
            except Exception as db_error:
                logger.error(f"Error accessing database for product: {str(db_error)}")
                
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
    global templates, tenant_manager, product_manager, cart_manager
    templates = app_templates
    
    # Try to load Flask app managers to replace SDK managers
    try:
        # Import managers one by one to avoid circular import errors
        try:
            from managers import ProductManager as FlaskProductManager
            product_manager = FlaskProductManager()
            logger.info("Loaded Flask ProductManager")
        except Exception as product_err:
            logger.warning(f"Error loading Flask ProductManager: {product_err}")
            # Initialize with SDK manager as fallback
            from pycommerce.models.product import ProductManager as SDKProductManager
            product_manager = SDKProductManager()
            logger.info("Initialized SDK ProductManager as fallback")
            
        try:
            from managers import CartManager as FlaskCartManager
            cart_manager = FlaskCartManager()
            logger.info("Loaded Flask CartManager")
        except Exception as cart_err:
            logger.warning(f"Error loading Flask CartManager: {cart_err}")
            # Initialize with SDK manager as fallback
            from pycommerce.models.cart import CartManager as SDKCartManager
            cart_manager = SDKCartManager()
            logger.info("Initialized SDK CartManager as fallback")
            
        try:
            from pycommerce.models.tenant import TenantManager as SDKTenantManager
            tenant_manager = SDKTenantManager()
            logger.info("Initialized SDK TenantManager")
        except Exception as tenant_err:
            logger.warning(f"Error initializing SDK TenantManager: {tenant_err}")
            
        logger.info("Finished loading managers")
    except Exception as e:
        logger.error(f"General error loading managers: {e}")
        # We'll keep using the SDK managers as fallback
        
    return router