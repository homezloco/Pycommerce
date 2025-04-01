"""
Web server with FastAPI and Jinja2 templates for PyCommerce.

This file provides a web interface for the PyCommerce platform using FastAPI
and HTML templates.
"""

import os
import logging
import uvicorn
from fastapi import FastAPI, Depends, Query, HTTPException, Request, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from starlette.middleware.sessions import SessionMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize PyCommerce SDK
from pycommerce.core.db import init_db
from pycommerce.core.migrations import init_migrations
from pycommerce.models.tenant import TenantManager
from pycommerce.models.product import ProductManager
from pycommerce.models.user import UserManager
from pycommerce.api.routes import products as products_router
from pycommerce.api.routes import cart as cart_router
from pycommerce.api.routes import checkout as checkout_router
from pycommerce.api.routes import users as users_router

# Initialize the database
init_db()

# Initialize migrations
try:
    init_migrations()
except Exception as e:
    logger.warning(f"Error initializing migrations: {str(e)}")

# Initialize managers
tenant_manager = TenantManager()
product_manager = ProductManager()
user_manager = UserManager()

# Initialize cart and order managers
from pycommerce.models.cart import CartManager
from pycommerce.models.order import OrderManager

cart_manager = CartManager()
order_manager = OrderManager()

# Create the FastAPI app
app = FastAPI(
    title="PyCommerce Web",
    description="Web interface for PyCommerce Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add session middleware for cart functionality
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SESSION_SECRET", "supersecretkey"))

# Setup user manager in the routes
users_router.set_user_manager(user_manager)
cart_router.set_cart_manager(cart_manager)
checkout_router.set_order_manager(order_manager)

# Set product manager for the cart and checkout routes
products_router.set_product_manager(product_manager)

# Include API routes
app.include_router(products_router.router, prefix="/api/products", tags=["products"])
app.include_router(cart_router.router, prefix="/api/cart", tags=["cart"])
app.include_router(checkout_router.router, prefix="/api/checkout", tags=["checkout"])
app.include_router(users_router.router, prefix="/api/users", tags=["users"])

# Set up templates
templates = Jinja2Templates(directory="templates")

# Endpoints for HTML templates
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Get cart data for navigation
    cart_id = request.session.get("cart_id")
    cart_item_count = 0
    
    if cart_id:
        try:
            cart = cart_manager.get(cart_id)
            cart_item_count = sum(item.quantity for item in cart.items)
        except Exception:
            pass
            
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "cart_item_count": cart_item_count
        }
    )

@app.get("/stores", response_class=HTMLResponse)
async def stores(request: Request):
    tenants = []
    try:
        tenants_list = tenant_manager.list() or []
        tenants = [
            {
                "id": str(t.id),
                "name": t.name,
                "slug": t.slug,
                "domain": t.domain if hasattr(t, 'domain') else None,
                "active": t.active if hasattr(t, 'active') else True
            }
            for t in tenants_list if t and hasattr(t, 'id')
        ]
    except Exception as e:
        logger.error(f"Error fetching tenants: {str(e)}")
    
    # Get cart data for navigation
    cart_id = request.session.get("cart_id")
    cart_item_count = 0
    
    if cart_id:
        try:
            cart = cart_manager.get(cart_id)
            cart_item_count = sum(item.quantity for item in cart.items)
        except Exception:
            pass
    
    return templates.TemplateResponse(
        "stores.html", 
        {
            "request": request, 
            "tenants": tenants,
            "cart_item_count": cart_item_count
        }
    )

@app.get("/products", response_class=HTMLResponse)
async def products(
    request: Request,
    tenant: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None
):
    # Get all tenants for the dropdown
    tenants = []
    try:
        tenants_list = tenant_manager.list() or []
        tenants = [
            {
                "id": str(t.id),
                "name": t.name,
                "slug": t.slug
            }
            for t in tenants_list if t and hasattr(t, 'id')
        ]
    except Exception as e:
        logger.error(f"Error fetching tenants: {str(e)}")
    
    # Get filtered products
    products_list = []
    tenant_obj = None
    
    if tenant:
        # Try to get tenant by slug
        try:
            tenant_obj = tenant_manager.get_by_slug(tenant)
        except Exception as e:
            logger.warning(f"Tenant not found with slug '{tenant}': {str(e)}")
    
    try:
        # Get all products with filters
        all_products = product_manager.list(
            category=category,
            min_price=min_price,
            max_price=max_price,
            in_stock=in_stock
        )
        
        # Filter by tenant if specified
        if tenant_obj and hasattr(tenant_obj, 'id'):
            tenant_products = []
            for p in all_products:
                if hasattr(p, 'metadata') and p.metadata.get('tenant_id') == str(tenant_obj.id):
                    tenant_products.append(p)
            products_to_show = tenant_products
        else:
            products_to_show = all_products
        
        # Format products for template
        if products_to_show:
            products_list = [
                {
                    "id": str(p.id) if p and hasattr(p, 'id') else None,
                    "name": p.name if p and hasattr(p, 'name') else 'Unnamed Product',
                    "description": p.description if p and hasattr(p, 'description') else None,
                    "price": p.price if p and hasattr(p, 'price') else 0.0,
                    "sku": p.sku if p and hasattr(p, 'sku') else None,
                    "stock": p.stock if p and hasattr(p, 'stock') else 0,
                    "categories": p.categories if p and hasattr(p, 'categories') else []
                }
                for p in products_to_show if p
            ]
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
    
    # Prepare filter values for the template
    filters = {
        "category": category,
        "min_price": min_price,
        "max_price": max_price,
        "in_stock": in_stock
    }
    
    # Get cart data for navigation
    cart_id = request.session.get("cart_id")
    cart_item_count = 0
    
    if cart_id:
        try:
            cart = cart_manager.get(cart_id)
            cart_item_count = sum(item.quantity for item in cart.items)
        except Exception:
            pass
    
    return templates.TemplateResponse(
        "products.html", 
        {
            "request": request, 
            "products": products_list,
            "tenants": tenants,
            "selected_tenant": tenant,
            "filters": filters,
            "cart_item_count": cart_item_count
        }
    )

@app.get("/store/{slug}", response_class=HTMLResponse)
async def store(
    request: Request,
    slug: str,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None
):
    tenant_obj = None
    try:
        tenant_obj = tenant_manager.get_by_slug(slug)
    except Exception as e:
        logger.warning(f"Tenant not found with slug '{slug}': {str(e)}")
        # Redirect to stores page if tenant not found
        return RedirectResponse(url="/stores")
    
    tenant_data = {
        "id": str(tenant_obj.id),
        "name": tenant_obj.name,
        "slug": tenant_obj.slug,
        "domain": tenant_obj.domain if hasattr(tenant_obj, 'domain') else None
    }
    
    # Get products for this tenant
    products_list = []
    try:
        # Get all products with filters
        all_products = product_manager.list(
            category=category,
            min_price=min_price,
            max_price=max_price,
            in_stock=in_stock
        )
        
        # Filter by tenant
        tenant_products = []
        for p in all_products:
            if hasattr(p, 'metadata') and p.metadata.get('tenant_id') == str(tenant_obj.id):
                tenant_products.append(p)
        
        # Format products for template
        if tenant_products:
            products_list = [
                {
                    "id": str(p.id) if p and hasattr(p, 'id') else None,
                    "name": p.name if p and hasattr(p, 'name') else 'Unnamed Product',
                    "description": p.description if p and hasattr(p, 'description') else None,
                    "price": p.price if p and hasattr(p, 'price') else 0.0,
                    "sku": p.sku if p and hasattr(p, 'sku') else None,
                    "stock": p.stock if p and hasattr(p, 'stock') else 0,
                    "categories": p.categories if p and hasattr(p, 'categories') else []
                }
                for p in tenant_products if p
            ]
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
    
    # Prepare filter values for the template
    filters = {
        "category": category,
        "min_price": min_price,
        "max_price": max_price,
        "in_stock": in_stock
    }
    
    # Get cart data for navigation
    cart_id = request.session.get("cart_id")
    cart_item_count = 0
    
    if cart_id:
        try:
            cart = cart_manager.get(cart_id)
            cart_item_count = sum(item.quantity for item in cart.items)
        except Exception:
            pass
    
    return templates.TemplateResponse(
        "store/index.html", 
        {
            "request": request, 
            "tenant": tenant_data,
            "products": products_list,
            "filters": filters,
            "cart_item_count": cart_item_count
        }
    )

# API endpoint to generate sample data
@app.get("/api/generate-sample-data")
async def generate_sample_data():
    try:
        created_tenants = []
        created_products = []
        
        # Check if tenants already exist - don't duplicate them
        try:
            existing_tenants = tenant_manager.list() or []
            existing_slugs = [t.slug for t in existing_tenants if t and hasattr(t, 'slug')] 
            
            # If we already have demo tenants, return them instead of creating duplicates
            if 'demo1' in existing_slugs and 'demo2' in existing_slugs:
                return RedirectResponse(url="/stores")
        except Exception as e:
            logger.warning(f"Error checking existing tenants: {str(e)}")
            existing_slugs = []
        
        # Create tenants
        tenant1 = None
        tenant2 = None
        
        if 'demo1' not in existing_slugs:
            try:
                tenant1 = tenant_manager.create(
                    name="Demo Store 1",
                    slug="demo1",
                    domain="demo1.pycommerce.example"
                )
                created_tenants.append(tenant1)
                logger.info(f"Created tenant: {tenant1.name}")
            except Exception as e:
                logger.error(f"Error creating tenant 'demo1': {str(e)}")
        
        if 'demo2' not in existing_slugs:
            try:
                tenant2 = tenant_manager.create(
                    name="Demo Store 2",
                    slug="demo2",
                    domain="demo2.pycommerce.example"
                )
                created_tenants.append(tenant2)
                logger.info(f"Created tenant: {tenant2.name}")
            except Exception as e:
                logger.error(f"Error creating tenant 'demo2': {str(e)}")
        
        # Create products for tenant 1
        if tenant1 and hasattr(tenant1, 'id'):
            for i in range(1, 6):
                try:
                    # Store tenant_id in metadata to associate with tenant
                    metadata = {"tenant_id": str(tenant1.id)}
                    categories = ["demo", f"price-tier-{i}", "store1"]
                    
                    product = product_manager.create({
                        "name": f"Product {i} for Demo Store 1",
                        "description": f"This is product {i} for tenant 1",
                        "price": 10.0 * i,
                        "sku": f"DEMO1-PROD-{i}",
                        "stock": 100,
                        "metadata": metadata,
                        "categories": categories
                    })
                    created_products.append(product)
                    logger.info(f"Created product for tenant1: {product.name}")
                except Exception as e:
                    logger.error(f"Error creating product for tenant1: {str(e)}")
            
        # Create products for tenant 2
        if tenant2 and hasattr(tenant2, 'id'):
            for i in range(1, 6):
                try:
                    # Store tenant_id in metadata to associate with tenant
                    metadata = {"tenant_id": str(tenant2.id)}
                    categories = ["demo", f"price-tier-{i}", "store2", "premium"]
                    
                    product = product_manager.create({
                        "name": f"Product {i} for Demo Store 2",
                        "description": f"This is product {i} for tenant 2",
                        "price": 20.0 * i,
                        "sku": f"DEMO2-PROD-{i}",
                        "stock": 100,
                        "metadata": metadata,
                        "categories": categories
                    })
                    created_products.append(product)
                    logger.info(f"Created product for tenant2: {product.name}")
                except Exception as e:
                    logger.error(f"Error creating product for tenant2: {str(e)}")
        
        return RedirectResponse(url="/stores")
    except Exception as e:
        logger.error(f"Error generating sample data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper function to get or create a cart from session
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


# Cart routes
@app.get("/cart", response_class=HTMLResponse)
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


@app.post("/cart/add", response_class=RedirectResponse)
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


@app.post("/cart/update", response_class=RedirectResponse)
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


@app.post("/cart/remove", response_class=RedirectResponse)
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


@app.post("/cart/clear", response_class=RedirectResponse)
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


# Checkout routes
@app.get("/checkout", response_class=HTMLResponse)
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


@app.post("/checkout/process", response_class=RedirectResponse)
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
            "phone": phone
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
        
        # Create a simple mock payment
        if payment_method == "credit":
            payment_id = f"CREDIT-{uuid4().hex[:8]}"
        else:
            payment_id = f"PAYPAL-{uuid4().hex[:8]}"
        
        # Update order with payment info
        order_manager.update_payment(order.id, payment_id)
        
        # Redirect to confirmation page
        return RedirectResponse(url="/confirmation", status_code=303)
        
    except Exception as e:
        logger.error(f"Error processing checkout: {str(e)}")
        # Redirect back to checkout page
        return RedirectResponse(url="/checkout", status_code=303)


@app.get("/confirmation", response_class=HTMLResponse)
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


# API health check
@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "message": "PyCommerce Platform is running with FastAPI and uvicorn."
    }

if __name__ == "__main__":
    uvicorn.run("web_server:app", host="0.0.0.0", port=5000, reload=True)