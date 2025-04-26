"""
Orders API endpoints for PyCommerce.

This module contains order-related API endpoints for creating, retrieving,
updating, and managing orders in the multi-tenant platform.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import logging
from datetime import datetime
from uuid import UUID

from managers import OrderManager, ProductManager, TenantManager
from pycommerce.models.order import OrderStatus, OrderType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router with tag
router = APIRouter(prefix="/orders", tags=["Orders"])

# Response models
class OrderItemBase(BaseModel):
    """Base model for order item data."""
    product_id: str
    quantity: int
    unit_price: float
    material_cost: Optional[float] = None
    labor_cost: Optional[float] = None
    
    class Config:
        schema_extra = {
            "example": {
                "product_id": "650e8400-e29b-41d4-a716-446655440000",
                "quantity": 2,
                "unit_price": 199.99,
                "material_cost": 120.00,
                "labor_cost": 25.00
            }
        }

class OrderItemResponse(OrderItemBase):
    """Model for order item responses with ID."""
    id: str
    product_name: Optional[str] = None
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "750e8400-e29b-41d4-a716-446655440000",
                "product_id": "650e8400-e29b-41d4-a716-446655440000",
                "product_name": "Premium Wireless Headphones",
                "quantity": 2,
                "unit_price": 199.99,
                "material_cost": 120.00,
                "labor_cost": 25.00
            }
        }

class CustomerInfo(BaseModel):
    """Model for customer information."""
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone": "555-123-4567",
                "address": "123 Main St",
                "city": "Springfield",
                "state": "IL",
                "postal_code": "62701",
                "country": "USA"
            }
        }

class OrderBase(BaseModel):
    """Base model for order data."""
    customer: CustomerInfo
    status: Optional[str] = "PENDING"
    order_type: Optional[str] = "STANDARD"
    shipping_method: Optional[str] = None
    shipping_cost: Optional[float] = 0.0
    tax_amount: Optional[float] = 0.0
    notes: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "customer": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                    "phone": "555-123-4567",
                    "address": "123 Main St",
                    "city": "Springfield",
                    "state": "IL",
                    "postal_code": "62701",
                    "country": "USA"
                },
                "status": "PENDING",
                "order_type": "STANDARD",
                "shipping_method": "standard",
                "shipping_cost": 9.99,
                "tax_amount": 23.99,
                "notes": "Please leave at the door"
            }
        }

class OrderCreate(OrderBase):
    """Model for creating a new order."""
    tenant_id: str
    items: List[OrderItemBase]
    
    class Config:
        schema_extra = {
            "example": {
                "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
                "customer": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                    "phone": "555-123-4567",
                    "address": "123 Main St",
                    "city": "Springfield",
                    "state": "IL",
                    "postal_code": "62701",
                    "country": "USA"
                },
                "status": "PENDING",
                "order_type": "STANDARD",
                "shipping_method": "standard",
                "shipping_cost": 9.99,
                "tax_amount": 23.99,
                "notes": "Please leave at the door",
                "items": [
                    {
                        "product_id": "650e8400-e29b-41d4-a716-446655440000",
                        "quantity": 2,
                        "unit_price": 199.99,
                        "material_cost": 120.00,
                        "labor_cost": 25.00
                    }
                ]
            }
        }

class OrderResponse(OrderBase):
    """Model for order responses with ID."""
    id: str
    tenant_id: str
    order_number: str
    items: List[OrderItemResponse]
    subtotal: float
    total: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "850e8400-e29b-41d4-a716-446655440000",
                "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
                "order_number": "ORD-12345",
                "customer": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                    "phone": "555-123-4567",
                    "address": "123 Main St",
                    "city": "Springfield",
                    "state": "IL",
                    "postal_code": "62701",
                    "country": "USA"
                },
                "status": "PENDING",
                "order_type": "STANDARD",
                "shipping_method": "standard",
                "shipping_cost": 9.99,
                "tax_amount": 23.99,
                "notes": "Please leave at the door",
                "items": [
                    {
                        "id": "750e8400-e29b-41d4-a716-446655440000",
                        "product_id": "650e8400-e29b-41d4-a716-446655440000",
                        "product_name": "Premium Wireless Headphones",
                        "quantity": 2,
                        "unit_price": 199.99,
                        "material_cost": 120.00,
                        "labor_cost": 25.00
                    }
                ],
                "subtotal": 399.98,
                "total": 433.96,
                "created_at": "2025-04-22T00:00:00Z",
                "updated_at": "2025-04-22T01:00:00Z"
            }
        }

class OrdersResponse(BaseModel):
    """Model for listing multiple orders."""
    orders: List[OrderResponse]
    tenant: str
    count: int
    filters: Dict[str, Any] = {}
    
    class Config:
        schema_extra = {
            "example": {
                "orders": [
                    {
                        "id": "850e8400-e29b-41d4-a716-446655440000",
                        "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
                        "order_number": "ORD-12345",
                        "customer": {
                            "first_name": "John",
                            "last_name": "Doe",
                            "email": "john.doe@example.com",
                            "phone": "555-123-4567",
                            "address": "123 Main St",
                            "city": "Springfield",
                            "state": "IL",
                            "postal_code": "62701",
                            "country": "USA"
                        },
                        "status": "PENDING",
                        "order_type": "STANDARD",
                        "shipping_method": "standard",
                        "shipping_cost": 9.99,
                        "tax_amount": 23.99,
                        "notes": "Please leave at the door",
                        "items": [
                            {
                                "id": "750e8400-e29b-41d4-a716-446655440000",
                                "product_id": "650e8400-e29b-41d4-a716-446655440000",
                                "product_name": "Premium Wireless Headphones",
                                "quantity": 2,
                                "unit_price": 199.99,
                                "material_cost": 120.00,
                                "labor_cost": 25.00
                            }
                        ],
                        "subtotal": 399.98,
                        "total": 433.96,
                        "created_at": "2025-04-22T00:00:00Z",
                        "updated_at": "2025-04-22T01:00:00Z"
                    }
                ],
                "tenant": "electronics",
                "count": 1,
                "filters": {"status": "PENDING"}
            }
        }

class OrderUpdate(BaseModel):
    """Model for updating an order."""
    status: Optional[str] = None
    shipping_method: Optional[str] = None
    shipping_cost: Optional[float] = None
    notes: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "status": "PROCESSING",
                "shipping_method": "express",
                "shipping_cost": 15.99,
                "notes": "Please leave at the door. Customer called to request express shipping."
            }
        }

class OrderNoteCreate(BaseModel):
    """Model for creating a new order note."""
    content: str
    
    class Config:
        schema_extra = {
            "example": {
                "content": "Customer called to inquire about delivery time."
            }
        }

class OrderNoteResponse(OrderNoteCreate):
    """Model for order note responses with ID."""
    id: str
    order_id: str
    created_at: datetime
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "950e8400-e29b-41d4-a716-446655440000",
                "order_id": "850e8400-e29b-41d4-a716-446655440000",
                "content": "Customer called to inquire about delivery time.",
                "created_at": "2025-04-22T02:00:00Z"
            }
        }

# API Routes
@router.get("/", 
         response_model=OrdersResponse, 
         summary="List Orders",
         description="Retrieve orders for a tenant with comprehensive filtering options",
         responses={
             200: {"description": "Orders retrieved successfully", "model": OrdersResponse},
             400: {"description": "Invalid request parameters"},
             401: {"description": "Unauthorized - requires proper authentication"},
             404: {"description": "Tenant not found"},
             500: {"description": "Internal server error"}
         })
async def list_orders(
    tenant: str = Query(..., description="Tenant slug identifier"),
    status: Optional[str] = Query(None, description="Filter by order status (PENDING, PROCESSING, SHIPPED, DELIVERED, COMPLETED)"),
    order_type: Optional[str] = Query(None, description="Filter by order type (STANDARD, RUSH, CUSTOM)"),
    start_date: Optional[str] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    customer_email: Optional[str] = Query(None, description="Filter by customer email address")
):
    """
    Retrieve orders for a tenant with comprehensive filtering options.
    
    This endpoint returns orders for a specific tenant with support for multiple filters.
    You can filter orders by status, type, date range, and customer email. The API returns 
    a paginated list of orders matching the criteria, along with count information
    and a summary of the applied filters.
    
    - **tenant**: Required tenant slug identifier (string)
    - **status**: Optional order status to filter by (PENDING, PROCESSING, SHIPPED, DELIVERED, COMPLETED)
    - **order_type**: Optional order type to filter by (STANDARD, RUSH, CUSTOM)
    - **start_date**: Optional date to filter orders created on or after (YYYY-MM-DD format)
    - **end_date**: Optional date to filter orders created on or before (YYYY-MM-DD format)
    - **customer_email**: Optional customer email to filter orders by
    
    Returns a structured response containing matching orders, tenant identifier, 
    total count, and applied filters. If the tenant does not exist, a 404 error is returned.
    """
    tenant_manager = TenantManager()
    order_manager = OrderManager()
    
    # Get tenant ID from slug
    tenant_obj = tenant_manager.get_tenant_by_slug(tenant)
    if not tenant_obj:
        raise HTTPException(
            status_code=404, detail=f"Tenant not found: {tenant}"
        )

    # Build filters
    filters = {}
    if status:
        filters["status"] = status
    if order_type:
        filters["order_type"] = order_type
    if start_date:
        filters["start_date"] = start_date
    if end_date:
        filters["end_date"] = end_date
    if customer_email:
        filters["customer_email"] = customer_email
    
    # Get orders with filters
    orders = order_manager.get_orders_by_tenant(tenant_obj.id, filters)
    
    # Format response
    response_orders = []
    for order in orders:
        items = order_manager.get_order_items(order.id)
        
        # Format items
        formatted_items = []
        for item in items:
            product_name = None
            try:
                product_manager = ProductManager()
                product = product_manager.get_product_by_id(item.product_id)
                if product:
                    product_name = product.name
            except Exception as e:
                logger.error(f"Error getting product name: {e}")
            
            formatted_items.append({
                "id": str(item.id),
                "product_id": str(item.product_id),
                "product_name": product_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "material_cost": item.material_cost,
                "labor_cost": item.labor_cost
            })
        
        # Calculate totals
        subtotal = sum(item.unit_price * item.quantity for item in items)
        total = subtotal + order.shipping_cost + order.tax_amount
        
        response_orders.append({
            "id": str(order.id),
            "tenant_id": str(order.tenant_id),
            "order_number": order.order_number,
            "customer": {
                "first_name": order.customer_first_name,
                "last_name": order.customer_last_name,
                "email": order.customer_email,
                "phone": order.customer_phone,
                "address": order.shipping_address,
                "city": order.shipping_city,
                "state": order.shipping_state,
                "postal_code": order.shipping_postal_code,
                "country": order.shipping_country
            },
            "status": order.status,
            "order_type": order.order_type,
            "shipping_method": order.shipping_method,
            "shipping_cost": order.shipping_cost,
            "tax_amount": order.tax_amount,
            "notes": order.notes,
            "items": formatted_items,
            "subtotal": subtotal,
            "total": total,
            "created_at": order.created_at,
            "updated_at": order.updated_at
        })
    
    return {
        "orders": response_orders,
        "tenant": tenant,
        "count": len(orders),
        "filters": filters
    }

@router.get("/{order_id}", 
         response_model=OrderResponse, 
         summary="Get Order by ID",
         description="Retrieve detailed information about a specific order by its unique ID",
         responses={
             200: {"description": "Order retrieved successfully", "model": OrderResponse},
             400: {"description": "Invalid order ID format"},
             401: {"description": "Unauthorized - requires proper authentication"},
             404: {"description": "Order not found"},
             500: {"description": "Internal server error"}
         })
async def get_order(
    order_id: str = Path(..., description="The unique UUID of the order to retrieve")
):
    """
    Retrieve detailed information about a specific order by its unique ID.
    
    This endpoint returns comprehensive details about a specific order, including its items,
    customer information, shipping details, costs, and current status. The order ID should 
    be provided as a UUID string.
    
    - **order_id**: The unique identifier of the order (UUID format)
    
    Returns the order details if found, including all line items, pricing information,
    shipping details, and customer information. If the order does not exist, a 404 error is returned.
    """
    order_manager = OrderManager()
    order = order_manager.get_order_by_id(order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail=f"Order with id {order_id} not found")
    
    # Get order items
    items = order_manager.get_order_items(order.id)
    
    # Format items
    formatted_items = []
    for item in items:
        product_name = None
        try:
            product_manager = ProductManager()
            product = product_manager.get_product_by_id(item.product_id)
            if product:
                product_name = product.name
        except Exception as e:
            logger.error(f"Error getting product name: {e}")
        
        formatted_items.append({
            "id": str(item.id),
            "product_id": str(item.product_id),
            "product_name": product_name,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "material_cost": item.material_cost,
            "labor_cost": item.labor_cost
        })
    
    # Calculate totals
    subtotal = sum(item.unit_price * item.quantity for item in items)
    total = subtotal + order.shipping_cost + order.tax_amount
    
    return {
        "id": str(order.id),
        "tenant_id": str(order.tenant_id),
        "order_number": order.order_number,
        "customer": {
            "first_name": order.customer_first_name,
            "last_name": order.customer_last_name,
            "email": order.customer_email,
            "phone": order.customer_phone,
            "address": order.shipping_address,
            "city": order.shipping_city,
            "state": order.shipping_state,
            "postal_code": order.shipping_postal_code,
            "country": order.shipping_country
        },
        "status": order.status,
        "order_type": order.order_type,
        "shipping_method": order.shipping_method,
        "shipping_cost": order.shipping_cost,
        "tax_amount": order.tax_amount,
        "notes": order.notes,
        "items": formatted_items,
        "subtotal": subtotal,
        "total": total,
        "created_at": order.created_at,
        "updated_at": order.updated_at
    }

@router.post("/", 
         response_model=OrderResponse, 
         summary="Create Order",
         description="Create a new order in the system with complete customer and product details",
         responses={
             201: {"description": "Order created successfully", "model": OrderResponse},
             400: {"description": "Invalid request format or product not found"},
             401: {"description": "Unauthorized - requires proper authentication"},
             404: {"description": "Tenant not found"},
             422: {"description": "Validation error - invalid data format"},
             500: {"description": "Internal server error"}
         },
         status_code=201)
async def create_order(
    order: OrderCreate = Body(..., description="The complete order details including customer information and line items")
):
    """
    Create a new order in the system with complete customer and product details.
    
    This endpoint creates a new order with the provided details, including customer information,
    shipping preferences, and product line items. Each order must be associated with a valid
    tenant and contain valid product references. The system will automatically generate an
    order number and calculate relevant totals.
    
    - **order**: Complete order details including:
      - **tenant_id**: ID of the tenant this order belongs to (required)
      - **customer**: Customer information including name, contact details, and shipping address (required)
      - **items**: List of order line items with product references, quantities, and prices (required)
      - **status**: Order status (default: PENDING)
      - **order_type**: Type of order (default: STANDARD)
      - **shipping_method**: Selected shipping method (optional)
      - **shipping_cost**: Cost of shipping (default: 0.0)
      - **tax_amount**: Tax applied to the order (default: 0.0)
      - **notes**: Additional order notes or instructions (optional)
    
    Returns the created order with full details including order ID, order number, and calculated totals.
    Returns a 400 error if any referenced product does not exist.
    Returns a 404 error if the specified tenant does not exist.
    """
    tenant_manager = TenantManager()
    order_manager = OrderManager()
    product_manager = ProductManager()
    
    # Check if tenant exists
    tenant = tenant_manager.get_tenant_by_id(order.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant with id {order.tenant_id} not found")
    
    # Check if all products exist
    for item in order.items:
        product = product_manager.get_product_by_id(item.product_id)
        if not product:
            raise HTTPException(status_code=400, detail=f"Product with id {item.product_id} not found")
    
    # Create order
    try:
        # Prepare customer data
        customer_data = {
            "customer_first_name": order.customer.first_name,
            "customer_last_name": order.customer.last_name,
            "customer_email": order.customer.email,
            "customer_phone": order.customer.phone,
            "shipping_address": order.customer.address,
            "shipping_city": order.customer.city,
            "shipping_state": order.customer.state,
            "shipping_postal_code": order.customer.postal_code,
            "shipping_country": order.customer.country
        }
        
        # Create order
        new_order = order_manager.create_order(
            tenant_id=order.tenant_id,
            status=OrderStatus(order.status) if order.status else OrderStatus.PENDING,
            order_type=OrderType(order.order_type) if order.order_type else OrderType.STANDARD,
            shipping_method=order.shipping_method,
            shipping_cost=order.shipping_cost or 0.0,
            tax_amount=order.tax_amount or 0.0,
            notes=order.notes,
            **customer_data
        )
        
        # Add order items
        for item in order.items:
            order_manager.add_order_item(
                order_id=new_order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                material_cost=item.material_cost,
                labor_cost=item.labor_cost
            )
        
        # Return created order
        return await get_order(str(new_order.id))
    
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")

@router.put("/{order_id}", 
         response_model=OrderResponse, 
         summary="Update Order",
         description="Update an existing order's information",
         responses={
             200: {"description": "Order updated successfully", "model": OrderResponse},
             400: {"description": "Invalid order ID format or request body"},
             401: {"description": "Unauthorized - requires proper authentication"},
             404: {"description": "Order not found"},
             422: {"description": "Validation error - invalid data format"},
             500: {"description": "Internal server error"}
         })
async def update_order(
    order_id: str = Path(..., description="The unique UUID of the order to update"),
    order_update: OrderUpdate = Body(..., description="The order fields to update (partial updates supported)")
):
    """
    Update an existing order's information.
    
    This endpoint allows for partial updates to order information. Only the fields
    provided in the request body will be updated; other fields will remain unchanged.
    This is useful for updating order status, shipping details, or adding notes as the
    order progresses through fulfillment.
    
    - **order_id**: The unique identifier of the order to update (UUID format)
    - **order_update**: The fields to update, which can include:
      - **status**: New order status (e.g., PENDING, PROCESSING, SHIPPED, DELIVERED)
      - **shipping_method**: New shipping method (e.g., express, standard)
      - **shipping_cost**: Updated shipping cost
      - **notes**: Additional notes or instructions for the order
    
    Returns the complete updated order with all fields.
    Returns a 404 error if no order exists with the provided ID.
    """
    order_manager = OrderManager()
    
    # Check if order exists
    existing = order_manager.get_order_by_id(order_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Order with id {order_id} not found")
    
    # Prepare update data
    update_data = {}
    if order_update.status is not None:
        update_data["status"] = OrderStatus(order_update.status)
    if order_update.shipping_method is not None:
        update_data["shipping_method"] = order_update.shipping_method
    if order_update.shipping_cost is not None:
        update_data["shipping_cost"] = order_update.shipping_cost
    if order_update.notes is not None:
        update_data["notes"] = order_update.notes
    
    # Update order
    order_manager.update_order(order_id, update_data)
    
    # Return updated order
    return await get_order(order_id)

@router.post("/{order_id}/notes", 
         response_model=OrderNoteResponse, 
         summary="Add Order Note",
         description="Add a note to an existing order for tracking important information",
         responses={
             201: {"description": "Note added successfully", "model": OrderNoteResponse},
             400: {"description": "Invalid order ID format"},
             401: {"description": "Unauthorized - requires proper authentication"},
             404: {"description": "Order not found"},
             422: {"description": "Validation error - invalid note format"},
             500: {"description": "Internal server error"}
         },
         status_code=201)
async def add_order_note(
    order_id: str = Path(..., description="The unique UUID of the order to add a note to"),
    note: OrderNoteCreate = Body(..., description="The note content to add to the order")
):
    """
    Add a note to an existing order for tracking important information.
    
    This endpoint allows adding notes to an order for tracking customer communications,
    special requests, fulfillment details, or other important information. Notes are
    stored with timestamps for audit and reference purposes, and can be retrieved
    separately from the main order data.
    
    - **order_id**: The unique identifier of the order to add a note to (UUID format)
    - **note**: The note details:
      - **content**: The text content of the note (required)
    
    Returns the created note with its ID and creation timestamp.
    Returns a 404 error if no order exists with the provided ID.
    """
    order_manager = OrderManager()
    
    # Check if order exists
    existing = order_manager.get_order_by_id(order_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Order with id {order_id} not found")
    
    # Add note
    new_note = order_manager.add_order_note(order_id, note.content)
    
    return {
        "id": str(new_note.id),
        "order_id": str(new_note.order_id),
        "content": new_note.content,
        "created_at": new_note.created_at
    }

@router.get("/{order_id}/notes", 
         response_model=List[OrderNoteResponse], 
         summary="Get Order Notes",
         description="Retrieve all notes associated with a specific order",
         responses={
             200: {"description": "Notes retrieved successfully", "model": List[OrderNoteResponse]},
             400: {"description": "Invalid order ID format"},
             401: {"description": "Unauthorized - requires proper authentication"},
             404: {"description": "Order not found"},
             500: {"description": "Internal server error"}
         })
async def get_order_notes(
    order_id: str = Path(..., description="The unique UUID of the order to get notes for")
):
    """
    Retrieve all notes associated with a specific order.
    
    This endpoint returns all notes that have been added to an order, sorted by creation
    date from newest to oldest. Order notes are used for tracking customer communications,
    fulfillment details, internal comments, and other important information related to
    the order processing workflow.
    
    - **order_id**: The unique identifier of the order (UUID format)
    
    Returns a list of all notes associated with the order, each including its content
    and creation timestamp. Returns an empty list if the order exists but has no notes.
    Returns a 404 error if no order exists with the provided ID.
    """
    order_manager = OrderManager()
    
    # Check if order exists
    existing = order_manager.get_order_by_id(order_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Order with id {order_id} not found")
    
    # Get notes
    notes = order_manager.get_order_notes(order_id)
    
    return [
        {
            "id": str(note.id),
            "order_id": str(note.order_id),
            "content": note.content,
            "created_at": note.created_at
        }
        for note in notes
    ]