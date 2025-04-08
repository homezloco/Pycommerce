"""
Admin routes for order management.

This module contains all the routes for managing orders in the admin interface.
"""
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

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
from pycommerce.models.order_note import OrderNoteManager, OrderNote
from pycommerce.models.tenant import TenantManager
from pycommerce.core.db import get_session

# Initialize managers
order_manager = OrderManager()
order_note_manager = OrderNoteManager()
tenant_manager = TenantManager()

# Custom functions to avoid SQLAlchemy detached object issues
def get_notes_for_order(order_id):
    """Get notes for an order using a fresh session."""
    try:
        # Make sure order_id is a string
        order_id_str = str(order_id)
        
        # Create a new session and query the notes
        with get_session() as session:
            # Execute the query directly and fetch all results
            notes_query = session.query(OrderNote).filter(
                OrderNote.order_id == order_id_str
            ).order_by(OrderNote.created_at.desc())
            
            notes = notes_query.all()
            
            # Safely convert to dictionaries to avoid session issues
            result = []
            for note in notes:
                try:
                    note_dict = {
                        "id": str(note.id),
                        "content": note.content or "",
                        "created_at": note.created_at,
                        "is_customer_note": bool(note.is_customer_note)
                    }
                    result.append(note_dict)
                except Exception as note_err:
                    logger.error(f"Error processing note {getattr(note, 'id', 'unknown')}: {note_err}")
                    continue
                    
            return result
    except Exception as e:
        logger.error(f"Error getting notes for order {order_id}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Always return an empty list on error
        return []

def get_order_items(order_id):
    """Get items for an order using a fresh session to avoid detached object issues."""
    try:
        from pycommerce.models.order import OrderItem
        from pycommerce.models.product import Product
        
        with get_session() as session:
            # Get order items with join to products to ensure we get product details
            items = session.query(OrderItem).filter(
                OrderItem.order_id == str(order_id)
            ).all()
            
            # Convert to dictionaries to avoid session issues
            result = []
            for item in items:
                try:
                    # Get product details directly from database to avoid relationship issues
                    product = session.query(Product).filter(
                        Product.id == str(item.product_id)
                    ).first()
                    
                    name = "Unknown Product"
                    sku = "N/A"
                    
                    if product:
                        name = product.name
                        sku = product.sku
                    
                    result.append({
                        "product_id": str(item.product_id),
                        "name": name,
                        "sku": sku,
                        "quantity": item.quantity,
                        "price": item.price,
                        "total": item.price * item.quantity,
                        "product": {
                            "id": str(item.product_id),
                            "name": name,
                            "sku": sku
                        }
                    })
                except Exception as item_err:
                    logger.error(f"Error processing order item: {item_err}")
                    # Add a placeholder if we can't get the product
                    result.append({
                        "product_id": str(item.product_id),
                        "name": "Unknown Product",
                        "sku": "N/A",
                        "quantity": item.quantity,
                        "price": item.price,
                        "total": item.price * item.quantity,
                        "product": None
                    })
            return result
    except Exception as e:
        logger.error(f"Error getting items for order: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []

def get_order_items_count(order_id):
    """Get the count of items for an order using a fresh session."""
    try:
        from pycommerce.models.order import OrderItem
        
        with get_session() as session:
            count = session.query(OrderItem).filter(
                OrderItem.order_id == str(order_id)
            ).count()
            return count
    except Exception as e:
        logger.error(f"Error getting item count for order: {e}")
        return 0

# We'll no longer monkey patch the OrderNoteManager, instead we'll use our direct functions

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
        # Get items count using our session-safe function
        items_count = get_order_items_count(str(order.id))
            
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
    # Add detailed debug logging
    logger.info(f"Starting admin_order_detail for order_id: {order_id}")
    
    # Get tenant from session
    selected_tenant_slug = request.session.get("selected_tenant")
    logger.info(f"Selected tenant slug: {selected_tenant_slug}")
    
    # If no tenant is selected, redirect to dashboard with message
    if not selected_tenant_slug:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Please+select+a+store+first&status_type=warning", 
            status_code=303
        )
    
    # Get tenant object using tenant_manager
    try:
        tenant = tenant_manager.get_by_slug(selected_tenant_slug)
        logger.info(f"Retrieved tenant: {tenant.id if tenant else 'None'}")
        if not tenant:
            return RedirectResponse(
                url="/admin/dashboard?status_message=Store+not+found&status_type=error", 
                status_code=303
            )
    except Exception as tenant_err:
        logger.error(f"Error getting tenant: {str(tenant_err)}")
        return RedirectResponse(
            url="/admin/dashboard?status_message=Error+retrieving+store+info&status_type=error", 
            status_code=303
        )
    
    # Initialize necessary data with safe defaults
    notes_data = []
    items_data = []
    
    try:
        # Get order by ID
        logger.info(f"Getting order by ID: {order_id}")
        order = None
        try:
            # Try with order manager
            logger.info("Using order manager to get order")
            order = order_manager.get_by_id(order_id)
        except Exception as order_err:
            logger.error(f"Error with order_manager.get_by_id: {str(order_err)}")
            # Try direct database access as fallback
            try:
                with get_session() as session:
                    from pycommerce.models.order import Order
                    order = session.query(Order).filter(Order.id == str(order_id)).first()
            except Exception as db_err:
                logger.error(f"Error with direct order query: {str(db_err)}")
                
        # Check if we found an order
        if not order:
            logger.warning(f"Order {order_id} not found")
            return RedirectResponse(
                url=f"/admin/orders?status_message=Order+not+found&status_type=error", 
                status_code=303
            )
        
        # Verify order belongs to the selected tenant
        logger.info(f"Comparing order.tenant_id: {order.tenant_id} with tenant.id: {tenant.id}")
        if str(order.tenant_id) != str(tenant.id):
            logger.warning(f"Order {order_id} does not belong to tenant {tenant.id}")
            return RedirectResponse(
                url=f"/admin/orders?status_message=Order+not+found+for+this+store&status_type=error", 
                status_code=303
            )
        
        # Get order notes directly with the function - not through the manager
        logger.info(f"Getting notes for order: {order_id}")
        try:
            notes_data = get_notes_for_order(order_id)
            logger.info(f"Retrieved {len(notes_data) if notes_data else 0} notes")
        except Exception as notes_err:
            logger.error(f"Error getting notes: {str(notes_err)}")
            import traceback
            logger.error(f"Notes traceback: {traceback.format_exc()}")
            notes_data = []
        
        # Get order items directly with the function - not through the manager
        logger.info(f"Getting items for order: {order_id}")
        try:
            items_data = get_order_items(order_id)
            logger.info(f"Retrieved {len(items_data) if items_data else 0} items")
        except Exception as items_err:
            logger.error(f"Error getting items: {str(items_err)}")
            import traceback
            logger.error(f"Items traceback: {traceback.format_exc()}")
            items_data = []
        
        # Make sure notes_data and items_data are lists, not function references
        if not isinstance(notes_data, list):
            logger.warning(f"notes_data is not a list, it's {type(notes_data)}")
            notes_data = []
        
        if not isinstance(items_data, list):
            logger.warning(f"items_data is not a list, it's {type(items_data)}")
            items_data = []
        
        # Format order data for template with safe defaults
        logger.info("Preparing order data for template")
        order_data = {
            "id": str(order.id),
            "customer_name": getattr(order, 'customer_name', '') or '',
            "customer_email": getattr(order, 'customer_email', '') or '',
            "shipping_address": {
                "address_line1": getattr(order, 'shipping_address_line1', '') or '',
                "address_line2": getattr(order, 'shipping_address_line2', '') or '',
                "city": getattr(order, 'shipping_city', '') or '',
                "state": getattr(order, 'shipping_state', '') or '',
                "postal_code": getattr(order, 'shipping_postal_code', '') or '',
                "country": getattr(order, 'shipping_country', '') or ''
            },
            "subtotal": getattr(order, 'subtotal', 0.0),
            "tax": getattr(order, 'tax', 0.0),
            "shipping_cost": getattr(order, 'shipping_cost', 0.0),
            "total": getattr(order, 'total', 0.0),
            "status": getattr(order, 'status', '').value if hasattr(order, 'status') else 'PENDING',
            "payment_id": getattr(order, 'payment_transaction_id', None),
            "created_at": getattr(order, 'created_at', datetime.utcnow()),
            "notes": notes_data or []
        }
        
        # Get all possible order statuses for status dropdown
        status_options = [status.value for status in OrderStatus]
        
        logger.info("Rendering order detail template")
        return templates.TemplateResponse(
            "admin/order_detail.html",
            {
                "request": request,
                "order": order_data,
                "order_items": items_data,  # Pass items separately to avoid conflict with dictionary's items() method
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
        import traceback
        logger.error(f"Main traceback: {traceback.format_exc()}")
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
        
        # Get items using our session-safe function - make sure to capture the result properly
        try:
            items_data = get_order_items(order_id)
            if items_data is None:
                items_data = []
        except Exception as e:
            logger.error(f"Error getting items for fulfillment: {str(e)}")
            items_data = []
        
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
                "order_items": items_data,  # Pass items separately to avoid conflict with dictionary's items() method
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
        
        # Add note to order - first try to use the manager method
        try:
            success = order_note_manager.add_note(
                order_id=order_id,
                content=content,
                is_customer_note=is_customer_note
            )
        except Exception as note_err:
            logger.error(f"Error using order_note_manager: {note_err}")
            # Fallback to direct database operation if manager fails
            from uuid import uuid4
            from datetime import datetime
            
            success = False
            try:
                with get_session() as session:
                    new_note = OrderNote(
                        id=str(uuid4()),
                        order_id=order_id,
                        content=content,
                        is_customer_note=is_customer_note,
                        created_at=datetime.utcnow()
                    )
                    session.add(new_note)
                    session.commit()
                    success = True
            except Exception as db_err:
                logger.error(f"Error adding note directly to database: {db_err}")
                success = False
        
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
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
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