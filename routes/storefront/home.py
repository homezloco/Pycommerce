"""
Home routes for the PyCommerce storefront.

This module defines the routes for the home page and other general pages.
"""
import logging
from typing import Optional, Dict, List, Any
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from pycommerce.models.tenant import TenantManager
from pycommerce.models.product import ProductManager
from pycommerce.models.cart import CartManager

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["home"])

# Global variables initialized in setup_routes
templates = None
tenant_manager = TenantManager()
product_manager = ProductManager()
cart_manager = CartManager()

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Home page for PyCommerce."""
    # Get cart data for navigation
    cart_id = request.session.get("cart_id")
    cart_item_count = 0
    
    if cart_id:
        try:
            cart = cart_manager.get(cart_id)
            cart_item_count = sum(item.quantity for item in cart.items)
        except Exception:
            pass
            
    # Default shipping config
    shipping_config = {
        "store_country": "US",
        "store_postal_code": "",
        "free_shipping_threshold": 100,
        "dimensional_weight_factor": 5000,
        "express_multiplier": 1.75,
        "flat_rate_domestic": 5.99,
        "flat_rate_international": 19.99,
        "weight_rates": {
            "domestic": {"base_rate": 5.99, "per_kg": 1.5, "min_weight_kg": 0.1},
            "continental": {"base_rate": 12.99, "per_kg": 3.5, "min_weight_kg": 0.1},
            "international_close": {"base_rate": 18.99, "per_kg": 5.0, "min_weight_kg": 0.1},
            "international_far": {"base_rate": 29.99, "per_kg": 8.0, "min_weight_kg": 0.1}
        }
    }
    
    # Get current tenant from request or default to None
    selected_tenant = None
    try:
        # Try to get tenant from domain or query parameter
        tenant_slug = request.query_params.get('tenant')
        if tenant_slug:
            tenant = tenant_manager.get_by_slug(tenant_slug)
            if tenant:
                selected_tenant = {
                    "id": str(tenant.id),
                    "name": tenant.name,
                    "slug": tenant.slug
                }
    except Exception as e:
        logger.error(f"Error determining current tenant: {e}")
    
    # Get shipping config if tenant is selected
    if selected_tenant:
        try:
            from pycommerce.plugins import get_plugin_registry
            plugin_registry = get_plugin_registry()
            shipping_plugin = plugin_registry.get_shipping_plugin('standard')
            
            if shipping_plugin:
                tenant_shipping_config = shipping_plugin.get_shipping_config(str(selected_tenant["id"]))
                if tenant_shipping_config:
                    shipping_config.update(tenant_shipping_config)
        except Exception as e:
            logger.error(f"Error loading shipping configuration: {e}")

    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "cart_item_count": cart_item_count
        }
    )

@router.get("/api/generate-sample-data")
async def generate_sample_data():
    """Generate sample data for testing."""
    try:
        created_tenants = []
        
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
                created_tenants.append({"name": tenant1.name, "slug": tenant1.slug})
            except Exception as e:
                logger.error(f"Error creating tenant demo1: {str(e)}")
                
        if 'demo2' not in existing_slugs:
            try:
                tenant2 = tenant_manager.create(
                    name="Demo Store 2",
                    slug="demo2",
                    domain="demo2.pycommerce.example"
                )
                created_tenants.append({"name": tenant2.name, "slug": tenant2.slug})
            except Exception as e:
                logger.error(f"Error creating tenant demo2: {str(e)}")
                
        # Create products for tenant1
        if tenant1:
            products_tenant1 = [
                {
                    "sku": "T1-PROD-001",
                    "name": "Demo Product 1",
                    "description": "This is a demo product for tenant 1",
                    "price": 19.99,
                    "stock": 100,
                    "categories": ["demo", "electronics"],
                    "metadata": {"tenant_id": str(tenant1.id)}
                },
                {
                    "sku": "T1-PROD-002",
                    "name": "Demo Product 2",
                    "description": "Another demo product for tenant 1",
                    "price": 29.99,
                    "stock": 50,
                    "categories": ["demo", "clothing"],
                    "metadata": {"tenant_id": str(tenant1.id)}
                }
            ]
            
            for product_data in products_tenant1:
                try:
                    product_manager.create(product_data)
                except Exception as e:
                    logger.error(f"Error creating product {product_data['name']}: {str(e)}")
        
        # Create products for tenant2
        if tenant2:
            products_tenant2 = [
                {
                    "sku": "T2-PROD-001",
                    "name": "Tenant 2 Product 1",
                    "description": "This is a demo product for tenant 2",
                    "price": 39.99,
                    "stock": 75,
                    "categories": ["demo", "food"],
                    "metadata": {"tenant_id": str(tenant2.id)}
                },
                {
                    "sku": "T2-PROD-002",
                    "name": "Tenant 2 Product 2",
                    "description": "Another demo product for tenant 2",
                    "price": 49.99,
                    "stock": 25,
                    "categories": ["demo", "household"],
                    "metadata": {"tenant_id": str(tenant2.id)}
                }
            ]
            
            for product_data in products_tenant2:
                try:
                    product_manager.create(product_data)
                except Exception as e:
                    logger.error(f"Error creating product {product_data['name']}: {str(e)}")
        
        # Redirect to the stores page
        return RedirectResponse(url="/stores", status_code=303)
        
    except Exception as e:
        logger.error(f"Error generating sample data: {str(e)}")
        return {"success": False, "message": f"Error generating sample data: {str(e)}"}

# Fallback for admin routes
@router.get("/admin")
@router.get("/admin/")
async def admin_redirect():
    """Redirect /admin to /admin/dashboard."""
    return RedirectResponse(url="/admin/dashboard")

def setup_routes(app_templates):
    """
    Set up routes with the given templates.
    
    Args:
        app_templates: Jinja2Templates instance from the main app
    """
    global templates
    templates = app_templates
    return router