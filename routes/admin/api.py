"""
Admin API routes for the PyCommerce admin panel.

This module provides general-purpose API endpoints used throughout the admin panel,
including endpoints for tenant verification, status checks, and utilities.
"""
import logging
from typing import Dict, Optional, List, Any

from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse

from pycommerce.models.tenant import TenantManager
from pycommerce.models.product import ProductManager
from pycommerce.core.db import SessionLocal

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin/api", tags=["admin", "api"])

# Initialize managers
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

@router.get("/tenant-check", tags=["admin", "api"])
async def tenant_check(
    request: Request,
    slug: str = Query(..., description="Tenant slug to check")
):
    """
    Check if a tenant with the given slug exists.
    This endpoint is used by the page builder for tenant verification.
    """
    try:
        logger.info(f"Checking if tenant exists with slug: {slug}")
        
        if not tenant_manager:
            logger.error("TenantManager not available")
            return JSONResponse(
                status_code=500,
                content={"error": "Tenant manager not available"}
            )
        
        # Try to get the tenant by slug
        tenant = tenant_manager.get_by_slug(slug)
        
        if tenant:
            logger.info(f"Tenant found: {tenant.name} (ID: {tenant.id})")
            return {
                "exists": True,
                "tenant": {
                    "id": str(tenant.id),
                    "name": tenant.name,
                    "slug": tenant.slug
                }
            }
        else:
            logger.info(f"No tenant found with slug: {slug}")
            return {"exists": False}
            
    except Exception as e:
        logger.error(f"Error checking tenant: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error checking tenant: {str(e)}"}
        )

@router.get("/tenants/{tenant_id}", tags=["admin", "api"])
async def get_tenant(
    request: Request,
    tenant_id: str
):
    """
    Get tenant information by ID.
    This endpoint is used by the page builder and other admin components.
    """
    try:
        logger.info(f"Getting tenant with ID: {tenant_id}")
        
        if not tenant_manager:
            logger.error("TenantManager not available")
            return JSONResponse(
                status_code=500,
                content={"error": "Tenant manager not available"}
            )
        
        # Try to get the tenant by ID
        tenant = tenant_manager.get(tenant_id)
        
        if tenant:
            logger.info(f"Tenant found: {tenant.name} (ID: {tenant.id})")
            return {
                "id": str(tenant.id),
                "name": tenant.name,
                "slug": tenant.slug,
                "domain": tenant.domain if hasattr(tenant, "domain") else None
            }
        else:
            logger.info(f"No tenant found with ID: {tenant_id}")
            return JSONResponse(
                status_code=404,
                content={"error": f"Tenant with ID {tenant_id} not found"}
            )
            
    except Exception as e:
        logger.error(f"Error getting tenant: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error getting tenant: {str(e)}"}
        )

@router.get("/products", tags=["admin", "api"])
async def admin_products_api(
    request: Request,
    tenant: Optional[str] = Query(None, description="Tenant slug to filter products by"),
    category: Optional[str] = Query(None, description="Category name to filter products by"),
    min_price: Optional[float] = Query(None, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, description="Maximum price filter"),
    in_stock: Optional[bool] = Query(None, description="Filter for products in stock")
):
    """
    Admin API endpoint to get products in JSON format.
    This endpoint is used by the page builder for product blocks.
    """
    try:
        logger.info(f"Admin API request for products with tenant={tenant}")
        
        if not product_manager:
            logger.error("ProductManager not available")
            return JSONResponse(
                status_code=500,
                content={"error": "Product manager not available"}
            )
        
        if not tenant_manager:
            logger.error("TenantManager not available")
            return JSONResponse(
                status_code=500,
                content={"error": "Tenant manager not available"}
            )
        
        # Find tenant
        tenant_obj = None
        if tenant:
            try:
                tenant_obj = tenant_manager.get_by_slug(tenant)
                logger.info(f"Found tenant: {tenant_obj.name} (ID: {tenant_obj.id})")
            except Exception as e:
                logger.warning(f"Error finding tenant with slug '{tenant}': {str(e)}")
        
        # If no specific tenant, use the first one as default
        if not tenant_obj:
            try:
                tenants_list = tenant_manager.list() or []
                if tenants_list:
                    tenant_obj = tenants_list[0]
                    logger.info(f"Using default tenant: {tenant_obj.name} (ID: {tenant_obj.id})")
            except Exception as e:
                logger.error(f"Error getting tenant list: {str(e)}")
                return {"error": f"Error getting tenant list: {str(e)}"}
        
        if not tenant_obj:
            return {"error": "No tenant found"}
            
        # Get products for the tenant
        products_list = []
        try:
            raw_products = product_manager.get_by_tenant(str(tenant_obj.id)) or []
            
            # Apply filters
            filtered_products = []
            for product in raw_products:
                # Check if product should be included based on filters
                if category and hasattr(product, 'categories') and category not in product.categories:
                    continue
                
                if min_price is not None and product.price < min_price:
                    continue
                    
                if max_price is not None and product.price > max_price:
                    continue
                    
                if in_stock is not None:
                    if in_stock and (not hasattr(product, 'stock') or product.stock <= 0):
                        continue
                    elif not in_stock and hasattr(product, 'stock') and product.stock > 0:
                        continue
                
                filtered_products.append(product)
            
            # Format products for JSON response
            for product in filtered_products:
                # Get image URL from metadata if available
                image_url = None
                if hasattr(product, 'metadata') and product.metadata:
                    image_url = product.metadata.get('image_url')
                
                products_list.append({
                    "id": str(product.id),
                    "name": product.name,
                    "sku": product.sku,
                    "price": product.price,
                    "stock": product.stock if hasattr(product, 'stock') else 0,
                    "categories": product.categories if hasattr(product, 'categories') else [],
                    "description": product.description if hasattr(product, 'description') else "",
                    "image_url": image_url,
                    "tenant_id": str(tenant_obj.id)
                })
                
            logger.info(f"Found {len(products_list)} products for tenant {tenant_obj.name}")
        except Exception as e:
            logger.error(f"Error getting products for tenant {tenant_obj.name}: {str(e)}")
            return {"error": f"Error getting products: {str(e)}"}
        
        return {
            "tenant": {
                "id": str(tenant_obj.id),
                "name": tenant_obj.name,
                "slug": tenant_obj.slug
            },
            "products": products_list,
            "count": len(products_list),
            "filters": {
                "category": category,
                "min_price": min_price,
                "max_price": max_price,
                "in_stock": in_stock
            }
        }
    except Exception as e:
        logger.error(f"Error in admin products API: {str(e)}")
        return {"error": f"Server error: {str(e)}"}

@router.get("/products/all", tags=["admin", "api"])
async def admin_all_products(request: Request):
    """
    Admin API endpoint to get all products across all tenants.
    This is a fallback endpoint for the page builder.
    """
    try:
        logger.info("Admin API request for ALL products across tenants")
        
        if not product_manager:
            logger.error("ProductManager not available")
            return JSONResponse(
                status_code=500,
                content={"error": "Product manager not available"}
            )
        
        if not tenant_manager:
            logger.error("TenantManager not available")
            return JSONResponse(
                status_code=500,
                content={"error": "Tenant manager not available"}
            )
        
        # Get all tenants
        all_tenants = []
        try:
            all_tenants = tenant_manager.list() or []
        except Exception as e:
            logger.error(f"Error getting tenant list: {str(e)}")
            return {"error": f"Error getting tenant list: {str(e)}"}
        
        # Collect all products from all tenants
        all_products = []
        for tenant in all_tenants:
            try:
                tenant_products = product_manager.get_by_tenant(str(tenant.id)) or []
                # Format products for JSON response
                for product in tenant_products:
                    # Get image URL from metadata if available
                    image_url = None
                    if hasattr(product, 'metadata') and product.metadata:
                        image_url = product.metadata.get('image_url')
                    
                    all_products.append({
                        "id": str(product.id),
                        "name": product.name,
                        "sku": product.sku,
                        "price": product.price,
                        "stock": product.stock if hasattr(product, 'stock') else 0,
                        "categories": product.categories if hasattr(product, 'categories') else [],
                        "description": product.description if hasattr(product, 'description') else "",
                        "image_url": image_url,
                        "tenant_id": str(tenant.id),
                        "tenant_name": tenant.name,
                        "tenant_slug": tenant.slug
                    })
            except Exception as e:
                logger.warning(f"Error getting products for tenant {tenant.name}: {str(e)}")
                continue
        
        logger.info(f"Found {len(all_products)} products across all tenants")
        
        return {
            "products": all_products,
            "count": len(all_products)
        }
    except Exception as e:
        logger.error(f"Error in admin all products API: {str(e)}")
        return {"error": f"Server error: {str(e)}"}

def setup_routes():
    """Set up the API routes."""
    return router