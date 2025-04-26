"""
Admin routes for estimates.

This module provides admin routes for managing estimates, including creating,
viewing, editing, converting estimates to orders, and exporting estimates as PDFs.
"""

import logging
import uuid
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from io import BytesIO

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file, make_response
from weasyprint import HTML, CSS

from pycommerce.models.order import OrderManager
from pycommerce.services.estimate_service import EstimateService

logger = logging.getLogger(__name__)

# Create blueprint
estimates_bp = Blueprint('admin_estimates', __name__)

# Initialize services
estimate_service = EstimateService()
order_manager = OrderManager()


@estimates_bp.route('/admin/estimates')
def list_estimates():
    """List all estimates for a tenant."""
    tenant_id = request.args.get('tenant_id')
    if not tenant_id:
        flash('Tenant ID is required', 'error')
        return redirect(url_for('admin.dashboard'))
    
    estimates = estimate_service.get_for_tenant(tenant_id)
    
    return render_template(
        'admin/estimates/list.html',
        estimates=estimates,
        tenant_id=tenant_id
    )


@estimates_bp.route('/admin/estimates/create', methods=['GET', 'POST'])
def create_estimate():
    """Create a new estimate."""
    tenant_id = request.args.get('tenant_id')
    if not tenant_id:
        flash('Tenant ID is required', 'error')
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        data = {
            'tenant_id': tenant_id,
            'customer_id': request.form.get('customer_id'),
            'customer_name': request.form.get('customer_name'),
            'customer_email': request.form.get('customer_email'),
            'customer_phone': request.form.get('customer_phone'),
            'project_name': request.form.get('project_name'),
            'project_description': request.form.get('project_description'),
            'tax': float(request.form.get('tax', 0)),
            'status': 'DRAFT'
        }
        
        estimate = estimate_service.create_estimate(data)
        if estimate:
            flash('Estimate created successfully', 'success')
            return redirect(url_for('admin_estimates.edit_estimate', estimate_id=estimate.id))
        else:
            flash('Failed to create estimate', 'error')
    
    return render_template(
        'admin/estimates/create.html',
        tenant_id=tenant_id
    )


@estimates_bp.route('/admin/estimates/<estimate_id>')
def view_estimate(estimate_id):
    """View an estimate."""
    estimate = estimate_service.get_by_id(estimate_id)
    if not estimate:
        flash('Estimate not found', 'error')
        return redirect(url_for('admin.dashboard'))
    
    return render_template(
        'admin/estimates/view.html',
        estimate=estimate
    )


@estimates_bp.route('/admin/estimates/<estimate_id>/edit', methods=['GET', 'POST'])
def edit_estimate(estimate_id):
    """Edit an estimate."""
    estimate = estimate_service.get_by_id(estimate_id)
    if not estimate:
        flash('Estimate not found', 'error')
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        data = {
            'customer_name': request.form.get('customer_name'),
            'customer_email': request.form.get('customer_email'),
            'customer_phone': request.form.get('customer_phone'),
            'project_name': request.form.get('project_name'),
            'project_description': request.form.get('project_description'),
            'tax': float(request.form.get('tax', 0)),
            'status': request.form.get('status', 'DRAFT')
        }
        
        updated_estimate = estimate_service.update_estimate(estimate_id, data)
        if updated_estimate:
            flash('Estimate updated successfully', 'success')
            return redirect(url_for('admin_estimates.view_estimate', estimate_id=estimate_id))
        else:
            flash('Failed to update estimate', 'error')
    
    return render_template(
        'admin/estimates/edit.html',
        estimate=estimate
    )


@estimates_bp.route('/admin/estimates/<estimate_id>/delete', methods=['POST'])
def delete_estimate(estimate_id):
    """Delete an estimate."""
    success = estimate_service.delete_estimate(estimate_id)
    if success:
        flash('Estimate deleted successfully', 'success')
    else:
        flash('Failed to delete estimate', 'error')
    
    return redirect(url_for('admin_estimates.list_estimates', tenant_id=request.args.get('tenant_id')))


@estimates_bp.route('/admin/estimates/<estimate_id>/convert', methods=['POST'])
def convert_to_order(estimate_id):
    """Convert an estimate to an order."""
    order, error = estimate_service.convert_to_order(estimate_id)
    if order:
        flash('Estimate converted to order successfully', 'success')
        return redirect(url_for('admin_orders.view_order', order_id=order.id))
    else:
        flash(f'Failed to convert estimate to order: {error}', 'error')
        return redirect(url_for('admin_estimates.view_estimate', estimate_id=estimate_id))


@estimates_bp.route('/admin/estimates/<estimate_id>/materials', methods=['GET', 'POST'])
def manage_materials(estimate_id):
    """Manage materials for an estimate."""
    estimate = estimate_service.get_by_id(estimate_id)
    if not estimate:
        flash('Estimate not found', 'error')
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        # Update all materials at once
        materials_data = []
        
        # Process form data for materials
        material_ids = request.form.getlist('material_id')
        material_names = request.form.getlist('material_name')
        material_descriptions = request.form.getlist('material_description')
        material_quantities = request.form.getlist('material_quantity')
        material_units = request.form.getlist('material_unit')
        material_cost_prices = request.form.getlist('material_cost_price')
        material_selling_prices = request.form.getlist('material_selling_price')
        
        for i in range(len(material_names)):
            material_data = {
                'name': material_names[i],
                'description': material_descriptions[i],
                'quantity': float(material_quantities[i]),
                'unit': material_units[i],
                'cost_price': float(material_cost_prices[i]),
                'selling_price': float(material_selling_prices[i])
            }
            
            # Add product ID if available
            product_id = request.form.getlist('material_product_id')[i]
            if product_id:
                material_data['product_id'] = product_id
            
            materials_data.append(material_data)
        
        # Update estimate with new materials
        updated_estimate = estimate_service.update_estimate(estimate_id, {'materials': materials_data})
        if updated_estimate:
            flash('Materials updated successfully', 'success')
        else:
            flash('Failed to update materials', 'error')
        
        return redirect(url_for('admin_estimates.view_estimate', estimate_id=estimate_id))
    
    return render_template(
        'admin/estimates/materials.html',
        estimate=estimate
    )


@estimates_bp.route('/admin/estimates/<estimate_id>/labor', methods=['GET', 'POST'])
def manage_labor(estimate_id):
    """Manage labor items for an estimate."""
    estimate = estimate_service.get_by_id(estimate_id)
    if not estimate:
        flash('Estimate not found', 'error')
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        # Update all labor items at once
        labor_data = []
        
        # Process form data for labor items
        labor_names = request.form.getlist('labor_name')
        labor_descriptions = request.form.getlist('labor_description')
        labor_hours = request.form.getlist('labor_hours')
        labor_cost_prices = request.form.getlist('labor_cost_price')
        labor_selling_prices = request.form.getlist('labor_selling_price')
        
        for i in range(len(labor_names)):
            labor_item_data = {
                'name': labor_names[i],
                'description': labor_descriptions[i],
                'hours': float(labor_hours[i]),
                'cost_price': float(labor_cost_prices[i]),
                'selling_price': float(labor_selling_prices[i])
            }
            
            labor_data.append(labor_item_data)
        
        # Update estimate with new labor items
        updated_estimate = estimate_service.update_estimate(estimate_id, {'labor_items': labor_data})
        if updated_estimate:
            flash('Labor items updated successfully', 'success')
        else:
            flash('Failed to update labor items', 'error')
        
        return redirect(url_for('admin_estimates.view_estimate', estimate_id=estimate_id))
    
    return render_template(
        'admin/estimates/labor.html',
        estimate=estimate
    )


@estimates_bp.route('/admin/estimates/add-material', methods=['POST'])
def add_material():
    """Add a material to an estimate via AJAX."""
    estimate_id = request.json.get('estimate_id')
    if not estimate_id:
        return jsonify({'success': False, 'error': 'Estimate ID is required'}), 400
    
    estimate = estimate_service.get_by_id(estimate_id)
    if not estimate:
        return jsonify({'success': False, 'error': 'Estimate not found'}), 404
    
    # Get current materials
    materials = [
        {
            'name': m.name,
            'description': m.description,
            'quantity': m.quantity,
            'unit': m.unit,
            'cost_price': m.cost_price,
            'selling_price': m.selling_price,
            'product_id': m.product_id
        }
        for m in estimate.materials
    ]
    
    # Add new material
    materials.append({
        'name': request.json.get('name', 'New Material'),
        'description': request.json.get('description', ''),
        'quantity': float(request.json.get('quantity', 1)),
        'unit': request.json.get('unit', 'piece'),
        'cost_price': float(request.json.get('cost_price', 0)),
        'selling_price': float(request.json.get('selling_price', 0)),
        'product_id': request.json.get('product_id')
    })
    
    # Update estimate with new materials
    updated_estimate = estimate_service.update_estimate(estimate_id, {'materials': materials})
    if updated_estimate:
        new_material = updated_estimate.materials[-1]
        return jsonify({
            'success': True,
            'material': {
                'id': new_material.id,
                'name': new_material.name,
                'description': new_material.description,
                'quantity': new_material.quantity,
                'unit': new_material.unit,
                'cost_price': new_material.cost_price,
                'selling_price': new_material.selling_price,
                'total_cost': new_material.total_cost,
                'total_price': new_material.total_price,
                'profit': new_material.profit,
                'profit_margin': new_material.profit_margin
            }
        })
    else:
        return jsonify({'success': False, 'error': 'Failed to add material'}), 500


@estimates_bp.route('/admin/estimates/<estimate_id>/export-pdf', methods=['GET'])
def export_estimate_pdf(estimate_id):
    """Export an estimate as a PDF file."""
    estimate = estimate_service.get_by_id(estimate_id)
    if not estimate:
        flash('Estimate not found', 'error')
        return redirect(url_for('admin.dashboard'))
    
    # Render the estimate template to HTML
    html_content = render_template(
        'admin/estimates/pdf_template.html',
        estimate=estimate
    )
    
    # Use WeasyPrint to convert HTML to PDF
    pdf = HTML(string=html_content).write_pdf()
    
    # Create a response with the PDF
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=estimate_{estimate.estimate_number}.pdf'
    
    return response


@estimates_bp.route('/admin/estimates/add-labor', methods=['POST'])
def add_labor():
    """Add a labor item to an estimate via AJAX."""
    estimate_id = request.json.get('estimate_id')
    if not estimate_id:
        return jsonify({'success': False, 'error': 'Estimate ID is required'}), 400
    
    estimate = estimate_service.get_by_id(estimate_id)
    if not estimate:
        return jsonify({'success': False, 'error': 'Estimate not found'}), 404
    
    # Get current labor items
    labor_items = [
        {
            'name': l.name,
            'description': l.description,
            'hours': l.hours,
            'cost_price': l.cost_price,
            'selling_price': l.selling_price
        }
        for l in estimate.labor_items
    ]
    
    # Add new labor item
    labor_items.append({
        'name': request.json.get('name', 'New Labor'),
        'description': request.json.get('description', ''),
        'hours': float(request.json.get('hours', 1)),
        'cost_price': float(request.json.get('cost_price', 0)),
        'selling_price': float(request.json.get('selling_price', 0))
    })
    
    # Update estimate with new labor items
    updated_estimate = estimate_service.update_estimate(estimate_id, {'labor_items': labor_items})
    if updated_estimate:
        new_labor = updated_estimate.labor_items[-1]
        return jsonify({
            'success': True,
            'labor': {
                'id': new_labor.id,
                'name': new_labor.name,
                'description': new_labor.description,
                'hours': new_labor.hours,
                'cost_price': new_labor.cost_price,
                'selling_price': new_labor.selling_price,
                'total_cost': new_labor.total_cost,
                'total_price': new_labor.total_price,
                'profit': new_labor.profit,
                'profit_margin': new_labor.profit_margin
            }
        })
    else:
        return jsonify({'success': False, 'error': 'Failed to add labor item'}), 500