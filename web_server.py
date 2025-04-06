"""
Web server with FastAPI and Jinja2 templates for PyCommerce.

This file provides a web interface for the PyCommerce platform using FastAPI
and HTML templates.
"""

import os
import logging
import uvicorn
from datetime import datetime
from fastapi import FastAPI, Depends, Query, HTTPException, Request, Form, Cookie, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional, List, Dict, Any, Union
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
from pycommerce.plugins.payment.config import (
    STRIPE_API_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_ENABLED,
    PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, PAYPAL_ENABLED, PAYPAL_SANDBOX
)
from pycommerce.plugins.ai.providers import (
    AIProvider, OpenAIProvider, GeminiProvider, DeepSeekProvider, OpenRouterProvider
)
from pycommerce.plugins.ai.config import get_ai_providers, load_ai_config
from pycommerce.api.routes import checkout as checkout_router
from pycommerce.api.routes import users as users_router
from pycommerce.services.media_service import MediaService
from pycommerce.api.routes import media as media_router

# Import plugin modules
from pycommerce.plugins import StripePaymentPlugin, StandardShippingPlugin

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

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

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

# Import and include AI routes
from pycommerce.api.routes import ai
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])

# Include media routes
app.include_router(media_router.router, prefix="/api/media", tags=["media"])

# Initialize services
media_service = MediaService()

# Set up templates
templates = Jinja2Templates(directory="templates")

# Get TinyMCE API key from environment
# No need for external API keys with Quill.js

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
    
    # Get theme settings from tenant if available
    theme_settings = {}
    if tenant_obj and hasattr(tenant_obj, 'settings') and tenant_obj.settings:
        theme_settings = tenant_obj.settings.get('theme', {})
    
    return templates.TemplateResponse(
        "store/index.html", 
        {
            "request": request, 
            "tenant": tenant_data,
            "products": products_list,
            "filters": filters,
            "cart_item_count": cart_item_count,
            "theme": theme_settings
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

# Admin routes for dashboard and management
@app.get("/admin", response_class=HTMLResponse)
@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, status_message: Optional[str] = None, status_type: str = "info"):
    """Admin dashboard page."""
    # Get all tenants for the store selector
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
        
        # Get selected tenant from query param or session
        selected_tenant = request.query_params.get('tenant')
        if not selected_tenant and tenants:
            selected_tenant = tenants[0]["slug"]
        
        # Get cart item count if available
        cart_item_count = 0
        session = request.session
        if 'cart_id' in session:
            try:
                cart_id = session['cart_id']
                cart = cart_manager.get(cart_id)
                cart_item_count = sum(item.quantity for item in cart.items)
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Error fetching tenants: {str(e)}")
        if status_message is None:
            status_message = f"Error fetching tenants: {str(e)}"
            status_type = "danger"
        tenants = []
        selected_tenant = None
        cart_item_count = 0
    
    return templates.TemplateResponse(
        "admin/dashboard.html", 
        {
            "request": request,
            "active_page": "dashboard",
            "tenants": tenants,
            "selected_tenant": selected_tenant,
            "cart_item_count": cart_item_count,
            "status_message": status_message,
            "status_type": status_type
        }
    )

# Admin store selector (for changing between stores)
@app.get("/admin/change-store", response_class=RedirectResponse)
async def admin_change_store(request: Request, tenant: str = ""):
    """Change the selected store for admin management."""
    redirect_url = request.query_params.get('redirect_url', '/admin')
    if tenant:
        return RedirectResponse(url=f"{redirect_url}?tenant={tenant}", status_code=303)
    return RedirectResponse(url=redirect_url, status_code=303)

# Admin store settings
@app.get("/admin/store-settings", response_class=HTMLResponse)
async def admin_store_settings(
    request: Request, 
    status_message: Optional[str] = None, 
    status_type: str = "info",
    tab: Optional[str] = None,
    provider: Optional[str] = None
):
    """Admin page for managing store settings."""
    # Get all tenants for the store selector
    tenants = []
    selected_tenant = None
    
    try:
        tenants_list = tenant_manager.list() or []
        tenants = [
            {
                "id": str(t.id),
                "name": t.name,
                "slug": t.slug,
                "domain": t.domain if hasattr(t, 'domain') else None,
                "active": t.active if hasattr(t, 'active') else True,
                "settings": t.settings if hasattr(t, 'settings') else {}
            }
            for t in tenants_list if t and hasattr(t, 'id')
        ]
        
        # Get selected tenant from query param
        selected_tenant_slug = request.query_params.get('tenant')
        if selected_tenant_slug:
            for tenant in tenants:
                if tenant["slug"] == selected_tenant_slug:
                    selected_tenant = tenant
                    break
        elif tenants:
            selected_tenant = tenants[0]
            selected_tenant_slug = selected_tenant["slug"]
        
        # Get cart item count if available
        cart_item_count = 0
        session = request.session
        if 'cart_id' in session:
            try:
                cart_id = session['cart_id']
                cart = cart_manager.get(cart_id)
                cart_item_count = sum(item.quantity for item in cart.items)
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Error fetching tenants: {str(e)}")
        if status_message is None:
            status_message = f"Error fetching tenants: {str(e)}"
            status_type = "danger"
        tenants = []
        cart_item_count = 0
        
    # For AI Configuration tab
    ai_providers = []
    active_provider = None
    selected_provider = None
    field_values = {}
    
    if tab == "ai" or provider:
        try:
            # Get AI providers
            ai_providers = get_ai_providers()
            
            # Get active provider
            tenant_id = selected_tenant["id"] if selected_tenant else None
            config = load_ai_config(tenant_id)
            active_provider = config.get("active_provider", "openai")
            
            # Default to first provider if none selected
            selected_provider_id = provider or active_provider
            selected_provider = next((p for p in ai_providers if p["id"] == selected_provider_id), ai_providers[0])
            
            # Get provider configuration
            provider_config = config.get("provider_config", {}) 
            
            if provider_config:
                for field in selected_provider["fields"]:
                    if field["id"] in provider_config:
                        field_values[field["id"]] = provider_config[field["id"]]
        except Exception as e:
            logger.error(f"Error loading AI configuration: {str(e)}")
            if status_message is None:
                status_message = f"Error loading AI configuration: {str(e)}"
                status_type = "danger"
    
    return templates.TemplateResponse(
        "admin/store_settings.html", 
        {
            "request": request,
            "active_page": "store_settings",
            "tenants": tenants,
            "selected_tenant": selected_tenant_slug,
            "tenant": selected_tenant,
            "cart_item_count": cart_item_count,
            "status_message": status_message,
            "status_type": status_type,
            # Tab selection
            "tab": tab,
            # AI Config tab data
            "ai_providers": ai_providers,
            "active_provider": active_provider,
            "selected_provider": selected_provider,
            "field_values": field_values
        }
    )

# Admin store settings update
@app.post("/admin/store-settings/update", response_class=RedirectResponse)
async def admin_store_settings_update(
    request: Request,
    tenant_id: str = Form(...),
    store_name: str = Form(...),
    store_slug: str = Form(...),
    store_domain: Optional[str] = Form(None),
    store_active: bool = Form(False),
    store_description: Optional[str] = Form(None),
    store_email: Optional[str] = Form(None),
    store_phone: Optional[str] = Form(None)
):
    """Update store settings."""
    try:
        # Get tenant object
        tenant = tenant_manager.get(tenant_id)
        
        # Update basic tenant info
        tenant.name = store_name
        tenant.slug = store_slug
        tenant.domain = store_domain
        tenant.active = store_active
        
        # Update settings
        if not hasattr(tenant, 'settings') or tenant.settings is None:
            tenant.settings = {}
            
        tenant.settings['email'] = store_email
        tenant.settings['phone'] = store_phone
        tenant.settings['description'] = store_description
        
        # Update tenant
        tenant_manager.update(tenant)
        
        return RedirectResponse(
            url=f"/admin/store-settings?tenant={store_slug}&status_message=Store+settings+updated+successfully&status_type=success", 
            status_code=303
        )
    except Exception as e:
        error_message = str(e).replace(" ", "+")
        return RedirectResponse(
            url=f"/admin/store-settings?tenant={store_slug}&status_message={error_message}&status_type=danger", 
            status_code=303
        )

# Admin theme settings
@app.get("/admin/theme-settings", response_class=HTMLResponse)
async def admin_theme_settings(request: Request, status_message: Optional[str] = None, status_type: str = "info"):
    """Admin page for managing theme settings."""
    # Get all tenants for the store selector
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
        
        # Get selected tenant from query param
        selected_tenant_slug = request.query_params.get('tenant')
        if not selected_tenant_slug and tenants:
            selected_tenant_slug = tenants[0]["slug"]
            
        # Get the tenant details
        tenant = None
        theme_settings = {}
        if selected_tenant_slug:
            tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
            if tenant_obj:
                tenant = {
                    "id": str(tenant_obj.id),
                    "name": tenant_obj.name,
                    "slug": tenant_obj.slug,
                    "domain": tenant_obj.domain,
                    "active": tenant_obj.active
                }
                
                # Get theme settings from tenant settings
                if hasattr(tenant_obj, 'settings') and tenant_obj.settings:
                    if 'theme' in tenant_obj.settings:
                        theme_settings = tenant_obj.settings['theme']
        
        # Get cart item count if available
        cart_item_count = 0
        session = request.session
        if 'cart_id' in session:
            try:
                cart_id = session['cart_id']
                cart = cart_manager.get(cart_id)
                cart_item_count = sum(item.quantity for item in cart.items)
            except Exception:
                pass
                
    except Exception as e:
        logger.error(f"Error loading theme settings: {str(e)}")
        if status_message is None:
            status_message = f"Error loading theme settings: {str(e)}"
            status_type = "danger"
    
    return templates.TemplateResponse(
        "admin/theme_settings.html", 
        {
            "request": request,
            "active_page": "theme_settings",
            "tenants": tenants,
            "tenant": tenant,
            "theme": theme_settings,
            "cart_item_count": cart_item_count,
            "success": status_message if status_type == "success" else None,
            "error": status_message if status_type == "danger" else None
        }
    )

@app.post("/admin/theme-settings", response_class=RedirectResponse)
async def admin_save_theme_settings(request: Request):
    """Save theme settings for a tenant."""
    try:
        form_data = await request.form()
        
        # Get the selected tenant from the query parameters
        selected_tenant_slug = request.query_params.get('tenant')
        
        if not selected_tenant_slug:
            raise ValueError("No tenant selected")
        
        # Get the tenant
        tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
        if not tenant_obj:
            raise ValueError(f"Tenant not found: {selected_tenant_slug}")
        
        # Create theme settings dictionary
        theme_settings = {
            # Colors
            "primary_color": form_data.get("primary_color", "#007bff"),
            "secondary_color": form_data.get("secondary_color", "#6c757d"),
            "background_color": form_data.get("background_color", "#ffffff"),
            "text_color": form_data.get("text_color", "#212529"),
            
            # Typography
            "font_family": form_data.get("font_family", "'Open Sans', sans-serif"),
            "heading_font_family": form_data.get("heading_font_family", "inherit"),
            "base_font_size": int(form_data.get("base_font_size", "16")),
            "heading_scale": form_data.get("heading_scale", "moderate"),
            
            # Layout
            "container_width": form_data.get("container_width", "standard"),
            "border_radius": int(form_data.get("border_radius", "4")),
            "spacing_scale": form_data.get("spacing_scale", "moderate"),
            
            # Store Elements
            "header_style": form_data.get("header_style", "standard"),
            "product_card_style": form_data.get("product_card_style", "standard"),
            "button_style": form_data.get("button_style", "standard"),
            
            # Custom CSS
            "custom_css": form_data.get("custom_css", ""),
            
            # Updated timestamp
            "updated_at": datetime.now().isoformat()
        }
        
        # Update tenant theme settings
        tenant_manager.update_theme(tenant_obj.id, theme_settings)
        
        status_message = "Theme settings saved successfully"
        status_type = "success"
    except Exception as e:
        logger.error(f"Error saving theme settings: {str(e)}")
        status_message = f"Error saving theme settings: {str(e)}"
        status_type = "danger"
    
    # Redirect back to the theme settings page
    redirect_url = f"/admin/theme-settings?tenant={selected_tenant_slug}&status_message={status_message}&status_type={status_type}"
    return RedirectResponse(url=redirect_url, status_code=303)

# AI Configuration Routes
@app.get("/admin/ai-config", response_class=HTMLResponse)
async def admin_ai_config(
    request: Request, 
    status_message: Optional[str] = None, 
    status_type: str = "info"
):
    """Admin page for AI configuration."""
    # Get all tenants for the store selector
    tenants = []
    selected_tenant = None
    
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
        
        # Get selected tenant from query param
        selected_tenant_slug = request.query_params.get('tenant')
        if selected_tenant_slug:
            for tenant in tenants:
                if tenant["slug"] == selected_tenant_slug:
                    selected_tenant = tenant
                    break
        elif tenants:
            selected_tenant = tenants[0]
            selected_tenant_slug = selected_tenant["slug"]
        
        # Get cart item count if available
        cart_item_count = 0
        session = request.session
        if 'cart_id' in session:
            try:
                cart_id = session['cart_id']
                cart = cart_manager.get(cart_id)
                cart_item_count = sum(item.quantity for item in cart.items)
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Error fetching tenants: {str(e)}")
        if status_message is None:
            status_message = f"Error fetching tenants: {str(e)}"
            status_type = "danger"
        tenants = []
        cart_item_count = 0
    
    # Get AI providers
    ai_providers = get_ai_providers()
    
    # Get active provider
    tenant_id = selected_tenant["id"] if selected_tenant else None
    config = load_ai_config(tenant_id)
    active_provider = config.get("active_provider", "openai")
    
    # Default to first provider if none selected
    selected_provider_id = request.query_params.get('provider', active_provider)
    selected_provider = next((p for p in ai_providers if p["id"] == selected_provider_id), ai_providers[0])
    
    # Get provider configuration
    field_values = {}
    provider_config = config.get("provider_config", {}) 
    
    if provider_config:
        for field in selected_provider["fields"]:
            if field["id"] in provider_config:
                field_values[field["id"]] = provider_config[field["id"]]
    
    return templates.TemplateResponse(
        "admin/ai_config.html", 
        {
            "request": request,
            "active_page": "ai_config",
            "tenants": tenants,
            "selected_tenant": selected_tenant_slug,
            "ai_providers": ai_providers,
            "active_provider": active_provider,
            "selected_provider": selected_provider,
            "field_values": field_values,
            "cart_item_count": cart_item_count,
            "status_message": status_message,
            "status_type": status_type
        }
    )

@app.get("/admin/ai-config/configure/{provider_id}", response_class=RedirectResponse)
async def admin_ai_config_redirect(provider_id: str, tenant: Optional[str] = None):
    """Redirect to store settings page with AI tab active and selected provider."""
    url = f"/admin/store-settings?tab=ai&provider={provider_id}"
    if tenant:
        url += f"&tenant={tenant}"
    return RedirectResponse(url=url, status_code=303)

@app.post("/admin/store-settings/ai/save", response_class=RedirectResponse)
async def admin_ai_config_save(
    request: Request,
    provider_id: str = Form(...),
    tenant: str = Form(...)
):
    """Save AI provider configuration from store settings."""
    try:
        # Get form data for provider configuration
        form_data = await request.form()
        config_data = {}
        
        # Get provider info to know which fields to expect
        provider_info = next((p for p in get_ai_providers() if p["id"] == provider_id), None)
        
        if not provider_info:
            return RedirectResponse(
                url=f"/admin/store-settings?tab=ai&status_message=Invalid provider: {provider_id}&status_type=danger", 
                status_code=303
            )
        
        # Build configuration from form data
        for field in provider_info["fields"]:
            field_id = field["id"]
            if field_id in form_data:
                value = form_data[field_id]
                
                # Convert types as needed
                if field.get("type") == "number":
                    try:
                        value = float(value)
                    except ValueError:
                        pass
                
                config_data[field_id] = value
        
        # Get tenant object if tenant is specified
        tenant_obj = tenant_manager.get_by_slug(tenant) if tenant else None
        tenant_id = str(tenant_obj.id) if tenant_obj else None
        
        # Save configuration
        from pycommerce.models.plugin_config import PluginConfigManager
        config_manager = PluginConfigManager()
        config_manager.save_config(f"ai_{provider_id}", config_data, tenant_id)
        
        # Set status message
        status_message = f"{provider_info['name']} configuration saved successfully"
        status_type = "success"
    except Exception as e:
        logger.error(f"Error saving AI configuration: {str(e)}")
        status_message = f"Error saving AI configuration: {str(e)}"
        status_type = "danger"
    
    # Redirect back to store settings AI tab
    redirect_url = f"/admin/store-settings?tab=ai&provider={provider_id}&tenant={tenant}&status_message={status_message}&status_type={status_type}"
    return RedirectResponse(url=redirect_url, status_code=303)

@app.post("/admin/store-settings/ai/set-active", response_class=RedirectResponse)
async def admin_ai_config_set_active(
    request: Request,
    provider_id: str = Form(...),
    tenant: str = Form(...)
):
    """Set active AI provider from store settings."""
    try:
        # Get tenant object if tenant is specified
        tenant_obj = tenant_manager.get_by_slug(tenant) if tenant else None
        tenant_id = str(tenant_obj.id) if tenant_obj else None
        
        # Save active provider
        from pycommerce.models.plugin_config import PluginConfigManager
        config_manager = PluginConfigManager()
        config_manager.save_config("ai_active_provider", {"provider": provider_id}, tenant_id)
        
        # Set status message
        provider_info = next((p for p in get_ai_providers() if p["id"] == provider_id), None)
        provider_name = provider_info["name"] if provider_info else provider_id
        status_message = f"{provider_name} set as active AI provider"
        status_type = "success"
    except Exception as e:
        logger.error(f"Error setting active AI provider: {str(e)}")
        status_message = f"Error setting active AI provider: {str(e)}"
        status_type = "danger"
    
    # Redirect back to store settings AI tab
    redirect_url = f"/admin/store-settings?tab=ai&provider={provider_id}&tenant={tenant}&status_message={status_message}&status_type={status_type}"
    return RedirectResponse(url=redirect_url, status_code=303)

# Admin plugins page
@app.get("/admin/plugins", response_class=HTMLResponse)
async def admin_plugins(request: Request, status_message: Optional[str] = None, status_type: str = "info"):
    """Admin page for managing plugins."""
    # Get all tenants for the store selector
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
        
        # Get selected tenant from query param
        selected_tenant = request.query_params.get('tenant')
        if not selected_tenant and tenants:
            selected_tenant = tenants[0]["slug"]
        
        # Get cart item count if available
        cart_item_count = 0
        session = request.session
        if 'cart_id' in session:
            try:
                cart_id = session['cart_id']
                cart = cart_manager.get(cart_id)
                cart_item_count = sum(item.quantity for item in cart.items)
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Error fetching tenants: {str(e)}")
        if status_message is None:
            status_message = f"Error fetching tenants: {str(e)}"
            status_type = "danger"
        tenants = []
        selected_tenant = None
        cart_item_count = 0
    
    # Get available plugins
    from pycommerce.core.plugin import get_available_plugins
    plugins = get_available_plugins()
    
    return templates.TemplateResponse(
        "admin/plugins.html", 
        {
            "request": request,
            "active_page": "plugins",
            "tenants": tenants,
            "selected_tenant": selected_tenant,
            "plugins": plugins,
            "cart_item_count": cart_item_count,
            "status_message": status_message,
            "status_type": status_type
        }
    )

# Admin routes for store management
@app.get("/admin/stores", response_class=HTMLResponse)
async def admin_stores(request: Request, status_message: Optional[str] = None, status_type: str = "info"):
    """Admin page for managing stores (tenants)."""
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
        status_message = f"Error fetching stores: {str(e)}"
        status_type = "danger"
    
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
        "admin/stores.html", 
        {
            "request": request, 
            "active_page": "stores",
            "tenants": tenants,
            "cart_item_count": cart_item_count,
            "status_message": status_message,
            "status_type": status_type
        }
    )

async def admin_add_store(
    request: Request,
    name: str = Form(...),
    slug: str = Form(...),
    domain: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """Add a new store."""
    try:
        # Create new tenant
        metadata = {}
        if description:
            metadata["description"] = description
            
        tenant = tenant_manager.create(
            name=name,
            slug=slug,
            domain=domain,
            metadata=metadata
        )
        logger.info(f"Created tenant: {tenant.name}")
        
        # Redirect to stores page with success message
        return RedirectResponse(url="/admin/stores?status_message=Store+created+successfully&status_type=success", status_code=303)
    
    except Exception as e:
        logger.error(f"Error creating tenant: {str(e)}")
        # Redirect with error message
        error_message = f"Error creating store: {str(e)}"
        return RedirectResponse(
            url=f"/admin/stores?status_message={error_message}&status_type=danger", 
            status_code=303
        )

@app.get("/admin/stores/edit/{tenant_id}", response_class=HTMLResponse)
async def admin_edit_store(
    request: Request,
    tenant_id: str,
    status_message: Optional[str] = None, 
    status_type: str = "info"
):
    """Edit store page."""
    try:
        tenant_obj = tenant_manager.get(tenant_id)
        
        tenant = {
            "id": str(tenant_obj.id),
            "name": tenant_obj.name,
            "slug": tenant_obj.slug,
            "domain": tenant_obj.domain if hasattr(tenant_obj, 'domain') else None,
            "active": tenant_obj.active if hasattr(tenant_obj, 'active') else True,
            "description": tenant_obj.settings.get("description", "") if hasattr(tenant_obj, 'settings') else ""
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
            "admin/store_edit.html", 
            {
                "request": request, 
                "active_page": "stores",
                "tenant": tenant,
                "cart_item_count": cart_item_count,
                "status_message": status_message,
                "status_type": status_type
            }
        )
        
    except Exception as e:
        # Redirect with error message
        error_message = f"Error fetching store: {str(e)}"
        return RedirectResponse(
            url=f"/admin/stores?status_message={error_message}&status_type=danger", 
            status_code=303
        )

@app.post("/admin/stores/update/{tenant_id}", response_class=RedirectResponse)
async def admin_update_store(
    request: Request,
    tenant_id: str,
    name: str = Form(...),
    slug: str = Form(...),
    domain: Optional[str] = Form(None),
    active: bool = Form(False),
    description: Optional[str] = Form(None)
):
    """Update a store."""
    try:
        # Update tenant
        update_data = {
            "name": name,
            "slug": slug,
            "domain": domain,
            "active": active
        }
        
        # Update metadata if description exists
        tenant_obj = tenant_manager.get(tenant_id)
        metadata = getattr(tenant_obj, 'metadata', {}) or {}
        
        if description:
            metadata["description"] = description
            update_data["metadata"] = metadata
        
        tenant_manager.update(tenant_id, **update_data)
        logger.info(f"Updated tenant: {name}")
        
        # Redirect to stores page with success message
        return RedirectResponse(
            url="/admin/stores?status_message=Store+updated+successfully&status_type=success", 
            status_code=303
        )
    
    except Exception as e:
        logger.error(f"Error updating tenant: {str(e)}")
        # Redirect with error message
        error_message = f"Error updating store: {str(e)}"
        return RedirectResponse(
            url=f"/admin/stores?status_message={error_message}&status_type=danger", 
            status_code=303
        )

@app.get("/admin/stores/toggle/{tenant_id}", response_class=RedirectResponse)
async def admin_toggle_store(
    request: Request,
    tenant_id: str
):
    """Toggle store active status."""
    try:
        # Get current tenant
        tenant_obj = tenant_manager.get(tenant_id)
        
        # Toggle active status
        current_status = getattr(tenant_obj, 'active', True)
        new_status = not current_status
        
        # Update tenant
        tenant_manager.update(tenant_id, active=new_status)
        logger.info(f"Toggled tenant {tenant_obj.name} active status to {new_status}")
        
        # Redirect to stores page with success message
        status_action = "activated" if new_status else "deactivated"
        return RedirectResponse(
            url=f"/admin/stores?status_message=Store+{status_action}+successfully&status_type=success", 
            status_code=303
        )
    
    except Exception as e:
        logger.error(f"Error toggling tenant status: {str(e)}")
        # Redirect with error message
        error_message = f"Error updating store status: {str(e)}"
        return RedirectResponse(
            url=f"/admin/stores?status_message={error_message}&status_type=danger", 
            status_code=303
        )

@app.get("/admin/stores/delete/{tenant_id}", response_class=RedirectResponse)
async def admin_delete_store(
    request: Request,
    tenant_id: str
):
    """Delete a store."""
    try:
        # Delete tenant
        tenant_manager.delete(tenant_id)
        logger.info(f"Deleted tenant with ID: {tenant_id}")
        
        # Redirect to stores page with success message
        return RedirectResponse(
            url="/admin/stores?status_message=Store+deleted+successfully&status_type=success", 
            status_code=303
        )
    
    except Exception as e:
        logger.error(f"Error deleting tenant: {str(e)}")
        # Redirect with error message
        error_message = f"Error deleting store: {str(e)}"
        return RedirectResponse(
            url=f"/admin/stores?status_message={error_message}&status_type=danger", 
            status_code=303
        )

# Admin routes for product management
@app.get("/admin/products", response_class=HTMLResponse)
async def admin_products(
    request: Request,
    tenant: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for managing products."""
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
            max_price=max_price
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
            products_list = []
            for p in products_to_show:
                if not p:
                    continue
                
                # Get tenant name for the product
                tenant_name = "Unknown"
                tenant_id = p.metadata.get('tenant_id') if hasattr(p, 'metadata') else None
                
                if tenant_id:
                    try:
                        t = tenant_manager.get(tenant_id)
                        tenant_name = t.name
                    except Exception:
                        pass
                
                products_list.append({
                    "id": str(p.id) if hasattr(p, 'id') else None,
                    "name": p.name if hasattr(p, 'name') else 'Unnamed Product',
                    "description": p.description if hasattr(p, 'description') else None,
                    "price": p.price if hasattr(p, 'price') else 0.0,
                    "sku": p.sku if hasattr(p, 'sku') else None,
                    "stock": p.stock if hasattr(p, 'stock') else 0,
                    "categories": p.categories if hasattr(p, 'categories') else [],
                    "image_url": p.metadata.get('image_url') if hasattr(p, 'metadata') else None,
                    "tenant_id": tenant_id,
                    "tenant_name": tenant_name
                })
                
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        status_message = f"Error fetching products: {str(e)}"
        status_type = "danger"
    
    # Prepare filter values for the template
    filters = {
        "category": category,
        "min_price": min_price,
        "max_price": max_price
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
        "admin/products.html", 
        {
            "request": request, 
            "active_page": "products",
            "products": products_list,
            "tenants": tenants,
            "selected_tenant": tenant,
            "filters": filters,
            "cart_item_count": cart_item_count,
            "status_message": status_message,
            "status_type": status_type
        }
    )

@app.get("/admin/products/add", response_class=HTMLResponse)
async def admin_add_product_form(request: Request):
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
    
    # Get the selected tenant from the session
    selected_tenant_slug = request.session.get("selected_tenant")
    selected_tenant = None
    
    if selected_tenant_slug:
        try:
            selected_tenant = tenant_manager.get_by_slug(selected_tenant_slug)
        except Exception:
            pass
    
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
        "admin/product_add.html", 
        {
            "request": request,
            "active_page": "products",
            "tenants": tenants,
            "selected_tenant": selected_tenant,
            "cart_item_count": cart_item_count
        }
    )

@app.post("/admin/products/add", response_class=RedirectResponse)
async def admin_add_product(
    request: Request,
    tenant_id: str = Form(...),
    name: str = Form(...),
    sku: str = Form(...),
    price: float = Form(...),
    stock: int = Form(0),
    categories: Optional[str] = Form(""),
    image_url: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """Add a new product."""
    try:
        # Process categories string into list
        category_list = []
        if categories:
            category_list = [cat.strip() for cat in categories.split(",") if cat.strip()]
        
        # Prepare metadata
        metadata = {"tenant_id": tenant_id}
        if image_url:
            metadata["image_url"] = image_url
        
        # Create product
        product_data = {
            "name": name,
            "sku": sku,
            "price": price,
            "stock": stock,
            "categories": category_list,
            "description": description,
            "metadata": metadata
        }
        
        product = product_manager.create(product_data)
        logger.info(f"Created product: {product.name}")
        
        # Redirect to products page with success message
        return RedirectResponse(
            url="/admin/products?status_message=Product+created+successfully&status_type=success", 
            status_code=303
        )
    
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        # Redirect with error message
        error_message = f"Error creating product: {str(e)}"
        return RedirectResponse(
            url=f"/admin/products?status_message={error_message}&status_type=danger", 
            status_code=303
        )

@app.get("/admin/products/edit/{product_id}", response_class=HTMLResponse)
async def admin_edit_product(
    request: Request,
    product_id: str,
    status_message: Optional[str] = None, 
    status_type: str = "info"
):
    """Edit product page."""
    try:
        # Get product
        product_obj = product_manager.get(product_id)
        
        # Get tenant ID from metadata
        tenant_id = product_obj.metadata.get('tenant_id') if hasattr(product_obj, 'metadata') else None
        
        # Format product for template
        product = {
            "id": str(product_obj.id),
            "name": product_obj.name,
            "sku": product_obj.sku,
            "price": product_obj.price,
            "stock": product_obj.stock,
            "categories": product_obj.categories if hasattr(product_obj, 'categories') else [],
            "description": product_obj.description if hasattr(product_obj, 'description') else "",
            "image_url": product_obj.metadata.get('image_url') if hasattr(product_obj, 'metadata') else None,
            "tenant_id": tenant_id
        }
        
        # Get all tenants for the dropdown
        tenants = []
        try:
            tenants_list = tenant_manager.list() or []
            tenants = [
                {
                    "id": str(t.id),
                    "name": t.name
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
            "admin/product_edit.html", 
            {
                "request": request, 
                "active_page": "products",
                "product": product,
                "tenants": tenants,
                "cart_item_count": cart_item_count,
                "status_message": status_message,
                "status_type": status_type
            }
        )
        
    except Exception as e:
        logger.error(f"Error fetching product: {str(e)}")
        error_message = f"Error fetching product: {str(e)}"
        return RedirectResponse(
            url=f"/admin/products?status_message={error_message}&status_type=danger", 
            status_code=303
        )

@app.post("/admin/products/update/{product_id}", response_class=RedirectResponse)
async def admin_update_product(
    request: Request,
    product_id: str,
    tenant_id: str = Form(...),
    name: str = Form(...),
    sku: str = Form(...),
    price: float = Form(...),
    stock: int = Form(0),
    categories: Optional[str] = Form(""),
    image_url: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """Update a product."""
    try:
        # Process categories string into list
        category_list = []
        if categories:
            category_list = [cat.strip() for cat in categories.split(",") if cat.strip()]
        
        # Get existing product to preserve metadata
        product_obj = product_manager.get(product_id)
        metadata = getattr(product_obj, 'metadata', {}) or {}
        
        # Update metadata
        metadata["tenant_id"] = tenant_id
        if image_url:
            metadata["image_url"] = image_url
        
        # Update product
        update_data = {
            "name": name,
            "sku": sku,
            "price": price,
            "stock": stock,
            "categories": category_list,
            "description": description,
            "metadata": metadata
        }
        
        product_manager.update(product_id, **update_data)
        logger.info(f"Updated product: {name}")
        
        # Redirect to products page with success message
        return RedirectResponse(
            url="/admin/products?status_message=Product+updated+successfully&status_type=success", 
            status_code=303
        )
    
    except Exception as e:
        logger.error(f"Error updating product: {str(e)}")
        # Redirect with error message
        error_message = f"Error updating product: {str(e)}"
        return RedirectResponse(
            url=f"/admin/products?status_message={error_message}&status_type=danger", 
            status_code=303
        )

@app.get("/admin/products/delete/{product_id}", response_class=RedirectResponse)
async def admin_delete_product(
    request: Request,
    product_id: str
):
    """Delete a product."""
    try:
        # Delete product
        product_manager.delete(product_id)
        logger.info(f"Deleted product with ID: {product_id}")
        
        # Redirect to products page with success message
        return RedirectResponse(
            url="/admin/products?status_message=Product+deleted+successfully&status_type=success", 
            status_code=303
        )
    
    except Exception as e:
        logger.error(f"Error deleting product: {str(e)}")
        # Redirect with error message
        error_message = f"Error deleting product: {str(e)}"
        return RedirectResponse(
            url=f"/admin/products?status_message={error_message}&status_type=danger", 
            status_code=303
        )

# Admin routes for media management
"""
Order management route additions for web_server.py
"""

# Order management routes
@app.get("/admin/orders", response_class=HTMLResponse)
async def admin_orders(
    request: Request,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    email: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for order management."""
    # Get selected tenant
    selected_tenant_slug = request.cookies.get("selected_tenant", None)
    selected_tenant = None
    
    # Try to get tenant data
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
        
        if selected_tenant_slug:
            for t in tenants_list:
                if hasattr(t, 'slug') and t.slug == selected_tenant_slug:
                    selected_tenant = t
                    break
    except Exception as e:
        logger.error(f"Error fetching tenants: {str(e)}")
    
    # Initialize an empty list for orders
    orders = []
    from models import Order
    
    try:
        # Check if we have a tenant selected
        if selected_tenant and hasattr(selected_tenant, 'id'):
            # Build the query with filters
            query = Order.query.filter_by(tenant_id=str(selected_tenant.id))
            
            # Apply additional filters if provided
            if status:
                query = query.filter_by(status=status)
            
            if email:
                query = query.filter(Order.email.ilike(f"%{email}%"))
            
            if date_from:
                try:
                    from_date = datetime.strptime(date_from, "%Y-%m-%d")
                    query = query.filter(Order.created_at >= from_date)
                except Exception as e:
                    logger.warning(f"Invalid date_from format: {str(e)}")
            
            if date_to:
                try:
                    to_date = datetime.strptime(date_to, "%Y-%m-%d")
                    # Make to_date inclusive by setting it to the end of the day
                    to_date = to_date.replace(hour=23, minute=59, second=59)
                    query = query.filter(Order.created_at <= to_date)
                except Exception as e:
                    logger.warning(f"Invalid date_to format: {str(e)}")
            
            # Get orders sorted by created_at in descending order (newest first)
            orders = query.order_by(Order.created_at.desc()).all()
            logger.info(f"Found {len(orders)} orders for tenant {selected_tenant.slug}")
        else:
            logger.warning("No tenant selected for orders page")
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
    
    # Prepare template parameters
    template_params = {
        "request": request,
        "active_page": "orders",
        "tenants": tenants,
        "selected_tenant": selected_tenant_slug,
        "orders": orders,
        "filter_status": status,
        "filter_date_from": date_from,
        "filter_date_to": date_to,
        "filter_email": email,
        "status_message": status_message,
        "status_type": status_type
    }
    
    return templates.TemplateResponse("admin/orders.html", template_params)


@app.get("/admin/orders/{order_id}", response_class=HTMLResponse)
async def admin_order_detail(
    request: Request,
    order_id: str,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for viewing order details."""
    # Get selected tenant
    selected_tenant_slug = request.cookies.get("selected_tenant", None)
    
    # Try to get tenant data
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
    
    # Get order details
    order = None
    from models import Order, OrderItem
    
    try:
        # Get the order with items
        order = Order.query.filter_by(id=order_id).first()
        
        if not order:
            logger.warning(f"Order not found: {order_id}")
            return RedirectResponse(
                url=f"/admin/orders?status_message=Order+not+found&status_type=danger",
                status_code=303
            )
        
        # Load order items with product details
        order_items = OrderItem.query.filter_by(order_id=order_id).all()
        for item in order_items:
            try:
                # Get product details if available
                from models import Product
                item.product = Product.query.filter_by(id=item.product_id).first()
            except Exception as e:
                logger.warning(f"Could not load product for order item: {str(e)}")
                item.product = None
        
        # Assign items to the order
        order.items = order_items
        
        # Get order notes if any (depends on your data model)
        try:
            # This depends on your schema - adjust as needed
            order.notes = []  # Replace with actual notes query if you have them
        except Exception as e:
            logger.warning(f"Could not load order notes: {str(e)}")
            order.notes = []
        
        logger.info(f"Loaded order details for order {order_id}")
        
    except Exception as e:
        logger.error(f"Error fetching order details: {str(e)}")
        return RedirectResponse(
            url=f"/admin/orders?status_message=Error+loading+order+details&status_type=danger",
            status_code=303
        )
    
    # Prepare template parameters
    template_params = {
        "request": request,
        "active_page": "orders",
        "tenants": tenants,
        "selected_tenant": selected_tenant_slug,
        "order": order,
        "status_message": status_message,
        "status_type": status_type
    }
    
    return templates.TemplateResponse("admin/order_detail.html", template_params)


@app.get("/admin/orders/update-status/{order_id}", response_class=RedirectResponse)
async def admin_update_order_status(request: Request, order_id: str, status: str):
    """Update order status and redirect back to order details."""
    try:
        # Validate status
        valid_statuses = ['pending', 'paid', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded']
        if status not in valid_statuses:
            logger.warning(f"Invalid order status: {status}")
            return RedirectResponse(
                url=f"/admin/orders/{order_id}?status_message=Invalid+status&status_type=danger",
                status_code=303
            )
        
        # Update order status
        from models import Order
        order = Order.query.filter_by(id=order_id).first()
        
        if not order:
            logger.warning(f"Order not found: {order_id}")
            return RedirectResponse(
                url=f"/admin/orders?status_message=Order+not+found&status_type=danger",
                status_code=303
            )
        
        # Update the status
        old_status = order.status
        order.status = status
        order.updated_at = datetime.utcnow()
        
        # You could also add an entry to an order history/log table here
        
        # Save the changes
        from app import db
        db.session.commit()
        
        logger.info(f"Updated order {order_id} status from {old_status} to {status}")
        
        # Redirect back to order details with success message
        return RedirectResponse(
            url=f"/admin/orders/{order_id}?status_message=Order+status+updated+successfully&status_type=success",
            status_code=303
        )
        
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")
        return RedirectResponse(
            url=f"/admin/orders/{order_id}?status_message=Error+updating+order+status&status_type=danger",
            status_code=303
        )


@app.post("/admin/orders/add-note/{order_id}", response_class=RedirectResponse)
async def admin_add_order_note(
    request: Request,
    order_id: str,
    content: str = Form(...),
    notify_customer: Optional[str] = Form(None)
):
    """Add a note to an order."""
    try:
        # Validate order exists
        from models import Order
        order = Order.query.filter_by(id=order_id).first()
        
        if not order:
            logger.warning(f"Order not found: {order_id}")
            return RedirectResponse(
                url=f"/admin/orders?status_message=Order+not+found&status_type=danger",
                status_code=303
            )
        
        # For now, we'll just log the note (you'd typically save it to a database)
        # In a real implementation, you'd create an OrderNote model and save to DB
        logger.info(f"Added note to order {order_id}: {content}")
        
        # Check if we need to notify the customer
        should_notify = notify_customer == "1"
        if should_notify:
            # In a real implementation, you'd send an email to the customer here
            logger.info(f"Would notify customer {order.email} about note: {content}")
        
        # Redirect back to order details with success message
        return RedirectResponse(
            url=f"/admin/orders/{order_id}?status_message=Note+added+successfully&status_type=success",
            status_code=303
        )
        
    except Exception as e:
        logger.error(f"Error adding order note: {str(e)}")
        return RedirectResponse(
            url=f"/admin/orders/{order_id}?status_message=Error+adding+note&status_type=danger",
            status_code=303
        )

@app.get("/admin/media", response_class=HTMLResponse)
async def admin_media(
    request: Request,
    tenant: Optional[str] = None,
    file_type: Optional[str] = None,
    is_ai_generated: Optional[bool] = None,
    search: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for managing media files."""
    # Get all tenants for the store selector
    tenants = []
    selected_tenant = None
    
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
        
        # Get selected tenant from query param or session
        selected_tenant_slug = tenant or request.query_params.get('tenant')
        if not selected_tenant_slug and tenants:
            selected_tenant_slug = tenants[0]["slug"]
        
        selected_tenant = None
        if selected_tenant_slug:
            try:
                selected_tenant = tenant_manager.get_by_slug(selected_tenant_slug)
            except Exception as e:
                logger.warning(f"Could not get tenant with slug '{selected_tenant_slug}': {str(e)}")
                
        # Get media files for the selected tenant
        media_files = []
        if selected_tenant and hasattr(selected_tenant, 'id'):
            try:
                # Use the media service to list media files
                media_list = media_service.list_media(
                    tenant_id=str(selected_tenant.id),
                    file_type=file_type,
                    is_ai_generated=is_ai_generated,
                    search_term=search
                )
                # Handle both dict and list return types
                if isinstance(media_list, dict):
                    media_files = media_list.get("media", [])
                else:
                    media_files = media_list
            except Exception as e:
                logger.error(f"Error fetching media files: {str(e)}")
                if status_message is None:
                    status_message = f"Error fetching media files: {str(e)}"
                    status_type = "danger"
        
        # Get cart item count if available
        cart_item_count = 0
        session = request.session
        if 'cart_id' in session:
            try:
                cart_id = session['cart_id']
                cart = cart_manager.get(cart_id)
                cart_item_count = sum(item.quantity for item in cart.items)
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Error in admin_media: {str(e)}")
        if status_message is None:
            status_message = f"Error: {str(e)}"
            status_type = "danger"
        tenants = []
        selected_tenant = None
        media_files = []
        cart_item_count = 0
    
    # Prepare context data
    context = {
        "request": request,
        "active_page": "media",
        "tenants": tenants,
        "selected_tenant": selected_tenant_slug if selected_tenant_slug else "",
        "media_files": media_files,
        "cart_item_count": cart_item_count,
        "status_message": status_message,
        "status_type": status_type,
        "has_openai_key": bool(os.environ.get("OPENAI_API_KEY")),
        "file_type_filter": file_type,
        "is_ai_generated_filter": is_ai_generated,
        "search_query": search,
        "filters": {
            "file_type": file_type,
            "is_ai_generated": is_ai_generated,
            "search": search
        },
        "pagination": {
            "page": 1,
            "limit": 10,
            "total": len(media_files),
            "pages": max(1, (len(media_files) + 9) // 10)  # Calculate total pages (ceiling division)
        }
    }
    
    return templates.TemplateResponse("admin/media.html", context)

@app.post("/admin/media/upload", response_class=RedirectResponse)
async def admin_upload_media(
    request: Request,
    file: UploadFile = File(...),
    tenant_id: str = Form(...),
    alt_text: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """Upload a media file."""
    try:
        # Use the media service to handle the upload
        result = media_service.upload_file(file, tenant_id, alt_text, description)
        if result and result.get("id"):
            return RedirectResponse(
                url=f"/admin/media?tenant={tenant_id}&status_message=File+uploaded+successfully&status_type=success", 
                status_code=303
            )
        else:
            error_message = "Upload failed. Please try again."
            return RedirectResponse(
                url=f"/admin/media?tenant={tenant_id}&status_message={error_message}&status_type=danger", 
                status_code=303
            )
    except Exception as e:
        logger.error(f"Error uploading media: {str(e)}")
        error_message = f"Error uploading media: {str(e)}"
        return RedirectResponse(
            url=f"/admin/media?tenant={tenant_id}&status_message={error_message}&status_type=danger", 
            status_code=303
        )

@app.post("/admin/media/generate", response_class=RedirectResponse)
async def admin_generate_image(
    request: Request,
    prompt: str = Form(...),
    tenant_id: str = Form(...),
    size: str = Form("1024x1024"),
    quality: str = Form("standard"),
    alt_text: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """Generate an image using DALL-E."""
    try:
        # Use the media service to generate the image
        result = media_service.generate_image_with_dalle(
            prompt=prompt, 
            tenant_id=tenant_id, 
            size=size,
            quality=quality,
            alt_text=alt_text or prompt,
            description=description
        )
        if result and hasattr(result, 'id'):
            return RedirectResponse(
                url=f"/admin/media?tenant={tenant_id}&status_message=Image+generated+successfully&status_type=success", 
                status_code=303
            )
        else:
            error_message = "Image generation failed. Please try again."
            return RedirectResponse(
                url=f"/admin/media?tenant={tenant_id}&status_message={error_message}&status_type=danger", 
                status_code=303
            )
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        error_message = f"Error generating image: {str(e)}"
        return RedirectResponse(
            url=f"/admin/media?tenant={tenant_id}&status_message={error_message}&status_type=danger", 
            status_code=303
        )

@app.delete("/admin/media/{media_id}", response_class=RedirectResponse)
async def admin_delete_media(
    request: Request,
    media_id: str,
    tenant_id: str = Form(...)
):
    """Delete a media file."""
    try:
        # Use the media service to delete the media
        result = media_service.delete_media(media_id)
        if result:
            return RedirectResponse(
                url=f"/admin/media?tenant={tenant_id}&status_message=Media+deleted+successfully&status_type=success", 
                status_code=303
            )
        else:
            error_message = "Deletion failed. Please try again."
            return RedirectResponse(
                url=f"/admin/media?tenant={tenant_id}&status_message={error_message}&status_type=danger", 
                status_code=303
            )
    except Exception as e:
        logger.error(f"Error deleting media: {str(e)}")
        error_message = f"Error deleting media: {str(e)}"
        return RedirectResponse(
            url=f"/admin/media?tenant={tenant_id}&status_message={error_message}&status_type=danger", 
            status_code=303
        )

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
# Plugin configuration routes
@app.get("/admin/plugins/configure/{plugin_id}", response_class=HTMLResponse)
async def admin_plugin_config(
    request: Request,
    plugin_id: str,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Plugin configuration page."""
    # Initialize plugin details
    plugin_name = ""
    plugin_description = ""
    plugin_version = ""
    plugin_type = ""
    plugin_icon = "bi-puzzle"
    plugin_active = False
    plugin_author = "PyCommerce"
    plugin_docs_url = None
    config_fields = []
    help_content = None
    
    # Get the selected tenant from the query parameters
    selected_tenant = request.query_params.get('tenant')
    tenant_id = None
    
    # If a tenant is selected, get its ID
    if selected_tenant:
        from pycommerce.models.tenant import TenantManager
        tenant_manager = TenantManager()
        tenant_obj = tenant_manager.get_by_slug(selected_tenant)
        if tenant_obj:
            tenant_id = str(tenant_obj.id)
    
    # Initialize the plugin config manager
    from pycommerce.models.plugin_config import PluginConfigManager
    config_manager = PluginConfigManager()
    
    # Get plugin configuration from the database
    try:
        stored_config = config_manager.get_config(plugin_id, tenant_id)
        is_enabled = config_manager.is_enabled(plugin_id, tenant_id)
    except Exception as e:
        logger.error(f"Error loading plugin configuration: {str(e)}")
        stored_config = {}
        is_enabled = True

    # Configure different plugins
    if plugin_id == "stripe":
        plugin_name = "Stripe Payments"
        plugin_description = "Process credit card payments with Stripe"
        plugin_version = "1.0.0"
        plugin_type = "Payment"
        plugin_icon = "bi-credit-card"
        plugin_active = is_enabled
        plugin_docs_url = "https://stripe.com/docs/api"
        
        # Set default values from stored config
        stripe_api_key = stored_config.get("stripe_api_key", STRIPE_API_KEY or "")
        stripe_webhook_secret = stored_config.get("stripe_webhook_secret", STRIPE_WEBHOOK_SECRET or "")
        
        # Define configuration fields
        config_fields = [
            {
                "id": "stripe_api_key",
                "label": "Stripe API Key",
                "type": "password",
                "value": stripe_api_key,
                "required": True,
                "placeholder": "sk_test_...",
                "help_text": "Your Stripe secret API key. Starts with 'sk_test_' for test mode or 'sk_live_' for live mode."
            },
            {
                "id": "stripe_webhook_secret",
                "label": "Webhook Secret",
                "type": "password",
                "value": stripe_webhook_secret,
                "required": False,
                "placeholder": "whsec_...",
                "help_text": "Your Stripe webhook signing secret. Required for handling payment webhooks securely."
            },
            {
                "id": "stripe_enabled",
                "label": "Enable Stripe Payments",
                "type": "checkbox",
                "value": is_enabled,
                "required": False,
                "checkbox_label": "Enable Stripe payment processing",
                "help_text": "When enabled, Stripe will be available as a payment option for customers."
            }
        ]
        
        # Help content for Stripe
        help_content = """
        <p>Configure your Stripe payments integration here. You'll need to get your API keys from the Stripe Dashboard.</p>
        
        <h6>How to get your Stripe API keys:</h6>
        <ol>
            <li>Log in to your <a href="https://dashboard.stripe.com" target="_blank">Stripe Dashboard</a></li>
            <li>Go to Developers > API keys</li>
            <li>Copy the Secret key (starts with sk_test_ for test mode)</li>
            <li>Paste it into the API Key field here</li>
        </ol>
        
        <div class="alert alert-warning">
            <i class="bi bi-shield-exclamation"></i> <strong>Important:</strong> Never share your Stripe secret key publicly or commit it to your code repository.
        </div>
        """
    
    elif plugin_id == "paypal":
        plugin_name = "PayPal Payments"
        plugin_description = "Accept payments via PayPal"
        plugin_version = "1.0.0"
        plugin_type = "Payment"
        plugin_icon = "bi-paypal"
        plugin_active = is_enabled
        plugin_docs_url = "https://developer.paypal.com/docs/api/overview/"
        
        # Set default values from stored config
        paypal_client_id = stored_config.get("paypal_client_id", PAYPAL_CLIENT_ID or "")
        paypal_client_secret = stored_config.get("paypal_client_secret", PAYPAL_CLIENT_SECRET or "")
        paypal_sandbox = stored_config.get("paypal_sandbox", PAYPAL_SANDBOX)
        
        # Define configuration fields
        config_fields = [
            {
                "id": "paypal_client_id",
                "label": "PayPal Client ID",
                "type": "text",
                "value": paypal_client_id,
                "required": True,
                "placeholder": "Your PayPal client ID",
                "help_text": "Your PayPal client ID from the PayPal Developer Dashboard."
            },
            {
                "id": "paypal_client_secret",
                "label": "PayPal Client Secret",
                "type": "password",
                "value": paypal_client_secret,
                "required": True,
                "placeholder": "Your PayPal client secret",
                "help_text": "Your PayPal client secret from the PayPal Developer Dashboard."
            },
            {
                "id": "paypal_sandbox",
                "label": "Use Sandbox Mode",
                "type": "checkbox",
                "value": paypal_sandbox,
                "required": False,
                "checkbox_label": "Use PayPal sandbox for testing",
                "help_text": "When enabled, payments will be processed in PayPal's sandbox environment."
            },
            {
                "id": "paypal_enabled",
                "label": "Enable PayPal Payments",
                "type": "checkbox",
                "value": is_enabled,
                "required": False,
                "checkbox_label": "Enable PayPal payment processing",
                "help_text": "When enabled, PayPal will be available as a payment option for customers."
            }
        ]
        
        # Help content for PayPal
        help_content = """
        <p>Configure your PayPal payments integration here. You'll need to get your API credentials from the PayPal Developer Dashboard.</p>
        
        <h6>How to get your PayPal credentials:</h6>
        <ol>
            <li>Log in to the <a href="https://developer.paypal.com/developer/applications/" target="_blank">PayPal Developer Dashboard</a></li>
            <li>Create a new app or select an existing one</li>
            <li>Copy the Client ID and Secret</li>
            <li>Paste them into the fields here</li>
        </ol>
        
        <div class="alert alert-info">
            <i class="bi bi-info-circle"></i> <strong>Testing:</strong> Use Sandbox mode to test payments without processing real money.
        </div>
        """
    
    elif plugin_id == "standard-shipping":
        plugin_name = "Standard Shipping"
        plugin_description = "Basic shipping rate calculations"
        plugin_version = "1.0.0"
        plugin_type = "Shipping"
        plugin_icon = "bi-truck"
        plugin_active = is_enabled
        
        # Set default values from stored config
        flat_rate_domestic = stored_config.get("flat_rate_domestic", 5.99)
        flat_rate_international = stored_config.get("flat_rate_international", 19.99)
        free_shipping_threshold = stored_config.get("free_shipping_threshold", 50.00)
        
        # Help content for Standard Shipping
        help_content = """
        <p>Configure your shipping rates and options here. These settings will apply to all orders in the selected store.</p>
        
        <h6>Shipping Configuration Tips:</h6>
        <ul>
            <li>Set domestic rates for orders shipping within your primary country</li>
            <li>Set international rates for all cross-border shipments</li>
            <li>Configure free shipping thresholds to encourage larger orders</li>
        </ul>
        
        <div class="alert alert-info">
            <i class="bi bi-info-circle"></i> <strong>Tip:</strong> Consider offering free shipping on orders above a certain value to increase average order size.
        </div>
        """
        
        # Define configuration fields
        config_fields = [
            {
                "id": "flat_rate_domestic",
                "label": "Domestic Flat Rate",
                "type": "number",
                "value": flat_rate_domestic,
                "required": True,
                "help_text": "Flat shipping rate for domestic orders."
            },
            {
                "id": "flat_rate_international",
                "label": "International Flat Rate",
                "type": "number",
                "value": flat_rate_international,
                "required": True,
                "help_text": "Flat shipping rate for international orders."
            },
            {
                "id": "free_shipping_threshold",
                "label": "Free Shipping Threshold",
                "type": "number",
                "value": free_shipping_threshold,
                "required": False,
                "help_text": "Orders over this amount qualify for free shipping. Leave blank to disable free shipping."
            }
        ]
    
    else:
        # Unknown plugin
        return RedirectResponse(
            url="/admin/plugins?status_message=Plugin+not+found&status_type=danger",
            status_code=303
        )
    
    # Get all tenants for the store selector
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
    
    # Get selected tenant from query param or session
    selected_tenant = request.query_params.get('tenant')
    if not selected_tenant and tenants:
        selected_tenant = tenants[0]["slug"]
        
    return templates.TemplateResponse(
        "admin/plugin_config.html",
        {
            "request": request,
            "active_page": "plugins",
            "tenants": tenants,
            "selected_tenant": selected_tenant,
            "plugin_id": plugin_id,
            "plugin_name": plugin_name,
            "plugin_description": plugin_description,
            "plugin_version": plugin_version,
            "plugin_type": plugin_type,
            "plugin_icon": plugin_icon,
            "plugin_active": plugin_active,
            "plugin_author": plugin_author,
            "plugin_docs_url": plugin_docs_url,
            "config_fields": config_fields,
            "help_content": help_content,
            "status_message": status_message,
            "status_type": status_type
        }
    )

@app.post("/admin/plugins/save-config/{plugin_id}", response_class=RedirectResponse)
async def admin_plugin_save_config(
    request: Request,
    plugin_id: str
):
    """Save plugin configuration."""
    try:
        form_data = await request.form()
        
        # Get the selected tenant from the form
        selected_tenant = form_data.get('tenant')
        tenant_id = None
        
        # If a tenant is selected, get its ID
        if selected_tenant:
            from pycommerce.models.tenant import TenantManager
            tenant_manager = TenantManager()
            tenant_obj = tenant_manager.get_by_slug(selected_tenant)
            if tenant_obj:
                tenant_id = str(tenant_obj.id)
        
        # Initialize the plugin config manager
        from pycommerce.models.plugin_config import PluginConfigManager
        config_manager = PluginConfigManager()
        
        # Get the plugin-specific configuration
        if plugin_id == "stripe":
            stripe_api_key = form_data.get("stripe_api_key", "")
            stripe_webhook_secret = form_data.get("stripe_webhook_secret", "")
            stripe_enabled = form_data.get("stripe_enabled") == "on"
            
            # Create configuration dictionary
            config_data = {
                "stripe_api_key": stripe_api_key,
                "stripe_webhook_secret": stripe_webhook_secret
            }
            
            # Log (don't log actual keys in production)
            logger.info(f"Updating Stripe configuration: API Key: {'*' * 10 if stripe_api_key else 'Not provided'}")
            logger.info(f"Updating Stripe configuration: Webhook Secret: {'*' * 10 if stripe_webhook_secret else 'Not provided'}")
            logger.info(f"Updating Stripe configuration: Enabled: {stripe_enabled}")
            
            # Save configuration to database
            config_manager.save_config(plugin_id, config_data, tenant_id)
            
            # Set enabled/disabled status
            config_manager.set_enabled(plugin_id, stripe_enabled, tenant_id)
            
            return RedirectResponse(
                url=f"/admin/plugins/configure/stripe?tenant={selected_tenant}&status_message=Stripe+configuration+saved+successfully&status_type=success",
                status_code=303
            )
        
        elif plugin_id == "paypal":
            paypal_client_id = form_data.get("paypal_client_id", "")
            paypal_client_secret = form_data.get("paypal_client_secret", "")
            paypal_sandbox = form_data.get("paypal_sandbox") == "on"
            paypal_enabled = form_data.get("paypal_enabled") == "on"
            
            # Create configuration dictionary
            config_data = {
                "paypal_client_id": paypal_client_id,
                "paypal_client_secret": paypal_client_secret,
                "paypal_sandbox": paypal_sandbox
            }
            
            # Log (don't log actual keys in production)
            logger.info(f"Updating PayPal configuration: Client ID: {'*' * 10 if paypal_client_id else 'Not provided'}")
            logger.info(f"Updating PayPal configuration: Client Secret: {'*' * 10 if paypal_client_secret else 'Not provided'}")
            logger.info(f"Updating PayPal configuration: Sandbox: {paypal_sandbox}")
            logger.info(f"Updating PayPal configuration: Enabled: {paypal_enabled}")
            
            # Save configuration to database
            config_manager.save_config(plugin_id, config_data, tenant_id)
            
            # Set enabled/disabled status
            config_manager.set_enabled(plugin_id, paypal_enabled, tenant_id)
            
            return RedirectResponse(
                url=f"/admin/plugins/configure/paypal?tenant={selected_tenant}&status_message=PayPal+configuration+saved+successfully&status_type=success",
                status_code=303
            )
        
        elif plugin_id == "standard-shipping":
            flat_rate_domestic = float(form_data.get("flat_rate_domestic", 5.99))
            flat_rate_international = float(form_data.get("flat_rate_international", 19.99))
            free_shipping_threshold_str = form_data.get("free_shipping_threshold", "")
            
            free_shipping_threshold = float(free_shipping_threshold_str) if free_shipping_threshold_str else None
            
            # Create configuration dictionary
            config_data = {
                "flat_rate_domestic": flat_rate_domestic,
                "flat_rate_international": flat_rate_international,
                "free_shipping_threshold": free_shipping_threshold
            }
            
            logger.info(f"Updating Standard Shipping configuration: Domestic Rate: {flat_rate_domestic}")
            logger.info(f"Updating Standard Shipping configuration: International Rate: {flat_rate_international}")
            logger.info(f"Updating Standard Shipping configuration: Free Threshold: {free_shipping_threshold}")
            
            # Save configuration to database
            config_manager.save_config(plugin_id, config_data, tenant_id)
            
            # Always enabled for shipping
            config_manager.set_enabled(plugin_id, True, tenant_id)
            
            return RedirectResponse(
                url=f"/admin/plugins/configure/standard-shipping?tenant={selected_tenant}&status_message=Shipping+configuration+saved+successfully&status_type=success",
                status_code=303
            )
        
        else:
            # Unknown plugin
            return RedirectResponse(
                url="/admin/plugins?status_message=Plugin+not+found&status_type=danger",
                status_code=303
            )
    
    except Exception as e:
        logger.error(f"Error saving plugin configuration: {str(e)}")
        
        # Redirect with error message
        error_message = f"Error saving configuration: {str(e)}"
        return RedirectResponse(
            url=f"/admin/plugins/configure/{plugin_id}?status_message={error_message}&status_type=danger",
            status_code=303
        )

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "message": "PyCommerce Platform is running with FastAPI and uvicorn."
    }

if __name__ == "__main__":
    uvicorn.run("web_server:app", host="0.0.0.0", port=5000, reload=True)
