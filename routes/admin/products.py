"""
Admin routes for product management.

This module contains all the routes for managing products in the admin interface.
"""
import logging
from typing import Optional, List, Dict, Any
import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

# Template setup will be passed from main app
templates = None

# Initialize logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])

# Import models and managers for products
try:
    from pycommerce.models.tenant import TenantManager
    from pycommerce.models.product import ProductManager
    from pycommerce.services.media_service import MediaService
    
    # Initialize managers and services
    tenant_manager = TenantManager()
    product_manager = ProductManager()
    # CategoryManager may not exist, so we'll handle it gracefully
    category_manager = None
    media_service = MediaService()
except ImportError as e:
    logger.error(f"Error importing product modules: {str(e)}")
    tenant_manager = None
    product_manager = None
    category_manager = None
    media_service = None

@router.get("/products", response_class=HTMLResponse)
async def admin_products(
    request: Request,
    tenant: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[str] = None,
    max_price: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for managing products."""
    # Convert price strings to float if present and not empty
    min_price_float = None
    if min_price and min_price.strip():
        try:
            min_price_float = float(min_price)
        except ValueError:
            pass
            
    max_price_float = None
    if max_price and max_price.strip():
        try:
            max_price_float = float(max_price)
        except ValueError:
            pass
    # Get tenant from query parameters or session
    selected_tenant_slug = tenant or request.session.get("selected_tenant")
    
    # If no tenant is selected, redirect to dashboard with message
    if not selected_tenant_slug:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Please+select+a+store+first&status_type=warning", 
            status_code=303
        )
    
    # Store the selected tenant in session for future requests
    request.session["selected_tenant"] = selected_tenant_slug
    
    # Get tenant object
    tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
    if not tenant_obj:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Store+not+found&status_type=error", 
            status_code=303
        )
    
    # Get products for tenant
    logger.info(f"Fetching products for tenant: {tenant_obj.name} (ID: {tenant_obj.id})")
    products = product_manager.get_by_tenant(str(tenant_obj.id))
    logger.info(f"Found {len(products)} products for tenant {tenant_obj.name}")
    
    # Log product details for debugging
    for idx, p in enumerate(products):
        logger.info(f"Product {idx+1}: ID={p.id}, Name={p.name}, Price={p.price}")
    
    # Apply filters if specified
    if category:
        products = [p for p in products if hasattr(p, 'categories') and category in p.categories]
    if min_price_float is not None:
        products = [p for p in products if hasattr(p, 'price') and float(p.price) >= min_price_float]
    if max_price_float is not None:
        products = [p for p in products if hasattr(p, 'price') and float(p.price) <= max_price_float]
    
    # Format products for template
    products_list = []
    for product in products:
        product_dict = {
            "id": str(product.id),
            "name": product.name,
            "description": product.description if hasattr(product, "description") else "",
            "price": product.price,
            "stock": product.stock if hasattr(product, "stock") else 0,
            "sku": product.sku if hasattr(product, "sku") else "",
            "categories": product.categories if hasattr(product, "categories") else [],
            "image_url": product.image_url if hasattr(product, "image_url") else None,
            "tenant_name": tenant_obj.name
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
    
    # Debug the context being passed to the template
    context = {
        "request": request,
        "active_page": "products",
        "products": products_list,
        "tenant": tenant_obj,
        "selected_tenant": selected_tenant_slug,
        "tenants": tenants,
        "categories": categories,
        "filters": {
            "category": category,
            "min_price": min_price,
            "max_price": max_price
        },
        "status_message": status_message,
        "status_type": status_type,
        "cart_item_count": request.session.get("cart_item_count", 0)
    }
    
    # Add debugging for the products in the context
    logger.info(f"Context products type: {type(context['products'])}")
    logger.info(f"Context products length: {len(context['products'])}")
    if context['products']:
        logger.info(f"First product in context: {context['products'][0]}")
    
    return templates.TemplateResponse("admin/products.html", context)


@router.get("/products/add", response_class=HTMLResponse)
async def admin_add_product_form(
    request: Request,
    tenant: Optional[str] = None
):
    """Admin form for adding a new product."""
    # Get tenant from query parameters or session
    selected_tenant_slug = tenant or request.session.get("selected_tenant")
    
    # If no tenant is selected, redirect to dashboard with message
    if not selected_tenant_slug:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Please+select+a+store+first&status_type=warning", 
            status_code=303
        )
    
    # Store the selected tenant in session for future requests
    request.session["selected_tenant"] = selected_tenant_slug
    
    # Get tenant object
    tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
    if not tenant_obj:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Store+not+found&status_type=error", 
            status_code=303
        )
    
    # Get categories for tenant
    categories = []
    if category_manager:
        try:
            categories = category_manager.get_by_tenant(str(tenant_obj.id))
        except Exception as e:
            logger.warning(f"Error getting categories: {str(e)}")
    
    # Get media files for tenant
    media_files = []
    try:
        media_files = media_service.list_media(tenant_id=str(tenant_obj.id), file_type="image")
    except Exception as e:
        logger.warning(f"Error getting media files: {str(e)}")
    
    # Format media for template
    media_list = []
    for media in media_files:
        media_list.append({
            "id": str(media.id),
            "name": media.name if hasattr(media, "name") else (media.file_name if hasattr(media, "file_name") else ""),
            "url": media.file_url if hasattr(media, "file_url") else (media.url if hasattr(media, "url") else ""),
            "thumbnail_url": media.thumbnail_url if hasattr(media, "thumbnail_url") else None
        })
    
    return templates.TemplateResponse(
        "admin/product_form.html",
        {
            "request": request,
            "active_page": "products",
            "tenant": tenant_obj,
            "tenant_id": str(tenant_obj.id),
            "categories": categories,
            "media_files": media_list,
            "form_action": "/admin/products/add",
            "form_title": "Add New Product",
            "cart_item_count": request.session.get("cart_item_count", 0)
        }
    )

@router.post("/products/add", response_class=RedirectResponse)
async def admin_add_product(
    request: Request,
    tenant_id: str = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    sku: str = Form(...),
    stock: int = Form(0),
    categories: List[str] = Form([]),
    image_url: Optional[str] = Form(None),
    metadata: Optional[Dict[str, Any]] = Form({})
):
    """Add a new product."""
    try:
        # Create product data
        product_data = {
            "tenant_id": tenant_id,
            "name": name,
            "description": description,
            "price": price,
            "sku": sku,
            "stock": stock,
            "categories": categories,
            "image_url": image_url,
            "metadata": metadata or {}
        }
        
        # Add image URL to metadata if provided
        if image_url:
            product_data["metadata"]["image_url"] = image_url
        
        # Create product
        product = product_manager.create(product_data)
        
        return RedirectResponse(
            url="/admin/products?status_message=Product+created+successfully&status_type=success", 
            status_code=303
        )
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        error_message = f"Error creating product: {str(e)}"
        return RedirectResponse(
            url=f"/admin/products?status_message={error_message}&status_type=danger", 
            status_code=303
        )

@router.get("/products/edit/{product_id}", response_class=HTMLResponse)
async def admin_edit_product(
    request: Request,
    product_id: str
):
    """Admin form for editing a product."""
    try:
        # Get product
        product = product_manager.get(product_id)
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")
        
        # Get tenant for the product
        tenant_id = str(product.tenant_id) if hasattr(product, "tenant_id") else None
        
        if not tenant_id:
            # Try to get tenant ID from metadata
            tenant_id = product.metadata.get("tenant_id") if hasattr(product, "metadata") else None
            
        if not tenant_id:
            raise ValueError(f"Cannot determine tenant for product {product_id}")
        
        # Get tenant object
        tenant_obj = tenant_manager.get(tenant_id)
        if not tenant_obj:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        # Get categories for tenant
        categories = []
        if category_manager:
            try:
                categories = category_manager.get_by_tenant(tenant_id)
            except Exception as e:
                logger.warning(f"Error getting categories: {str(e)}")
        
        # Get media files for tenant
        media_files = []
        try:
            media_files = media_service.list_media(tenant_id=tenant_id, file_type="image")
        except Exception as e:
            logger.warning(f"Error getting media files: {str(e)}")
        
        # Format media for template
        media_list = []
        for media in media_files:
            media_list.append({
                "id": str(media.id),
                "name": media.name if hasattr(media, "name") else (media.file_name if hasattr(media, "file_name") else ""),
                "url": media.file_url if hasattr(media, "file_url") else (media.url if hasattr(media, "url") else ""),
                "thumbnail_url": media.thumbnail_url if hasattr(media, "thumbnail_url") else None
            })
        
        # Get product image URL from metadata
        image_url = None
        if hasattr(product, "metadata") and product.metadata:
            image_url = product.metadata.get("image_url")
        
        # Prepare product data for template
        product_data = {
            "id": str(product.id),
            "name": product.name,
            "description": product.description if hasattr(product, "description") else "",
            "price": product.price,
            "sku": product.sku if hasattr(product, "sku") else "",
            "stock": product.stock if hasattr(product, "stock") else 0,
            "categories": product.categories if hasattr(product, "categories") else [],
            "image_url": image_url
        }
        
        return templates.TemplateResponse(
            "admin/product_form.html",
            {
                "request": request,
                "active_page": "products",
                "tenant": tenant_obj,
                "tenant_id": tenant_id,
                "product": product_data,
                "categories": categories,
                "media_files": media_list,
                "form_action": f"/admin/products/update/{product_id}",
                "form_title": "Edit Product",
                "cart_item_count": request.session.get("cart_item_count", 0)
            }
        )
    except Exception as e:
        logger.error(f"Error editing product: {str(e)}")
        error_message = f"Error editing product: {str(e)}"
        return RedirectResponse(
            url=f"/admin/products?status_message={error_message}&status_type=danger", 
            status_code=303
        )

@router.post("/products/update/{product_id}", response_class=RedirectResponse)
async def admin_update_product(
    request: Request,
    product_id: str,
    tenant_id: str = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    sku: str = Form(...),
    stock: int = Form(0),
    categories: List[str] = Form([]),
    image_url: Optional[str] = Form(None)
):
    """Update a product."""
    try:
        # Prepare product data
        product_data = {
            "name": name,
            "description": description,
            "price": price,
            "sku": sku,
            "stock": stock,
            "categories": categories
        }
        
        # Get current product to update metadata
        current_product = product_manager.get(product_id)
        
        # Create metadata if it doesn't exist
        metadata = getattr(current_product, "metadata", {}) or {}
        
        # Update image URL in metadata
        if image_url:
            metadata["image_url"] = image_url
            
        # Set updated metadata
        product_data["metadata"] = metadata
        
        # Update product
        product = product_manager.update(product_id, **product_data)
        
        return RedirectResponse(
            url="/admin/products?status_message=Product+updated+successfully&status_type=success", 
            status_code=303
        )
    except Exception as e:
        logger.error(f"Error updating product: {str(e)}")
        error_message = f"Error updating product: {str(e)}"
        return RedirectResponse(
            url=f"/admin/products?status_message={error_message}&status_type=danger", 
            status_code=303
        )

@router.get("/products/delete/{product_id}", response_class=RedirectResponse)
async def admin_delete_product(
    request: Request,
    product_id: str
):
    """Delete a product."""
    try:
        # Delete product
        product_manager.delete(product_id)
        
        return RedirectResponse(
            url="/admin/products?status_message=Product+deleted+successfully&status_type=success", 
            status_code=303
        )
    except Exception as e:
        logger.error(f"Error deleting product: {str(e)}")
        error_message = f"Error deleting product: {str(e)}"
        return RedirectResponse(
            url=f"/admin/products?status_message={error_message}&status_type=danger", 
            status_code=303
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