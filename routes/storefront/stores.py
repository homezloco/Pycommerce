"""
Store routes for the PyCommerce storefront.

This module defines the routes for store listings and store detail pages.
"""
import logging
from typing import Optional, Dict, List, Any
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# Import the pycommerce SDK managers for now, we'll get the real ones at runtime
from pycommerce.models.tenant import TenantManager
from pycommerce.models.product import ProductManager 
from pycommerce.models.cart import CartManager

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["store"])

# Global variables initialized in setup_routes
templates = None
tenant_manager = TenantManager()
product_manager = ProductManager()
cart_manager = CartManager()

@router.get("/stores", response_class=HTMLResponse)
async def stores(request: Request):
    """List all stores page."""
    tenants = []
    try:
        # Handle both SDK and Flask managers
        if hasattr(tenant_manager, 'get_all_tenants'):
            tenants_list = tenant_manager.get_all_tenants() or []
        else:
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
            # Handle both SDK and Flask managers
            if hasattr(cart_manager, 'get_cart_by_id'):
                cart = cart_manager.get_cart_by_id(cart_id)
            else:
                cart = cart_manager.get(cart_id)
            
            if cart and hasattr(cart, 'items'):
                cart_item_count = sum(item.quantity for item in cart.items)
        except Exception as e:
            logger.warning(f"Error getting cart: {str(e)}")
    
    return templates.TemplateResponse(
        "stores.html", 
        {
            "request": request, 
            "tenants": tenants,
            "cart_item_count": cart_item_count
        }
    )

@router.get("/store/{slug}", response_class=HTMLResponse)
async def store(
    request: Request,
    slug: str,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None
):
    """Store detail page showing products for a specific store."""
    tenant_obj = None
    try:
        # Handle both SDK and Flask managers
        if hasattr(tenant_manager, 'get_tenant_by_slug'):
            tenant_obj = tenant_manager.get_tenant_by_slug(slug)
        else:
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
        # Build filters
        filters_dict = {}
        if category:
            filters_dict["category"] = category
        if min_price is not None:
            filters_dict["min_price"] = min_price
        if max_price is not None:
            filters_dict["max_price"] = max_price
        if in_stock is not None:
            filters_dict["in_stock"] = in_stock
        
        # Get products using the appropriate manager method
        if hasattr(product_manager, 'get_products_by_tenant'):
            # Use SQLAlchemy manager's method
            tenant_products = product_manager.get_products_by_tenant(
                tenant_id=tenant_obj.id,
                filters=filters_dict
            )
        else:
            # Use SDK manager's method
            logger.info(f"Using SDK ProductManager to filter products for tenant: {tenant_obj.id}")
            
            # First try to access the products directly from the database
            try:
                # Import Product model directly to query the database
                from models import Product
                from app import app
                
                logger.info(f"Querying database directly for products of tenant: {tenant_obj.id}")
                
                # Build the query
                with app.app_context():
                    query = Product.query.filter_by(tenant_id=str(tenant_obj.id))
                    
                    # Apply filters
                    if filters_dict.get("category"):
                        category = filters_dict["category"]
                        query = query.filter(Product.categories.contains(f'["{category}"]'))
                    
                    if filters_dict.get("min_price") is not None:
                        query = query.filter(Product.price >= filters_dict["min_price"])
                    
                    if filters_dict.get("max_price") is not None:
                        query = query.filter(Product.price <= filters_dict["max_price"])
                    
                    if filters_dict.get("in_stock") is not None and filters_dict["in_stock"]:
                        query = query.filter(Product.stock > 0)
                    
                    # Execute the query
                    tenant_products = query.all()
                    logger.info(f"Found {len(tenant_products)} products in database")
            
            except Exception as e:
                logger.error(f"Error querying database directly: {str(e)}")
                
                # Fallback to SDK managers
                if hasattr(product_manager, 'get_by_tenant'):
                    logger.info(f"Falling back to get_by_tenant method for tenant: {tenant_obj.id}")
                    tenant_products = product_manager.get_by_tenant(str(tenant_obj.id))
                    
                    # Apply filters after getting tenant products
                    if filters_dict.get("category"):
                        tenant_products = [p for p in tenant_products if filters_dict["category"] in p.categories]
                    if filters_dict.get("min_price") is not None:
                        tenant_products = [p for p in tenant_products if p.price >= filters_dict["min_price"]]
                    if filters_dict.get("max_price") is not None:
                        tenant_products = [p for p in tenant_products if p.price <= filters_dict["max_price"]]
                    if filters_dict.get("in_stock") is not None and filters_dict["in_stock"]:
                        tenant_products = [p for p in tenant_products if p.stock > 0]
                else:
                    # Last resort fallback
                    logger.info(f"Using list method and filtering for tenant: {tenant_obj.id}")
                    tenant_products = []
                    all_products = product_manager.list(
                        category=filters_dict.get("category"),
                        min_price=filters_dict.get("min_price"),
                        max_price=filters_dict.get("max_price"),
                        in_stock=filters_dict.get("in_stock")
                    )
                    
                    # Filter by tenant ID in metadata
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
            # Handle both SDK and Flask managers
            if hasattr(cart_manager, 'get_cart_by_id'):
                cart = cart_manager.get_cart_by_id(cart_id)
            else:
                cart = cart_manager.get(cart_id)
            
            if cart and hasattr(cart, 'items'):
                cart_item_count = sum(item.quantity for item in cart.items)
        except Exception as e:
            logger.warning(f"Error getting cart: {str(e)}")
    
    # Get theme settings from tenant if available
    theme_settings = {}
    if tenant_obj and hasattr(tenant_obj, 'settings') and tenant_obj.settings:
        theme_settings = tenant_obj.settings.get('theme', {})
        logger.info(f"Theme settings for tenant {tenant_obj.name}: {theme_settings}")
    else:
        logger.warning(f"No theme settings found for tenant {tenant_obj.name if tenant_obj else 'unknown'}")
        
    # Check if logo_url exists
    if 'logo_url' not in theme_settings or not theme_settings.get('logo_url'):
        # Refetch the tenant using our improved get_by_slug method that always gets fresh data
        logger.info(f"No logo found in theme settings, re-fetching tenant with slug: {slug}")
        
        # Handle both SDK and Flask managers
        if hasattr(tenant_manager, 'get_tenant_by_slug'):
            tenant_obj = tenant_manager.get_tenant_by_slug(slug)
        else:
            tenant_obj = tenant_manager.get_by_slug(slug)
            
        if tenant_obj and hasattr(tenant_obj, 'settings') and tenant_obj.settings:
            theme_settings = tenant_obj.settings.get('theme', {})
            logger.info(f"Re-fetched theme settings: {theme_settings}")
            
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

def setup_routes(app_templates):
    """
    Set up routes with the given templates.
    
    Args:
        app_templates: Jinja2Templates instance from the main app
    """
    global templates, tenant_manager, product_manager, cart_manager
    templates = app_templates
    
    # Now that we have the application context, we can import the managers
    # from the Flask app instead of using the SDK versions
    try:
        # Importing here to avoid circular import errors
        from managers import TenantManager as FlaskTenantManager
        from managers import ProductManager as FlaskProductManager
        from managers import CartManager as FlaskCartManager
        
        # Replace the SDK managers with the Flask app managers
        tenant_manager = FlaskTenantManager()
        product_manager = FlaskProductManager()
        cart_manager = FlaskCartManager()
        
        logger.info("Successfully loaded Flask app managers")
    except Exception as e:
        logger.error(f"Error loading Flask app managers: {e}")
        # We'll keep using the SDK managers as fallback
    
    return router