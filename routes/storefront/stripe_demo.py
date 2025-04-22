"""
Stripe demo routes.

This module contains the routes for the Stripe demo feature.
"""
import logging
from flask import Blueprint, render_template, redirect, url_for, request, jsonify
import requests
import os

logger = logging.getLogger(__name__)

# Create a blueprint for the Stripe demo routes
blueprint = Blueprint('stripe_demo', __name__, url_prefix='/stripe-demo')

@blueprint.route('/', methods=['GET'])
def index():
    """Redirect to the Stripe demo app."""
    return redirect("http://localhost:5001/demo")

@blueprint.route('/checkout', methods=['GET'])
def checkout():
    """Proxy to the Stripe demo checkout page."""
    return redirect("http://localhost:5001/demo")

def register_routes(app):
    """Register the Stripe demo routes with the Flask app."""
    app.register_blueprint(blueprint)
    logger.info("Stripe demo routes registered successfully")
    return app