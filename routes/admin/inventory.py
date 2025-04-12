
"""
Admin interface for inventory management.

This module provides routes for managing product inventory in the admin interface.
"""
import logging
from typing import Optional, Dict, List, Any
from uuid import UUID
from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from pycommerce.models.tenant import TenantManager
from pycommerce.models.inventory import InventoryManager
from pycommerce.models.product import ProductManager

# Set up logging
logger = logging.getLogger(__name__)

# Router and templates to be initialized in setup_routes
router = APIRouter(prefix="/admin/inventory", tags=["admin", "inventory"])
templates = None

# Initialize managers
tenant_manager = TenantManager()
inventory_manager = InventoryManager()
product_manager = ProductManager()

def setup_routes(jinja_templates: Jinja2Templates):
    """
    Set up routes with the given templates.
    
    Args:
        jinja_templates: The Jinja2Templates instance to use
    
    Returns:
        The router to be included in the main app
    """
    global templates
    templates = jinja_templates
    
    return router

@router.get("", response_class=HTMLResponse)
async def inventory_list(
    request: Request,
    tenant: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    min_stock: Optional[int] = Query(None),
    max_stock: Optional[int] = Query(None)
):
    """
    List all inventory items with optional filtering.
    
    Args:
        request: The request object
        tenant: Optional tenant filter
        search: Optional search query
        category: Optional category filter
        min_stock: Optional minimum stock filter
        max_stock: Optional maximum stock filter
        
    Returns:
        HTML response with inventory list
    """
    # Get all tenants for dropdown
    tenants = tenant_manager.list()
    
    # Build filters
    filters = {}
    if search:
        filters["search"] = search
    if category:
        filters["category"] = category
    if min_stock is not None:
        filters["min_stock"] = min_stock
    if max_stock is not None:
        filters["max_stock"] = max_stock
    
    # Get selected tenant
    selected_tenant_slug = tenant or "all"
    tenant_obj = None
    
    if selected_tenant_slug.lower() != "all":
        tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
        if not tenant_obj:
            return RedirectResponse(url="/admin/inventory")
    
    # Handle "All Stores" selection
if selected_tenant_slug.lower() == "all":
    # Show inventory for all tenants
    from routes.admin.tenant_utils import get_items_for_all_tenants
    logger.info("Showing inventory for all tenants")

    inventory_items = get_items_for_all_tenants(
        tenant_manager=tenant_manager,
        item_manager=inventory_manager,
        get_method_name='get_by_tenant',
        logger=logger,
        filters=filters
    )
else:
    # Show inventory for specific tenant
    logger.info(f"Showing inventory for tenant: {tenant_obj.name}")
    
    inventory_items = inventory_manager.get_by_tenant(str(tenant_obj.id), filters)
    
    # Enhance inventory items with product info
    for item in inventory_items:
        product = product_manager.get(item.product_id, tenant_obj.id)
        if product:
            item.product_name = product.name
            item.product_sku = product.sku
        else:
            item.product_name = "Unknown Product"
            item.product_sku = "N/A"
    
    # Sort by stock level (low to high)
    inventory_items.sort(key=lambda x: x.stock)
    
    return templates.TemplateResponse(
        "admin/inventory.html",
        {
            "request": request,
            "inventory_items": inventory_items,
            "tenants": tenants,
            "selected_tenant": tenant_obj,
            "selected_tenant_slug": selected_tenant_slug,
            "filters": filters,
            "title": "Inventory Management"
        }
    )

@router.get("/{inventory_id}", response_class=HTMLResponse)
async def inventory_detail(
    request: Request,
    inventory_id: UUID,
    tenant: Optional[str] = Query(None)
):
    """
    Show inventory detail.
    
    Args:
        request: The request object
        inventory_id: The inventory item ID
        tenant: Optional tenant filter
        
    Returns:
        HTML response with inventory detail
    """
    # Get selected tenant
    tenant_obj = None
    if tenant:
        tenant_obj = tenant_manager.get_by_slug(tenant)
    
    if not tenant_obj:
        return RedirectResponse(url="/admin/inventory")
    
    # Get inventory item
    inventory_item = inventory_manager.get(str(inventory_id))
    
    if not inventory_item:
        return RedirectResponse(url="/admin/inventory")
    
    # Get product
    product = product_manager.get(inventory_item.product_id, tenant_obj.id)
    
    # Get transaction history
    transactions = inventory_manager.get_transactions(str(inventory_id))
    
    return templates.TemplateResponse(
        "admin/inventory_detail.html",
        {
            "request": request,
            "inventory_item": inventory_item,
            "product": product,
            "transactions": transactions,
            "tenant": tenant_obj,
            "title": f"Inventory for {product.name if product else 'Unknown Product'}"
        }
    )

@router.post("/{inventory_id}/adjust", response_class=HTMLResponse)
async def inventory_adjust(
    request: Request,
    inventory_id: UUID,
    adjustment: int = Form(...),
    reason: str = Form(...),
    tenant: str = Form(...)
):
    """
    Adjust inventory level.
    
    Args:
        request: The request object
        inventory_id: The inventory item ID
        adjustment: The amount to adjust
        reason: The reason for adjustment
        tenant: The tenant slug
        
    Returns:
        Redirect to inventory detail
    """
    # Get selected tenant
    tenant_obj = tenant_manager.get_by_slug(tenant)
    
    if not tenant_obj:
        return RedirectResponse(url="/admin/inventory")
    
    # Adjust inventory
    success = inventory_manager.adjust(
        inventory_id=str(inventory_id),
        adjustment=adjustment,
        reason=reason
    )
    
    if success:
        return RedirectResponse(
            url=f"/admin/inventory/{inventory_id}?tenant={tenant}",
            status_code=303
        )
    else:
        # Handle error
        inventory_item = inventory_manager.get(str(inventory_id))
        product = product_manager.get(inventory_item.product_id, tenant_obj.id)
        transactions = inventory_manager.get_transactions(str(inventory_id))
        
        return templates.TemplateResponse(
            "admin/inventory_detail.html",
            {
                "request": request,
                "inventory_item": inventory_item,
                "product": product,
                "transactions": transactions,
                "tenant": tenant_obj,
                "error": "Failed to adjust inventory",
                "title": f"Inventory for {product.name if product else 'Unknown Product'}"
            }
        )
