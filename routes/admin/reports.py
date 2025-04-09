"""
Reports management routes for the admin dashboard.

This module provides routes for generating and viewing sales, products, customers,
and tax reports.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
# Note: The login_required decorator will be added when the authentication system is fully implemented
# For now we'll keep routes accessible without login for testing

# Create a blueprint
reports_bp = Blueprint('admin_reports', __name__)

@reports_bp.route('/admin/reports', methods=['GET'])
def reports():
    """Reports dashboard."""
    return render_template('admin/reports.html',
                          active_page='reports',
                          status_message=request.args.get('status_message'),
                          status_type=request.args.get('status_type', 'info'))