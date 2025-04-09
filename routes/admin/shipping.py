"""
Shipping management routes for the admin dashboard.

This module provides routes for managing shipping methods, zones, rates, and labels.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
# Note: The login_required decorator will be added when the authentication system is fully implemented
# For now we'll keep routes accessible without login for testing

# Create a blueprint
shipping_bp = Blueprint('admin_shipping', __name__)

@shipping_bp.route('/admin/shipping', methods=['GET'])
def shipping():
    """Shipping management dashboard."""
    return render_template('admin/shipping.html', 
                          active_page='shipping',
                          status_message=request.args.get('status_message'),
                          status_type=request.args.get('status_type', 'info'))