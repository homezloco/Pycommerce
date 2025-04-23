"""
Test products page for the PyCommerce admin panel.

This module creates a test route for the products page that uses the original styling.
"""
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Request, Query, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from pycommerce.models.tenant import TenantManager
from pycommerce.models.product import ProductManager
# These might not exist, so we'll handle them differently
try:
    from pycommerce.models.category import CategoryManager
except ImportError:
    CategoryManager = None

try:
    from pycommerce.services.media_service import MediaService
except ImportError:
    try:
        from pycommerce.services.media import MediaService
    except ImportError:
        MediaService = None

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin/products", tags=["admin"])

# Global variables initialized in setup_routes
templates = None

# Initialize managers with error handling
try:
    tenant_manager = TenantManager()
except Exception as e:
    logger.error(f"Error initializing TenantManager: {e}")
    tenant_manager = None

try:
    product_manager = ProductManager()
except Exception as e:
    logger.error(f"Error initializing ProductManager: {e}")
    product_manager = None

# Handle CategoryManager
category_manager = None
if CategoryManager:
    try:
        category_manager = CategoryManager()
    except Exception as e:
        logger.error(f"Error initializing CategoryManager: {e}")

# Handle MediaService
media_service = None
if MediaService:
    try:
        media_service = MediaService()
    except Exception as e:
        logger.error(f"Error initializing MediaService: {e}")


@router.post("/update/{product_id}", response_class=RedirectResponse)
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

@router.get("/{product_id}", response_class=HTMLResponse)
async def admin_product_edit(
    request: Request,
    product_id: str,
    tenant: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Edit product page for admin panel."""
    try:
        # Get product directly
        product_obj = product_manager.get(product_id)
        
        if not product_obj:
            logger.error(f"Product with ID {product_id} not found")
            return RedirectResponse(
                url=f"/admin/products?status_message=Product+not+found&status_type=danger", 
                status_code=303
            )
        
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
        
        return templates.TemplateResponse(
            "admin/product_edit.html", 
            {
                "request": request, 
                "active_page": "products",
                "product": product,
                "tenants": tenants,
                "cart_item_count": request.session.get("cart_item_count", 0),
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

@router.get("", response_class=HTMLResponse)
async def admin_products(
    request: Request,
    tenant: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin products page using original template."""
    from routes.admin.tenant_utils import (
        get_selected_tenant, redirect_to_tenant_selection, 
        create_virtual_all_tenant, get_all_tenants, get_tenant_object
    )
    
    # Get selected tenant using the unified utility
    selected_tenant_slug, selected_tenant = get_selected_tenant(
        request=request,
        tenant_param=tenant,
        allow_all=True  # Products page allows "all" tenant selection
    )
    
    # If no tenant is selected, redirect to dashboard with message
    if not selected_tenant_slug:
        return redirect_to_tenant_selection()
    
    # Handle "all" tenant slug case
    if selected_tenant_slug.lower() == "all":
        logger.info("Using 'All Stores' selection in products page")
        tenant_obj = type('AllStoresTenant', (), create_virtual_all_tenant())
    else:
        # Get tenant object
        tenant_obj = get_tenant_object(selected_tenant_slug)
        if not tenant_obj:
            logger.error(f"Tenant with slug {selected_tenant_slug} not found")
            return redirect_to_tenant_selection(
                message="Store not found", 
                message_type="error"
            )
    
    # Build filters
    filters = {}
    if category:
        filters["category"] = category
    if min_price is not None:
        filters["min_price"] = min_price
    if max_price is not None:
        filters["max_price"] = max_price
    if in_stock is not None:
        filters["in_stock"] = in_stock
    
    # Fetch products
    if selected_tenant_slug.lower() == "all":
        # Fetch all products when "All Stores" is selected
        logger.info("Fetching products for all stores")
        from routes.admin.tenant_utils import get_products_for_all_tenants
        products = get_products_for_all_tenants(tenant_manager, product_manager, logger, filters)
    else:
        # Fetch products for specific tenant
        logger.info(f"Fetching products for tenant: {tenant_obj.name} (ID: {tenant_obj.id})")
        products = product_manager.get_by_tenant(
            tenant_id=str(tenant_obj.id),
            **filters
        )
        logger.info(f"Found {len(products)} products for tenant {tenant_obj.name}")
    
    # Format products for template
    products_list = []
    for idx, product in enumerate(products):
        product_id = str(product.id) if hasattr(product, "id") else f"product_{idx}"
        logger.info(f"Product {idx+1}: ID={product_id}, Name={product.name}, Price={product.price}")
        
        # Get product details
        name = product.name
        description = product.description if hasattr(product, "description") else ""
        price = product.price
        stock = product.stock if hasattr(product, "stock") else 0
        sku = product.sku if hasattr(product, "sku") else ""
        tenant_name = tenant_obj.name
        categories = product.categories if hasattr(product, "categories") else []
        
        # Store in list for template
        product_dict = {
            "id": product_id,
            "name": name,
            "description": description,
            "price": price,
            "stock": stock,
            "sku": sku,
            "categories": categories,
            "image_url": product.image_url if hasattr(product, "image_url") else None,
            "tenant_name": tenant_name
        }
        products_list.append(product_dict)
        logger.info(f"Added product to template: {product_dict['name']} with tenant_name={product_dict['tenant_name']}")
    
    logger.info(f"Total products for template: {len(products_list)}")
    
    # Get categories for filter
    categories = []
    if category_manager:
        try:
            categories = category_manager.get_by_tenant(str(tenant_obj.id))
        except Exception as e:
            logger.warning(f"Error getting categories: {str(e)}")
    
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
    
    return templates.TemplateResponse(
        "admin/products.html",
        {
            "request": request,
            "active_page": "products",
            "tenant": tenant_obj,
            "tenant_id": str(tenant_obj.id),
            "products": products_list,
            "categories": categories,
            "tenants": tenants,
            "selected_tenant_slug": selected_tenant_slug,
            "selected_tenant": selected_tenant_slug,  # Add this to ensure the dropdown shows correctly
            "category": category,
            "min_price": min_price,
            "max_price": max_price,
            "in_stock": in_stock,
            "cart_item_count": request.session.get("cart_item_count", 0),
            "status_message": status_message,
            "status_type": status_type
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