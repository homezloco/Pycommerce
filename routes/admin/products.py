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
        logger.info(f"Attempting to update product ID: {product_id}")
        
        # Find the product in all available tenants
        product_obj = None
        old_tenant_id = None
        
        # Get tenant object
        tenant_obj = None
        try:
            tenant_obj = tenant_manager.get(tenant_id)
            if tenant_obj:
                logger.info(f"Target tenant for update: {tenant_obj.name} (ID: {tenant_id})")
        except Exception as e:
            logger.warning(f"Error retrieving tenant with ID {tenant_id}: {str(e)}")
        
        # Search each tenant for the product
        all_tenants = tenant_manager.list()
        for t in all_tenants:
            try:
                logger.info(f"Checking for product in tenant: {t.name} (ID: {t.id})")
                tenant_products = product_manager.get_by_tenant(str(t.id))
                for prod in tenant_products:
                    if str(prod.id) == product_id:
                        product_obj = prod
                        old_tenant_id = str(t.id)
                        logger.info(f"Found product {product_id} in tenant {t.name} (ID: {t.id})")
                        break
                if product_obj:
                    break
            except Exception as e:
                logger.warning(f"Error checking tenant {t.name}: {str(e)}")
        
        if not product_obj:
            error_message = f"Product with ID {product_id} not found in any tenant"
            logger.error(error_message)
            return RedirectResponse(
                url=f"/admin/products?status_message={error_message}&status_type=danger",
                status_code=303
            )
        
        # Parse categories string to list
        categories_list = []
        if categories:
            categories_list = [cat.strip() for cat in categories.split(",") if cat.strip()]
        
        # Check if we need to move the product to a different tenant
        tenant_changed = old_tenant_id != tenant_id
        if tenant_changed:
            logger.info(f"Product is being moved from tenant ID {old_tenant_id} to tenant ID {tenant_id}")
        
        # Update the product
        try:
            logger.info(f"Updating product {product_id} with new values")
            
            # Create metadata dictionary with existing values plus new ones
            metadata = {}
            if hasattr(product_obj, 'metadata') and product_obj.metadata:
                metadata = dict(product_obj.metadata)
            
            metadata["tenant_id"] = tenant_id
            if image_url:
                metadata["image_url"] = image_url
            
            product_manager.update(
                product_id=product_id,
                name=name,
                sku=sku,
                price=price,
                stock=stock,
                categories=categories_list,
                description=description,
                metadata=metadata
            )
            
            logger.info(f"Product {product_id} updated successfully")
        except Exception as update_error:
            logger.error(f"Error in product_manager.update: {str(update_error)}")
            # If direct update fails, try tenant-specific update method
            try:
                logger.info("Trying tenant-specific update method")
                # Get the product schema used by the API
                from pycommerce.models.product import Product as ProductSchema
                
                # Create a product schema object with updated values
                updated_product = ProductSchema(
                    id=product_id,
                    name=name,
                    sku=sku,
                    price=price,
                    stock=stock,
                    categories=categories_list,
                    description=description,
                    metadata={
                        "tenant_id": tenant_id,
                        "image_url": image_url
                    }
                )
                
                # Try update_for_tenant first with new tenant ID
                product_manager.update_for_tenant(tenant_id=tenant_id, product=updated_product)
                logger.info(f"Product {product_id} updated for tenant {tenant_id}")
            except Exception as tenant_update_error:
                logger.error(f"Error in tenant-specific update: {str(tenant_update_error)}")
                raise tenant_update_error
        
        # Get the tenant slug for the redirect
        tenant_slug = ""
        if tenant_obj:
            tenant_slug = tenant_obj.slug
        
        # If we have a tenant slug, include it in the redirect
        redirect_url = "/admin/products"
        if tenant_slug:
            redirect_url += f"?tenant={tenant_slug}"
        
        return RedirectResponse(
            url=f"{redirect_url}&status_message=Product+updated+successfully&status_type=success",
            status_code=303
        )
    except Exception as e:
        logger.error(f"Error updating product: {str(e)}")
        return RedirectResponse(
            url=f"/admin/products?status_message=Error+updating+product:+{str(e)}&status_type=danger",
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
        # Debug product_id to make sure it's correct
        logger.info(f"Attempting to edit product with ID: {product_id}")
        
        # Find the product in all available tenants
        product_obj = None
        tenant_obj = None
        
        # If tenant is provided in the URL, try to get it from that specific tenant
        if tenant:
            try:
                tenant_obj = tenant_manager.get_by_slug(tenant)
                if tenant_obj:
                    logger.info(f"Looking for product {product_id} in tenant {tenant} (ID: {tenant_obj.id})")
                    products = product_manager.get_by_tenant(str(tenant_obj.id))
                    for prod in products:
                        if str(prod.id) == product_id:
                            product_obj = prod
                            logger.info(f"Found product {product_id} in tenant {tenant}")
                            break
            except Exception as tenant_err:
                logger.warning(f"Error getting tenant {tenant}: {str(tenant_err)}")
        
        # If not found yet, search in all tenants
        if not product_obj:
            logger.info("Product not found in specified tenant, searching in all tenants")
            all_tenants = tenant_manager.list()
            for t in all_tenants:
                try:
                    logger.info(f"Checking tenant: {t.name} (ID: {t.id})")
                    tenant_products = product_manager.get_by_tenant(str(t.id))
                    for prod in tenant_products:
                        if str(prod.id) == product_id:
                            product_obj = prod
                            tenant_obj = t
                            logger.info(f"Found product {product_id} in tenant {t.name}")
                            break
                    if product_obj:
                        break
                except Exception as e:
                    logger.warning(f"Error checking tenant {t.name}: {str(e)}")
                    continue
        
        if not product_obj:
            logger.error(f"Product with ID {product_id} not found in any tenant")
            return RedirectResponse(
                url=f"/admin/products?status_message=Product+not+found&status_type=danger", 
                status_code=303
            )
        
        # Get tenant ID from metadata or from the found tenant
        tenant_id = None
        if hasattr(product_obj, 'metadata') and product_obj.metadata and 'tenant_id' in product_obj.metadata:
            tenant_id = product_obj.metadata.get('tenant_id')
        elif tenant_obj:
            tenant_id = str(tenant_obj.id)
        
        # Format product for template
        product = {
            "id": str(product_obj.id),
            "name": product_obj.name,
            "sku": product_obj.sku,
            "price": product_obj.price,
            "stock": product_obj.stock,
            "categories": product_obj.categories if hasattr(product_obj, 'categories') else [],
            "description": product_obj.description if hasattr(product_obj, 'description') else "",
            "image_url": product_obj.metadata.get('image_url') if hasattr(product_obj, 'metadata') and product_obj.metadata else None,
            "tenant_id": tenant_id
        }
        
        logger.info(f"Formatted product for template: {product['name']} (ID: {product['id']})")
        
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