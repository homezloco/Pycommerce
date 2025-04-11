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
                    from pycommerce.models.db_registry import Product
                    # Import the correct SQLAlchemy Product model from db_registry

                    # Build a correct SQLAlchemy query
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
                        "product_name": name,  # Add this field to match template expectation
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
                        "product_name": "Unknown Product",  # Add this field to match template expectation
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

    if selected_tenant_slug.lower() == "all":
        # Get orders for all stores
        from routes.admin.tenant_utils import get_orders_for_all_tenants
        logger.info("Getting orders for all stores")
        
        orders = get_orders_for_all_tenants(
            tenant_manager=tenant_manager,
            order_manager=order_manager,
            logger=logger,
            filters=filters
        )
    else:
        # Get orders for specific tenant
        logger.info(f"Getting orders for tenant: {tenant.name}")
        orders = order_manager.get_for_tenant(
            tenant.id,
            filters=filters if filters else None
        )

    # Serialize orders for template
    orders_data = []
    for order in orders:
        # Get items count using our session-safe function
        items_count = get_order_items_count(str(order.id))

        # Try to extract both customer_name and customer_email safely
        customer_name = ""
        customer_email = ""
        status_value = ""

        # Safe extraction with error handling for better stability
        try:
            customer_name = order.customer_name if order.customer_name else ""
        except:
            pass

        try:
            customer_email = order.customer_email if order.customer_email else ""
        except:
            pass

        # Handle status whether it's an enum value, string, or int
        try:
            if hasattr(order.status, 'value'):
                # It's an enum
                status_value = order.status.value
            elif isinstance(order.status, int):
                # It's already an int
                status_value = order.status
            else:
                # It's a string or something else
                status_value = order.status
        except:
            # Default to a safe value if all fails
            status_value = 1  # PENDING

        orders_data.append({
            "id": str(order.id),
            "customer_name": customer_name,
            "customer_email": customer_email,
            "total": order.total,
            "status": status_value,
            "items_count": items_count,
            "created_at": order.created_at
        })

    # Get all possible order statuses for filter dropdown
    status_options = ["PENDING", "PROCESSING", "PAID", "SHIPPED", "DELIVERED", "COMPLETED", "CANCELLED", "REFUNDED"]

    # Get all tenants for the store selector
    tenants = tenant_manager.list()
    
    return templates.TemplateResponse(
        "admin/orders.html",
        {
            "request": request,
            "orders": orders_data,
            "selected_tenant": selected_tenant_slug,
            "tenant": tenant,
            "tenants": tenants,  # Pass all tenants for the dropdown
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

        # Convert the status to a readable string
        status_value = "pending"
        if hasattr(order, 'status'):
            try:
                # Get the enum value as a string
                if hasattr(order.status, 'value'):
                    status_value = order.status.value.lower()
                elif hasattr(order.status, 'name'):
                    status_value = order.status.name.lower()
                elif isinstance(order.status, int):
                    # If it's an integer, convert to string
                    # OrderStatus is already imported at the module level
                    status_values = {
                        1: "pending",
                        2: "processing",
                        3: "paid",
                        4: "shipped",
                        5: "delivered",
                        6: "completed",
                        7: "cancelled",
                        8: "refunded"
                    }
                    status_value = status_values.get(order.status, "pending")
                else:
                    # If it's already a string
                    status_value = str(order.status).lower()
            except Exception as status_err:
                logger.error(f"Error getting status: {status_err}")
                status_value = "pending"

        logger.info(f"Order status for template: {status_value}")

        order_data = {
            "id": str(order.id),
            "order_number": getattr(order, 'order_number', '') or '',
            # Customer information
            "customer_name": getattr(order, 'customer_name', '') or '',
            "customer_email": getattr(order, 'customer_email', '') or '',
            "customer_phone": getattr(order, 'customer_phone', '') or '',
            # Shipping address
            "shipping_address": {
                "address_line1": getattr(order, 'shipping_address_line1', '') or '',
                "address_line2": getattr(order, 'shipping_address_line2', '') or '',
                "city": getattr(order, 'shipping_city', '') or '',
                "state": getattr(order, 'shipping_state', '') or '',
                "postal_code": getattr(order, 'shipping_postal_code', '') or '',
                "country": getattr(order, 'shipping_country', '') or ''
            },
            # Billing address
            "billing_address": {
                "address_line1": getattr(order, 'billing_address_line1', '') or '',
                "address_line2": getattr(order, 'billing_address_line2', '') or '',
                "city": getattr(order, 'billing_city', '') or '',
                "state": getattr(order, 'billing_state', '') or '',
                "postal_code": getattr(order, 'billing_postal_code', '') or '',
                "country": getattr(order, 'billing_country', '') or ''
            },
            # Order financial details
            "subtotal": getattr(order, 'subtotal', 0.0),
            "tax": getattr(order, 'tax', 0.0),
            "shipping_cost": getattr(order, 'shipping_cost', 0.0),
            "discount": getattr(order, 'discount', 0.0),
            "total": getattr(order, 'total', 0.0),
            # Order status, type, and payment
            "status": status_value,  # Normalized status string
            "order_type": _get_order_type_string(order),  # Get order type as string
            "payment_method": getattr(order, 'payment_method', '') or '',
            "payment_id": getattr(order, 'payment_transaction_id', '') or '',
            "is_paid": getattr(order, 'is_paid', False),
            "paid_at": getattr(order, 'paid_at', None),
            # Shipping information
            "tracking_number": getattr(order, 'tracking_number', '') or '',
            "shipping_carrier": getattr(order, 'shipping_carrier', '') or '',
            "shipped_at": getattr(order, 'shipped_at', None),
            "delivered_at": getattr(order, 'delivered_at', None),
            # Timestamps and notes
            "created_at": getattr(order, 'created_at', datetime.utcnow()),
            "updated_at": getattr(order, 'updated_at', datetime.utcnow()),
            "notes": notes_data or []
        }

        # Get all possible order statuses for status dropdown as string values
        status_options = ["PENDING", "PROCESSING", "PAID", "SHIPPED", "DELIVERED", "COMPLETED", "CANCELLED", "REFUNDED"]

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
        # Validate status - now we're using string values, so validate against allowed values
        allowed_statuses = ["PENDING", "PROCESSING", "PAID", "SHIPPED", "DELIVERED", "COMPLETED", "CANCELLED", "REFUNDED"]
        if status.upper() not in allowed_statuses:
            return RedirectResponse(
                url=f"/admin/orders/{order_id}?status_message=Invalid+order+status&status_type=error", 
                status_code=303
            )

        # Use the string value directly
        order_status = status.upper()

        # Get the current tenant for store information
        selected_tenant_slug = request.session.get("selected_tenant")
        tenant = tenant_manager.get_by_slug(selected_tenant_slug)
        if not tenant:
            logger.warning(f"No tenant selected when updating order status")

        # Get the order before status update to check previous status
        order = order_manager.get_by_id(order_id)
        if not order:
            return RedirectResponse(
                url=f"/admin/orders?status_message=Order+not+found&status_type=error", 
                status_code=303
            )

        previous_status = order.status

        # Update order status
        success = order_manager.update_status(order_id, order_status)
        if success:
            # If status changed to SHIPPED, send shipping notification email
            if order_status == "SHIPPED" and previous_status != "SHIPPED":
                logger.info(f"Order status changed to SHIPPED, sending shipping notification email")
                try:
                    # Get updated order after status change
                    updated_order = order_manager.get_by_id(order_id)

                    # Import needed services
                    from pycommerce.services.mail_service import get_email_service, init_email_service, EmailConfig
                    from pycommerce.models.shipment import ShipmentManager, Shipment

                    # Get shipment manager and find or create shipment
                    shipment_manager = ShipmentManager()
                    shipments = shipment_manager.get_shipments_for_order(order_id)

                    # Use first shipment or create a new one if none exists
                    if shipments and len(shipments) > 0:
                        shipment = shipments[0]
                        logger.info(f"Using existing shipment {shipment.id}")
                    else:
                        # Create a new shipment with basic information
                        try:
                            shipping_method = "Standard Shipping"
                            if hasattr(updated_order, 'shipping_method') and updated_order.shipping_method:
                                shipping_method = updated_order.shipping_method

                            # Create shipment
                            shipment = shipment_manager.create_shipment(
                                order_id=order_id,
                                shipping_method=shipping_method,
                                tracking_number=getattr(updated_order, 'tracking_number', None),
                                carrier=getattr(updated_order, 'shipping_carrier', "Default Carrier")
                            )
                            logger.info(f"Created new shipment {shipment.id}")

                            # Add order items to shipment
                            order_items = get_order_items(order_id) 
                            for item in order_items:
                                shipment_manager.add_items_to_shipment(
                                    shipment_id=shipment.id,
                                    items=[{
                                        "order_item_id": str(item.get("id", item.get("order_item_id"))),
                                        "product_id": str(item.get("product_id")),
                                        "quantity": item.get("quantity", 1)
                                    }]
                                )
                        except Exception as ship_err:
                            logger.error(f"Error creating shipment: {str(ship_err)}")
                            # Continue even if shipment creation fails, use a mock shipment for the email
                            shipment = Shipment(
                                id="default",
                                order_id=order_id,
                                shipping_method="Standard Shipping",
                                carrier=getattr(updated_order, 'shipping_carrier', "Default Carrier"),
                                tracking_number=getattr(updated_order, 'tracking_number', "Not available")
                            )

                    # Initialize email service
                    email_service = get_email_service()
                    if not email_service:
                        email_service = init_email_service()

                    # Default to test mode if SMTP is not configured
                    if not email_service.config.enabled:
                        email_service.enable_test_mode()
                        logger.warning("Email service in test mode, emails will not be sent")

                    # Get customer email
                    customer_email = getattr(updated_order, 'customer_email', None)
                    if not customer_email:
                        logger.warning(f"No customer email available for order {order_id}")
                        return RedirectResponse(
                            url=f"/admin/orders/{order_id}?status_message=Order+status+updated+but+no+customer+email+available+for+notification&status_type=warning", 
                            status_code=303
                        )

                    # Get store information
                    store_name = tenant.name if tenant else "Our Store"
                    store_url = tenant.domain if tenant and tenant.domain else f"https://{request.headers.get('host')}"

                    # Send shipping notification email
                    email_sent = email_service.send_shipping_notification(
                        order=updated_order,
                        shipment=shipment,
                        to_email=customer_email,
                        store_name=store_name,
                        store_url=store_url,
                        contact_email=None  # Use default from config
                    )

                    if email_sent:
                        logger.info(f"Shipping notification email sent to {customer_email}")
                        return RedirectResponse(
                            url=f"/admin/orders/{order_id}?status_message=Order+status+updated+and+shipping+notification+email+sent&status_type=success", 
                            status_code=303
                        )
                    else:
                        logger.warning(f"Failed to send shipping notification email")
                        return RedirectResponse(
                            url=f"/admin/orders/{order_id}?status_message=Order+status+updated+but+shipping+notification+email+failed&status_type=warning", 
                            status_code=303
                        )

                except Exception as email_err:
                    logger.error(f"Error sending shipping notification: {str(email_err)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return RedirectResponse(
                        url=f"/admin/orders/{order_id}?status_message=Order+status+updated+but+shipping+email+failed:+{str(email_err)}&status_type=warning", 
                        status_code=303
                    )

            # Default success response
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
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
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
        # Convert the status to a readable string
        status_value = "pending"
        if hasattr(order, 'status'):
            try:
                # Get the enum value as a string
                if hasattr(order.status, 'value'):
                    status_value = order.status.value.lower()
                elif hasattr(order.status, 'name'):
                    status_value = order.status.name.lower()
                elif isinstance(order.status, int):
                    # If it's an integer, convert to string
                    # OrderStatus is already imported at the module level
                    status_values = {
                        1: "pending",
                        2: "processing",
                        3: "paid",
                        4: "shipped",
                        5: "delivered",
                        6: "completed",
                        7: "cancelled",
                        8: "refunded"
                    }
                    status_value = status_values.get(order.status, "pending")
                else:
                    # If it's already a string
                    status_value = str(order.status).lower()
            except Exception as status_err:
                logger.error(f"Error getting status: {status_err}")
                status_value = "pending"

        logger.info(f"Fulfillment - Order status for template: {status_value}")

        order_data = {
            "id": str(order.id),
            "order_number": getattr(order, 'order_number', '') or '',
            # Customer information
            "customer_name": getattr(order, 'customer_name', '') or '',
            "customer_email": getattr(order, 'customer_email', '') or '',
            "customer_phone": getattr(order, 'customer_phone', '') or '',
            # Shipping address
            "shipping_address": {
                "address_line1": getattr(order, 'shipping_address_line1', '') or '',
                "address_line2": getattr(order, 'shipping_address_line2', '') or '',
                "city": getattr(order, 'shipping_city', '') or '',
                "state": getattr(order, 'shipping_state', '') or '',
                "postal_code": getattr(order, 'shipping_postal_code', '') or '',
                "country": getattr(order, 'shipping_country', '') or ''
            },
            # Billing address
            "billing_address": {
                "address_line1": getattr(order, 'billing_address_line1', '') or '',
                "address_line2": getattr(order, 'billing_address_line2', '') or '',
                "city": getattr(order, 'billing_city', '') or '',
                "state": getattr(order, 'billing_state', '') or '',
                "postal_code": getattr(order, 'billing_postal_code', '') or '',
                "country": getattr(order, 'billing_country', '') or ''
            },
            # Order financial details
            "subtotal": getattr(order, 'subtotal', 0.0),
            "tax": getattr(order, 'tax', 0.0),
            "shipping_cost": getattr(order, 'shipping_cost', 0.0),
            "discount": getattr(order, 'discount', 0.0),
            "total": getattr(order, 'total', 0.0),
            # Order status, type, and payment
            "status": status_value,
            "order_type": _get_order_type_string(order),  # Get order type as string
            "payment_method": getattr(order, 'payment_method', '') or '',
            "payment_id": getattr(order, 'payment_transaction_id', '') or '',
            "is_paid": getattr(order, 'is_paid', False),
            "paid_at": getattr(order, 'paid_at', None),
            # Shipping information
            "tracking_number": getattr(order, 'tracking_number', '') or '',
            "shipping_carrier": getattr(order, 'shipping_carrier', '') or '',
            "shipped_at": getattr(order, 'shipped_at', None),
            "delivered_at": getattr(order, 'delivered_at', None),
            # Items and timestamps
            "items": items_data,
            "created_at": getattr(order, 'created_at', datetime.utcnow()),
            "updated_at": getattr(order, 'updated_at', datetime.utcnow())
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

def _get_order_type_string(order):
    """
    Get the order type as a string.

    Args:
        order: The order object

    Returns:
        The order type as a string (TEST, STANDARD, etc.)
    """
    try:
        if hasattr(order, 'order_type'):
            order_type = order.order_type
            # If it's an enum, get the name
            if hasattr(order_type, 'name'):
                return order_type.name
            # If it's an integer, map to a name
            elif isinstance(order_type, int):
                order_type_values = {
                    1: "STANDARD",
                    2: "TEST",
                    3: "SUBSCRIPTION",
                    4: "WHOLESALE",
                    5: "BACKORDER",
                    6: "PREORDER",
                    7: "GIFT",
                    8: "EXPEDITED",
                    9: "INTERNATIONAL"
                }
                return order_type_values.get(order_type, "STANDARD")
            # Otherwise, convert to string
            return str(order_type).upper()
    except Exception as e:
        logger.error(f"Error getting order type: {e}")

    # Default to STANDARD if anything goes wrong
    return "STANDARD"

def setup_routes(app_templates):
    """
    Set up routes with the given templates.

    Args:
        app_templates: Jinja2Templates instance from the main app
    """
    global templates
    templates = app_templates
    return router