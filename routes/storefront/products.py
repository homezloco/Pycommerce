"""
Product routes for the PyCommerce storefront.

This module defines the routes for product listings and product detail pages.
"""
import logging
from typing import Optional, Dict, List, Any
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from pycommerce.models.tenant import TenantManager
from pycommerce.models.product import ProductManager
from pycommerce.models.cart import CartManager
from pycommerce.services.recommendation import RecommendationService

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/products", tags=["products"])

# Global variables initialized in setup_routes
templates = None
tenant_manager = TenantManager()
product_manager = ProductManager()
cart_manager = CartManager()

@router.get("", response_class=HTMLResponse)
async def products(
    request: Request,
    tenant: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None
):
    """Products listing page with optional filtering."""
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

@router.get("/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, product_id: str):
    """Product detail page."""
    product_data = None
    tenant_id = None
    
    try:
        product = product_manager.get(product_id)
        if product:
            # If the product has a tenant, store the tenant ID for recommendations
            if hasattr(product, 'metadata') and 'tenant_id' in product.metadata:
                tenant_id = product.metadata.get('tenant_id')
                
            product_data = {
                "id": str(product.id),
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "sku": product.sku,
                "stock": product.stock,
                "categories": product.categories,
                "images": product.images if hasattr(product, 'images') else []
            }
    except Exception as e:
        logger.error(f"Error fetching product details: {str(e)}")
        # Redirect to products if product not found
        return RedirectResponse(url="/products")
    
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
        "product_detail.html", 
        {
            "request": request, 
            "product": product_data,
            "cart_item_count": cart_item_count,
            "tenant_id": tenant_id
        }
    )

def setup_routes(app_templates):
    """
    Set up routes with the given templates.
    
    Args:
        app_templates: Jinja2Templates instance from the main app
    """
    global templates
    templates = app_templates
    return router