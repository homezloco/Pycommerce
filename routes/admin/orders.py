"""
Admin routes for order management.

This module contains all the routes for managing orders in the admin interface.
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

# Template setup will be passed from main app
templates = None

# Initialize logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])

# Import models and managers for orders using the correct implementation
from pycommerce.models.order import OrderManager, OrderStatus
from pycommerce.models.order_note import OrderNoteManager
from pycommerce.models.tenant import TenantManager

# Initialize managers
order_manager = OrderManager()
order_note_manager = OrderNoteManager()
tenant_manager = TenantManager()

@router.get("/orders", response_class=HTMLResponse)
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
    # Get tenant from session
    selected_tenant_slug = request.session.get("selected_tenant")
    
    # If no tenant is selected, redirect to dashboard with message
    if not selected_tenant_slug:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Please+select+a+store+first&status_type=warning", 
            status_code=303
        )
    
    # Get tenant object using tenant_manager
    tenant = tenant_manager.get_by_slug(selected_tenant_slug)
    if not tenant:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Store+not+found&status_type=error", 
            status_code=303
        )
    
    # Convert status string to enum if provided
    order_status = None
    if status:
        try:
            order_status = OrderStatus(status)
        except ValueError:
            logger.warning(f"Invalid order status: {status}")
    
    # Get orders filtered by tenant and other criteria
    filters = {}
    if order_status:
        filters['status'] = order_status
    if date_from:
        filters['date_from'] = date_from
    if date_to:
        filters['date_to'] = date_to
    if email:
        filters['customer_email'] = email
        
    orders = order_manager.get_for_tenant(
        tenant.id,
        filters=filters if filters else None
    )
    
    # Serialize orders for template
    orders_data = []
    for order in orders:
        # Get items count safely (order might be detached from session)
        items_count = 0
        try:
            # Try to get items count if available
            if hasattr(order, 'items') and order.items is not None:
                items_count = len(order.items)
        except Exception as e:
            logger.warning(f"Could not get items count for order {order.id}: {e}")
            
        orders_data.append({
            "id": str(order.id),
            "customer_name": order.customer_name or "",
            "customer_email": order.customer_email or "",
            "total": order.total,
            "status": order.status.value,
            "items_count": items_count,
            "created_at": order.created_at
        })
    
    # Get all possible order statuses for filter dropdown
    status_options = [status.value for status in OrderStatus]
    
    return templates.TemplateResponse(
        "admin/orders.html",
        {
            "request": request,
            "orders": orders_data,
            "selected_tenant": selected_tenant_slug,
            "tenant": tenant,
            "status_options": status_options,
            "filters": {
                "status": status,
                "date_from": date_from,
                "date_to": date_to,
                "email": email
            },
            "status_message": status_message,
            "status_type": status_type,
            "cart_item_count": request.session.get("cart_item_count", 0)
        }
    )

@router.get("/orders/{order_id}", response_class=HTMLResponse)
async def admin_order_detail(
    request: Request,
    order_id: str,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for viewing order details."""
    # Get tenant from session
    selected_tenant_slug = request.session.get("selected_tenant")
    
    # If no tenant is selected, redirect to dashboard with message
    if not selected_tenant_slug:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Please+select+a+store+first&status_type=warning", 
            status_code=303
        )
    
    # Get tenant object
    tenant = tenant_manager.get_by_slug(selected_tenant_slug)
    if not tenant:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Store+not+found&status_type=error", 
            status_code=303
        )
    
    try:
        # Get order
        order = order_manager.get_by_id(order_id)
        if not order:
            return RedirectResponse(
                url=f"/admin/orders?status_message=Order+not+found&status_type=error", 
                status_code=303
            )
        
        # Verify order belongs to the selected tenant
        if str(order.tenant_id) != str(tenant.id):
            return RedirectResponse(
                url=f"/admin/orders?status_message=Order+not+found+for+this+store&status_type=error", 
                status_code=303
            )
        
        # Get order notes
        try:
            notes = order_note_manager.get_for_order(order_id)
            notes_data = []
            # Check if notes is iterable
            if hasattr(notes, '__iter__'):
                for note in notes:
                    notes_data.append({
                        "id": str(note.id),
                        "content": note.content,
                        "created_at": note.created_at,
                        "is_customer_note": note.is_customer_note
                    })
            else:
                logger.warning(f"Notes is not an iterable: {type(notes)}")
                notes_data = []
        except Exception as note_error:
            logger.warning(f"Error processing order notes: {note_error}")
            notes_data = []
        
        # Format items for display - safely handle possibly detached items
        items_data = []
        try:
            if hasattr(order, 'items') and order.items is not None:
                for item in order.items:
                    try:
                        # Get product name and SKU safely
                        name = getattr(item, 'name', None)
                        if name is None and hasattr(item, 'product') and item.product:
                            name = item.product.name
                        
                        sku = getattr(item, 'sku', None)
                        if sku is None and hasattr(item, 'product') and item.product:
                            sku = item.product.sku
                            
                        items_data.append({
                            "product_id": str(item.product_id),
                            "name": name or "Unknown Product",
                            "sku": sku or "N/A",
                            "quantity": item.quantity,
                            "price": item.price,
                            "total": item.price * item.quantity
                        })
                    except Exception as e:
                        logger.warning(f"Error processing order item: {e}")
        except Exception as e:
            logger.warning(f"Could not access order items: {e}")
        
        # Format order data for template
        order_data = {
            "id": str(order.id),
            "customer_name": order.customer_name or "",
            "customer_email": order.customer_email or "",
            "shipping_address": {
                "address_line1": order.shipping_address_line1 or "",
                "address_line2": order.shipping_address_line2 or "",
                "city": order.shipping_city or "",
                "state": order.shipping_state or "",
                "postal_code": order.shipping_postal_code or "",
                "country": order.shipping_country or ""
            },
            "subtotal": order.subtotal,
            "tax": order.tax,
            "shipping_cost": order.shipping_cost,
            "total": order.total,
            "status": order.status.value,
            "payment_id": getattr(order, 'payment_transaction_id', None),
            "items": items_data,
            "created_at": order.created_at,
            "notes": notes_data
        }
        
        # Get all possible order statuses for status dropdown
        status_options = [status.value for status in OrderStatus]
        
        return templates.TemplateResponse(
            "admin/order_detail.html",
            {
                "request": request,
                "order": order_data,
                "selected_tenant": selected_tenant_slug,
                "tenant": tenant,
                "status_options": status_options,
                "status_message": status_message,
                "status_type": status_type,
                "cart_item_count": request.session.get("cart_item_count", 0)
            }
        )
    
    except Exception as e:
        logger.error(f"Error getting order details: {str(e)}")
        return RedirectResponse(
            url=f"/admin/orders?status_message=Error+loading+order:+{str(e)}&status_type=error", 
            status_code=303
        )

@router.get("/orders/{order_id}/status/{status}", response_class=RedirectResponse)
async def admin_update_order_status(request: Request, order_id: str, status: str):
    """Update order status and redirect back to order details."""
    try:
        # Validate status
        try:
            order_status = OrderStatus(status)
        except ValueError:
            return RedirectResponse(
                url=f"/admin/orders/{order_id}?status_message=Invalid+order+status&status_type=error", 
                status_code=303
            )
        
        # Update order status
        success = order_manager.update_status(order_id, order_status)
        if success:
            return RedirectResponse(
                url=f"/admin/orders/{order_id}?status_message=Order+status+updated+successfully&status_type=success", 
                status_code=303
            )
        else:
            return RedirectResponse(
                url=f"/admin/orders/{order_id}?status_message=Failed+to+update+order+status&status_type=error", 
                status_code=303
            )
    
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")
        return RedirectResponse(
            url=f"/admin/orders/{order_id}?status_message=Error+updating+order+status:+{str(e)}&status_type=error", 
            status_code=303
        )

@router.get("/orders/{order_id}/fulfillment", response_class=HTMLResponse)
async def admin_order_fulfillment(
    request: Request,
    order_id: str,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for order fulfillment."""
    # Get tenant from session
    selected_tenant_slug = request.session.get("selected_tenant")
    
    # If no tenant is selected, redirect to dashboard with message
    if not selected_tenant_slug:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Please+select+a+store+first&status_type=warning", 
            status_code=303
        )
    
    # Get tenant object
    tenant = tenant_manager.get_by_slug(selected_tenant_slug)
    if not tenant:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Store+not+found&status_type=error", 
            status_code=303
        )
    
    try:
        # Get order
        order = order_manager.get_by_id(order_id)
        if not order:
            return RedirectResponse(
                url=f"/admin/orders?status_message=Order+not+found&status_type=error", 
                status_code=303
            )
        
        # Verify order belongs to the selected tenant
        if str(order.tenant_id) != str(tenant.id):
            return RedirectResponse(
                url=f"/admin/orders?status_message=Order+not+found+for+this+store&status_type=error", 
                status_code=303
            )
        
        # Format items for display - safely handle possibly detached items
        items_data = []
        try:
            if hasattr(order, 'items') and order.items is not None:
                for item in order.items:
                    try:
                        # Get product name and SKU safely
                        name = getattr(item, 'name', None)
                        if name is None and hasattr(item, 'product') and item.product:
                            name = item.product.name
                        
                        sku = getattr(item, 'sku', None)
                        if sku is None and hasattr(item, 'product') and item.product:
                            sku = item.product.sku
                            
                        items_data.append({
                            "product_id": str(item.product_id),
                            "name": name or "Unknown Product",
                            "sku": sku or "N/A",
                            "quantity": item.quantity,
                            "price": item.price,
                            "total": item.price * item.quantity
                        })
                    except Exception as e:
                        logger.warning(f"Error processing order item: {e}")
        except Exception as e:
            logger.warning(f"Could not access order items: {e}")
        
        # Get available shipping carriers
        carriers = ["FedEx", "UPS", "USPS", "DHL"]
        
        # Get shipping statuses
        shipping_statuses = ["pending", "ready", "shipped", "delivered", "returned"]
        
        # Format order data for template
        order_data = {
            "id": str(order.id),
            "customer_name": order.customer_name or "",
            "customer_email": order.customer_email or "",
            "shipping_address": {
                "address_line1": order.shipping_address_line1 or "",
                "address_line2": order.shipping_address_line2 or "",
                "city": order.shipping_city or "",
                "state": order.shipping_state or "",
                "postal_code": order.shipping_postal_code or "",
                "country": order.shipping_country or ""
            },
            "subtotal": order.subtotal,
            "tax": order.tax,
            "shipping_cost": order.shipping_cost,
            "total": order.total,
            "status": order.status.value,
            "payment_id": getattr(order, 'payment_transaction_id', None),
            "tracking_number": getattr(order, 'tracking_number', ''),
            "shipping_carrier": getattr(order, 'shipping_carrier', ''),
            "shipped_at": getattr(order, 'shipped_at', None),
            "delivered_at": getattr(order, 'delivered_at', None),
            "items": items_data,
            "created_at": order.created_at
        }
        
        return templates.TemplateResponse(
            "admin/order_fulfillment.html",
            {
                "request": request,
                "order": order_data,
                "selected_tenant": selected_tenant_slug,
                "tenant": tenant,
                "carriers": carriers,
                "shipping_statuses": shipping_statuses,
                "status_message": status_message,
                "status_type": status_type,
                "cart_item_count": request.session.get("cart_item_count", 0)
            }
        )
    
    except Exception as e:
        logger.error(f"Error getting fulfillment details: {str(e)}")
        return RedirectResponse(
            url=f"/admin/orders?status_message=Error+loading+fulfillment:+{str(e)}&status_type=error", 
            status_code=303
        )

@router.post("/orders/{order_id}/fulfillment", response_class=RedirectResponse)
async def admin_update_fulfillment(
    request: Request,
    order_id: str,
    shipping_status: str = Form(...),
    tracking_number: Optional[str] = Form(None),
    shipping_carrier: Optional[str] = Form(None)
):
    """Update order fulfillment information."""
    try:
        # Update the shipping information
        success = order_manager.update_shipping(
            order_id=order_id,
            status=shipping_status,
            tracking_number=tracking_number,
            carrier=shipping_carrier
        )
        
        if success:
            return RedirectResponse(
                url=f"/admin/orders/{order_id}/fulfillment?status_message=Shipping+information+updated+successfully&status_type=success", 
                status_code=303
            )
        else:
            return RedirectResponse(
                url=f"/admin/orders/{order_id}/fulfillment?status_message=Failed+to+update+shipping+information&status_type=error", 
                status_code=303
            )
    
    except Exception as e:
        logger.error(f"Error updating shipping information: {str(e)}")
        return RedirectResponse(
            url=f"/admin/orders/{order_id}/fulfillment?status_message=Error+updating+shipping:+{str(e)}&status_type=error", 
            status_code=303
        )

@router.post("/orders/{order_id}/notes", response_class=RedirectResponse)
async def admin_add_order_note(
    request: Request,
    order_id: str,
    content: str = Form(...),
    notify_customer: Optional[str] = Form(None)
):
    """Add a note to an order."""
    try:
        # Determine if this is a customer note
        is_customer_note = notify_customer is not None
        
        # Add note to order
        success = order_note_manager.add_note(
            order_id=order_id,
            content=content,
            is_customer_note=is_customer_note
        )
        
        if success:
            # If it's a customer note, we could send an email to the customer here
            if is_customer_note:
                # TODO: Send email to customer with note content
                pass
            
            return RedirectResponse(
                url=f"/admin/orders/{order_id}?status_message=Note+added+successfully&status_type=success", 
                status_code=303
            )
        else:
            return RedirectResponse(
                url=f"/admin/orders/{order_id}?status_message=Failed+to+add+note&status_type=error", 
                status_code=303
            )
    
    except Exception as e:
        logger.error(f"Error adding order note: {str(e)}")
        return RedirectResponse(
            url=f"/admin/orders/{order_id}?status_message=Error+adding+note:+{str(e)}&status_type=error", 
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