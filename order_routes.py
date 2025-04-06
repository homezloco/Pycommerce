"""
Order-related routes for the admin interface.

This module defines route handlers for order management, including
listing all orders, viewing order details, and handling order fulfillment.
"""

import os
import logging
import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, session

from app import db
from models import Tenant, Order, OrderItem, Product, Shipment, ShipmentItem
from managers import OrderManager, ShipmentManager, InventoryManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Blueprint for order routes
order_routes = Blueprint('order_routes', __name__)

@order_routes.route('/admin/orders')
def admin_orders_list():
    """List all orders in the admin interface."""
    # Get the tenant from the session
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        flash('Please select a tenant first', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # Get all orders for the tenant
    orders = Order.query.filter_by(tenant_id=tenant_id).order_by(Order.created_at.desc()).all()
    
    return render_template(
        'admin/orders.html', 
        orders=orders, 
        title='Orders',
        active_nav='orders'
    )

@order_routes.route('/admin/orders/<order_id>')
def admin_order_detail(order_id):
    """View order details in the admin interface."""
    # Get the tenant from the session
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        flash('Please select a tenant first', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # Get the order
    order = Order.query.filter_by(id=order_id, tenant_id=tenant_id).first_or_404()
    
    # Get order items with products
    items = OrderItem.query.filter_by(order_id=order_id).all()
    for item in items:
        item.product = Product.query.filter_by(id=item.product_id).first()
    
    order.items = items
    
    return render_template(
        'admin/order_detail.html',
        order=order,
        title=f'Order #{order_id}',
        active_nav='orders'
    )

@order_routes.route('/admin/orders/<order_id>/update', methods=['POST'])
def admin_order_update(order_id):
    """Update an order's status or details."""
    # Get the tenant from the session
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        flash('Please select a tenant first', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # Get the order
    order = Order.query.filter_by(id=order_id, tenant_id=tenant_id).first_or_404()
    
    # Update the order
    order_manager = OrderManager()
    status = request.form.get('status')
    
    try:
        order_manager.update_order(order_id, status=status)
        flash(f'Order status updated to {status}', 'success')
    except Exception as e:
        logger.error(f"Error updating order: {e}")
        flash(f'Error updating order: {e}', 'danger')
    
    return redirect(url_for('order_routes.admin_order_detail', order_id=order_id))

@order_routes.route('/admin/orders/<order_id>/notes', methods=['POST'])
def admin_order_add_note(order_id):
    """Add a note to an order."""
    # Get the tenant from the session
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        flash('Please select a tenant first', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # Get the order
    order = Order.query.filter_by(id=order_id, tenant_id=tenant_id).first_or_404()
    
    # Get note details
    content = request.form.get('content')
    is_customer_visible = 'is_customer_visible' in request.form
    author = "Admin"  # In a real app, this would be the logged-in user
    
    try:
        # Create the order note
        from models import OrderNote
        note = OrderNote(
            id=str(uuid.uuid4()),
            order_id=order_id,
            content=content,
            author=author,
            is_customer_visible=is_customer_visible,
            created_at=datetime.utcnow()
        )
        db.session.add(note)
        db.session.commit()
        
        flash('Note added successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding note: {e}")
        flash(f'Error adding note: {e}', 'danger')
    
    return redirect(url_for('order_routes.admin_order_detail', order_id=order_id))

@order_routes.route('/admin/orders/<order_id>/fulfillment')
def admin_order_fulfillment(order_id):
    """View order fulfillment page."""
    # Get the tenant from the session
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        flash('Please select a tenant first', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # Get the order
    order = Order.query.filter_by(id=order_id, tenant_id=tenant_id).first_or_404()
    
    # Get order items with products
    items = OrderItem.query.filter_by(order_id=order_id).all()
    for item in items:
        item.product = Product.query.filter_by(id=item.product_id).first()
    
    order.items = items
    
    # Get shipments for this order
    shipments = Shipment.query.filter_by(order_id=order_id).all()
    
    return render_template(
        'admin/order_fulfillment.html',
        order=order,
        shipments=shipments,
        title=f'Order Fulfillment - #{order_id}',
        active_nav='orders'
    )

@order_routes.route('/admin/orders/<order_id>/shipments/create', methods=['POST'])
def admin_create_shipment(order_id):
    """Create a new shipment for an order."""
    # Get the tenant from the session
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        flash('Please select a tenant first', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # Get the order
    order = Order.query.filter_by(id=order_id, tenant_id=tenant_id).first_or_404()
    
    # Create the shipment
    shipment_manager = ShipmentManager()
    inventory_manager = InventoryManager()
    
    shipping_method = request.form.get('shipping_method')
    carrier = request.form.get('carrier')
    tracking_number = request.form.get('tracking_number')
    tracking_url = request.form.get('tracking_url')
    
    try:
        # Create the shipment
        shipment = shipment_manager.create_shipment(
            order_id=order_id,
            shipping_method=shipping_method,
            carrier=carrier,
            tracking_number=tracking_number,
            tracking_url=tracking_url,
            shipping_address=order.shipping_address
        )
        
        # Get the items to include in the shipment
        item_ids = request.form.getlist('item_ids[]')
        for item_id in item_ids:
            product_id = request.form.get(f'product_ids[{item_id}]')
            quantity = int(request.form.get(f'quantities[{item_id}]', 1))
            
            # Add item to shipment
            shipment_manager.add_item_to_shipment(
                shipment_id=shipment.id,
                order_item_id=item_id,
                product_id=product_id,
                quantity=quantity
            )
            
            # Mark inventory as sold (convert from reserved to sold)
            inventory_manager.complete_inventory_sale(
                product_id=product_id,
                quantity=quantity,
                reference_id=order_id,
                reference_type="order"
            )
        
        flash('Shipment created successfully', 'success')
    except Exception as e:
        logger.error(f"Error creating shipment: {e}")
        flash(f'Error creating shipment: {e}', 'danger')
    
    return redirect(url_for('order_routes.admin_order_fulfillment', order_id=order_id))

@order_routes.route('/admin/orders/<order_id>/shipments/<shipment_id>/update', methods=['POST'])
def admin_update_shipment(order_id, shipment_id):
    """Update a shipment's status."""
    # Get the tenant from the session
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        flash('Please select a tenant first', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # Update the shipment
    shipment_manager = ShipmentManager()
    status = request.form.get('status')
    tracking_number = request.form.get('tracking_number')
    tracking_url = request.form.get('tracking_url')
    
    try:
        shipment = shipment_manager.update_shipment_status(
            shipment_id=shipment_id,
            status=status,
            tracking_number=tracking_number,
            tracking_url=tracking_url
        )
        flash(f'Shipment status updated to {status}', 'success')
    except Exception as e:
        logger.error(f"Error updating shipment: {e}")
        flash(f'Error updating shipment: {e}', 'danger')
    
    return redirect(url_for('order_routes.admin_order_fulfillment', order_id=order_id))

@order_routes.route('/admin/inventory')
def admin_inventory_list():
    """List all inventory in the admin interface."""
    # Get the tenant from the session
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        flash('Please select a tenant first', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # Get all inventory records for this tenant
    from models import InventoryRecord
    inventory_records = db.session.query(
        InventoryRecord, Product
    ).join(
        Product, InventoryRecord.product_id == Product.id
    ).filter(
        InventoryRecord.tenant_id == tenant_id
    ).all()
    
    # Format for display
    inventory_items = []
    for record, product in inventory_records:
        inventory_items.append({
            'id': record.id,
            'product_id': product.id,
            'product_name': product.name,
            'sku': record.sku or product.sku,
            'quantity': record.quantity,
            'available': record.available_quantity,
            'reserved': record.reserved_quantity,
            'reorder_point': record.reorder_point,
            'location': record.location
        })
    
    # Get low stock items
    inventory_manager = InventoryManager()
    low_stock_items = inventory_manager.get_low_stock_items(tenant_id)
    
    return render_template(
        'admin/inventory.html',
        inventory_items=inventory_items,
        low_stock_items=low_stock_items,
        title='Inventory Management',
        active_nav='inventory'
    )

@order_routes.route('/admin/inventory/<product_id>', methods=['GET', 'POST'])
def admin_inventory_detail(product_id):
    """View and update inventory for a product."""
    # Get the tenant from the session
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        flash('Please select a tenant first', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    # Get the product
    product = Product.query.filter_by(id=product_id, tenant_id=tenant_id).first_or_404()
    
    if request.method == 'POST':
        # Update inventory
        inventory_manager = InventoryManager()
        quantity = int(request.form.get('quantity', 0))
        location = request.form.get('location')
        sku = request.form.get('sku')
        reorder_point = int(request.form.get('reorder_point', 0))
        reorder_quantity = int(request.form.get('reorder_quantity', 0))
        
        try:
            inventory_manager.create_or_update_inventory(
                product_id=product_id,
                tenant_id=tenant_id,
                quantity=quantity,
                location=location,
                sku=sku,
                reorder_point=reorder_point,
                reorder_quantity=reorder_quantity
            )
            flash('Inventory updated successfully', 'success')
        except Exception as e:
            logger.error(f"Error updating inventory: {e}")
            flash(f'Error updating inventory: {e}', 'danger')
        
        return redirect(url_for('order_routes.admin_inventory_detail', product_id=product_id))
    
    # Get inventory record
    from models import InventoryRecord
    inventory = InventoryRecord.query.filter_by(product_id=product_id, tenant_id=tenant_id).first()
    
    # Get transaction history
    from models import InventoryTransaction
    transactions = []
    if inventory:
        transactions = InventoryTransaction.query.filter_by(
            inventory_record_id=inventory.id
        ).order_by(InventoryTransaction.created_at.desc()).all()
    
    return render_template(
        'admin/inventory_detail.html',
        product=product,
        inventory=inventory,
        transactions=transactions,
        title=f'Inventory - {product.name}',
        active_nav='inventory'
    )