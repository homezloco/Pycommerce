"""
Admin routes for return and refund management.

This module contains all the routes for managing returns and refunds in the admin interface.
"""
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse

# Template setup will be passed from main app
templates = None

# Initialize logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])

# Import models and managers
from pycommerce.models.order import OrderManager, OrderStatus
from pycommerce.models.return_request import ReturnManager, ReturnStatus, ReturnReason
from pycommerce.models.tenant import TenantManager
from pycommerce.core.db import get_session

# Initialize managers
order_manager = OrderManager()
return_manager = ReturnManager()
tenant_manager = TenantManager()


def get_return_status_string(status):
    """Convert return status to a display-friendly string."""
    if hasattr(status, 'name'):
        return status.name
    return str(status).upper()


def setup_routes(app_templates):
    """
    Set up routes with the given templates.
    
    Args:
        app_templates: Jinja2Templates instance from the main app
    """
    global templates
    templates = app_templates
    return router


@router.get("/returns", response_class=HTMLResponse)
async def returns_list(
    request: Request,
    tenant: str = Query(None),
    status: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    status_message: str = Query(None),
    status_type: str = Query("info")
):
    """Returns list page."""
    # Get the selected tenant
    selected_tenant_slug = tenant or "tech"
    
    try:
        # Get tenant info
        tenant = tenant_manager.get_by_slug(selected_tenant_slug)
        if not tenant:
            return RedirectResponse(
                url="/admin?status_message=Tenant+not+found&status_type=error",
                status_code=303
            )
        
        # Prepare filters
        filters = {}
        if status:
            filters["status"] = status
        
        if date_from:
            try:
                filters["date_from"] = datetime.strptime(date_from, "%Y-%m-%d")
            except ValueError:
                logger.warning(f"Invalid date_from format: {date_from}")
        
        if date_to:
            try:
                filters["date_to"] = datetime.strptime(date_to, "%Y-%m-%d")
            except ValueError:
                logger.warning(f"Invalid date_to format: {date_to}")
        
        # Get returns for tenant
        return_requests = return_manager.get_for_tenant(tenant.id, filters=filters)
        
        # Prepare data for template
        returns_data = []
        for return_request in return_requests:
            order = order_manager.get_by_id(return_request.order_id)
            customer_name = order.customer_name if order else "Unknown"
            customer_email = order.customer_email if order else "Unknown"
            
            # Get item count
            items_count = len(return_request.items) if hasattr(return_request, 'items') and return_request.items else 0
            
            # Convert status to string
            status_value = get_return_status_string(return_request.status)
            
            returns_data.append({
                "id": return_request.id,
                "return_number": return_request.return_number,
                "order_id": return_request.order_id,
                "order_number": order.order_number if order else "Unknown",
                "customer_name": customer_name,
                "customer_email": customer_email,
                "status": status_value,
                "requested_at": return_request.requested_at,
                "items_count": items_count,
                "refund_amount": return_request.refund_amount or 0.0,
                "is_refunded": return_request.is_refunded
            })
        
        # Get all possible return statuses for filter dropdown
        status_options = [status.name for status in ReturnStatus]
        
        return templates.TemplateResponse(
            "admin/returns.html",
            {
                "request": request,
                "returns": returns_data,
                "selected_tenant": selected_tenant_slug,
                "tenant": tenant,
                "status_options": status_options,
                "filters": {
                    "status": status,
                    "date_from": date_from,
                    "date_to": date_to
                },
                "status_message": status_message,
                "status_type": status_type,
                "cart_item_count": request.session.get("cart_item_count", 0),
                "active_page": "returns"  # For sidebar highlighting
            }
        )
    
    except Exception as e:
        logger.error(f"Error getting returns list: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return RedirectResponse(
            url=f"/admin?status_message=Error+loading+returns:+{str(e)}&status_type=error",
            status_code=303
        )


@router.get("/returns/{return_id}", response_class=HTMLResponse)
async def return_detail(
    request: Request,
    return_id: str,
    tenant: str = Query(None),
    status_message: str = Query(None),
    status_type: str = Query("info")
):
    """Return detail page."""
    # Get the selected tenant
    selected_tenant_slug = tenant or "tech"
    
    try:
        # Get tenant info
        tenant = tenant_manager.get_by_slug(selected_tenant_slug)
        if not tenant:
            return RedirectResponse(
                url="/admin?status_message=Tenant+not+found&status_type=error",
                status_code=303
            )
        
        # Get return request
        return_request = return_manager.get_by_id(return_id)
        if not return_request:
            return RedirectResponse(
                url=f"/admin/returns?tenant={selected_tenant_slug}&status_message=Return+request+not+found&status_type=error",
                status_code=303
            )
        
        # Get order
        order = order_manager.get_by_id(return_request.order_id)
        if not order:
            return RedirectResponse(
                url=f"/admin/returns?tenant={selected_tenant_slug}&status_message=Order+not+found&status_type=error",
                status_code=303
            )
        
        # Convert status to string
        status_value = get_return_status_string(return_request.status)
        
        # Prepare return items data
        items_data = []
        total_refund_amount = 0.0
        
        for item in return_request.items:
            # Get product information
            product_name = "Unknown"
            product_sku = "Unknown"
            
            if hasattr(item, 'product') and item.product:
                product_name = item.product.name
                product_sku = item.product.sku
            
            refund_amount = item.refund_amount or 0.0
            total_refund_amount += refund_amount
            
            items_data.append({
                "id": item.id,
                "product_id": item.product_id,
                "product_name": product_name,
                "product_sku": product_sku,
                "quantity": item.quantity,
                "reason": item.reason,
                "condition": item.condition,
                "refund_amount": refund_amount,
                "restocked": item.restocked
            })
        
        # Get all possible return statuses for dropdown
        status_options = [status.name for status in ReturnStatus]
        
        # Get all possible return reasons for dropdown
        reason_options = [reason.name for reason in ReturnReason]
        
        return templates.TemplateResponse(
            "admin/return_detail.html",
            {
                "request": request,
                "return_request": return_request,
                "return_status": status_value,
                "order": order,
                "return_items": items_data,
                "total_refund_amount": total_refund_amount,
                "selected_tenant": selected_tenant_slug,
                "tenant": tenant,
                "status_options": status_options,
                "reason_options": reason_options,
                "status_message": status_message,
                "status_type": status_type,
                "cart_item_count": request.session.get("cart_item_count", 0),
                "active_page": "returns"  # For sidebar highlighting
            }
        )
    
    except Exception as e:
        logger.error(f"Error getting return details: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return RedirectResponse(
            url=f"/admin/returns?tenant={selected_tenant_slug}&status_message=Error+loading+return+details:+{str(e)}&status_type=error",
            status_code=303
        )


@router.post("/returns/{return_id}/status", response_class=HTMLResponse)
async def update_return_status(
    request: Request,
    return_id: str,
    status: str = Form(...),
    notes: str = Form(None),
    tenant: str = Form(...)
):
    """Update return status."""
    try:
        # Update status
        success = return_manager.update_return_status(return_id, status, notes)
        
        if success:
            status_message = f"Return status updated to {status}"
            status_type = "success"
        else:
            status_message = "Failed to update return status"
            status_type = "error"
        
        return RedirectResponse(
            url=f"/admin/returns/{return_id}?tenant={tenant}&status_message={status_message}&status_type={status_type}",
            status_code=303
        )
    
    except Exception as e:
        logger.error(f"Error updating return status: {str(e)}")
        return RedirectResponse(
            url=f"/admin/returns/{return_id}?tenant={tenant}&status_message=Error+updating+status:+{str(e)}&status_type=error",
            status_code=303
        )


@router.post("/returns/{return_id}/refund", response_class=HTMLResponse)
async def process_refund(
    request: Request,
    return_id: str,
    amount: float = Form(...),
    method: str = Form(...),
    transaction_id: str = Form(None),
    notes: str = Form(None),
    tenant: str = Form(...)
):
    """Process refund for return."""
    try:
        # Prepare refund data
        refund_data = {
            "amount": amount,
            "method": method,
            "transaction_id": transaction_id,
            "notes": notes
        }
        
        # Process refund
        success = return_manager.process_refund(return_id, refund_data)
        
        if success:
            status_message = f"Refund processed successfully"
            status_type = "success"
        else:
            status_message = "Failed to process refund"
            status_type = "error"
        
        return RedirectResponse(
            url=f"/admin/returns/{return_id}?tenant={tenant}&status_message={status_message}&status_type={status_type}",
            status_code=303
        )
    
    except Exception as e:
        logger.error(f"Error processing refund: {str(e)}")
        return RedirectResponse(
            url=f"/admin/returns/{return_id}?tenant={tenant}&status_message=Error+processing+refund:+{str(e)}&status_type=error",
            status_code=303
        )


@router.get("/orders/{order_id}/create-return", response_class=HTMLResponse)
async def create_return_form(
    request: Request,
    order_id: str,
    tenant: str = Query(None),
    status_message: str = Query(None),
    status_type: str = Query("info")
):
    """Create return form page."""
    # Get the selected tenant
    selected_tenant_slug = tenant or "tech"
    
    try:
        # Get tenant info
        tenant = tenant_manager.get_by_slug(selected_tenant_slug)
        if not tenant:
            return RedirectResponse(
                url="/admin?status_message=Tenant+not+found&status_type=error",
                status_code=303
            )
        
        # Get order
        order = order_manager.get_by_id(order_id)
        if not order:
            return RedirectResponse(
                url=f"/admin/orders?tenant={selected_tenant_slug}&status_message=Order+not+found&status_type=error",
                status_code=303
            )
        
        # Check if order can be returned (not cancelled, etc.)
        if order.status in ["CANCELLED", "REFUNDED"]:
            return RedirectResponse(
                url=f"/admin/orders/{order_id}?tenant={selected_tenant_slug}&status_message=Cannot+create+return+for+{order.status}+order&status_type=error",
                status_code=303
            )
        
        # Get all possible return reasons for dropdown
        reason_options = [reason.name for reason in ReturnReason]
        
        return templates.TemplateResponse(
            "admin/create_return.html",
            {
                "request": request,
                "order": order,
                "order_items": order.items,
                "selected_tenant": selected_tenant_slug,
                "tenant": tenant,
                "reason_options": reason_options,
                "status_message": status_message,
                "status_type": status_type,
                "cart_item_count": request.session.get("cart_item_count", 0),
                "active_page": "orders"  # Use orders for sidebar since this is initiated from the order page
            }
        )
    
    except Exception as e:
        logger.error(f"Error loading create return form: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return RedirectResponse(
            url=f"/admin/orders/{order_id}?tenant={selected_tenant_slug}&status_message=Error+loading+return+form:+{str(e)}&status_type=error",
            status_code=303
        )


@router.post("/orders/{order_id}/create-return", response_class=HTMLResponse)
async def create_return(
    request: Request,
    order_id: str,
    reason: str = Form(...),
    customer_comments: str = Form(None),
    tenant: str = Form(...)
):
    """Create a new return request."""
    try:
        # Prepare return data
        return_data = {
            "order_id": order_id,
            "reason": reason,
            "customer_comments": customer_comments,
            "status": ReturnStatus.REQUESTED.name,
            "requested_at": datetime.utcnow()
        }
        
        # Create return
        return_request = return_manager.create_return(return_data)
        
        if return_request:
            # Process form data to get selected items
            form_data = await request.form()
            has_items = False
            
            # Loop through form data to find items
            for key, value in form_data.items():
                if key.startswith("item_") and value == "on":
                    # Extract order item ID
                    order_item_id = key.replace("item_", "")
                    
                    # Get quantity and refund amount
                    quantity = int(form_data.get(f"quantity_{order_item_id}", 1))
                    refund_amount = float(form_data.get(f"refund_{order_item_id}", 0))
                    condition = form_data.get(f"condition_{order_item_id}", "Used")
                    item_reason = form_data.get(f"reason_{order_item_id}", reason)
                    
                    # Get product ID from order item
                    with get_session() as session:
                        from pycommerce.models.order_item import OrderItem
                        order_item = session.query(OrderItem).filter(OrderItem.id == order_item_id).first()
                        if order_item:
                            # Add item to return
                            item_data = {
                                "order_item_id": order_item_id,
                                "product_id": order_item.product_id,
                                "quantity": quantity,
                                "reason": item_reason,
                                "condition": condition,
                                "refund_amount": refund_amount
                            }
                            return_manager.add_item_to_return(return_request.id, item_data)
                            has_items = True
            
            if has_items:
                status_message = "Return request created successfully"
                status_type = "success"
                return RedirectResponse(
                    url=f"/admin/returns/{return_request.id}?tenant={tenant}&status_message={status_message}&status_type={status_type}",
                    status_code=303
                )
            else:
                # No items selected, delete the return request
                # This could be handled better by requiring at least one item
                status_message = "No items selected for return"
                status_type = "warning"
                return RedirectResponse(
                    url=f"/admin/orders/{order_id}/create-return?tenant={tenant}&status_message={status_message}&status_type={status_type}",
                    status_code=303
                )
        else:
            status_message = "Failed to create return request"
            status_type = "error"
            return RedirectResponse(
                url=f"/admin/orders/{order_id}?tenant={tenant}&status_message={status_message}&status_type={status_type}",
                status_code=303
            )
    
    except Exception as e:
        logger.error(f"Error creating return: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return RedirectResponse(
            url=f"/admin/orders/{order_id}?tenant={tenant}&status_message=Error+creating+return:+{str(e)}&status_type=error",
            status_code=303
        )