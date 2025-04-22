"""
Stripe checkout integration for PyCommerce.

This module provides routes for integrating with Stripe's hosted checkout page.
"""

import os
import logging
import stripe
from flask import Blueprint, redirect, request, jsonify, url_for, render_template
from pycommerce.plugins.payment.config import get_payment_settings
from pycommerce.models.order import OrderStatus

# Configure Stripe API key
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Set up logging
logger = logging.getLogger(__name__)

# Create Blueprint for Stripe checkout routes
stripe_checkout_bp = Blueprint('stripe_checkout', __name__)

@stripe_checkout_bp.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """
    Create a Stripe checkout session and redirect to the Stripe hosted checkout page.
    
    This endpoint expects the following parameters in the request:
    - order_id: The ID of the order to be paid
    - items: List of items in the order (dict with product_id, name, price, quantity)
    - success_url: URL to redirect to after successful payment
    - cancel_url: URL to redirect to if payment is cancelled
    """
    try:
        # Get the domain for success and cancel URLs
        domain_url = os.environ.get('REPLIT_DEV_DOMAIN')
        if not domain_url:
            domains = os.environ.get('REPLIT_DOMAINS', '').split(',')
            domain_url = domains[0] if domains else request.host

        # Default URLs if not provided
        success_url = request.form.get('success_url', f'https://{domain_url}/checkout/success')
        cancel_url = request.form.get('cancel_url', f'https://{domain_url}/checkout/cancel')
        
        # Get order details from the request
        order_id = request.form.get('order_id')
        
        # Try to parse items from the request
        items = []
        try:
            if 'items' in request.form:
                import json
                items_data = json.loads(request.form.get('items', '[]'))
                items = [
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': item.get('name', 'Product'),
                                'description': item.get('description', ''),
                            },
                            'unit_amount': int(float(item.get('price', 0)) * 100),  # Stripe expects amount in cents
                        },
                        'quantity': item.get('quantity', 1),
                    }
                    for item in items_data
                ]
        except Exception as e:
            logger.error(f"Error parsing items: {e}")
            return jsonify({"error": "Invalid items data"}), 400
        
        # If no items were provided, return an error
        if not items:
            return jsonify({"error": "No items provided"}), 400
        
        # Create a new Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=items,
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'order_id': order_id
            },
            automatic_tax={'enabled': True},
        )
        
        # Log the checkout session creation
        logger.info(f"Created Stripe checkout session {checkout_session.id} for order {order_id}")
        
        # Redirect to the Stripe checkout page
        return redirect(checkout_session.url, code=303)
    
    except Exception as e:
        logger.error(f"Error creating Stripe checkout session: {e}")
        return jsonify({"error": str(e)}), 500

@stripe_checkout_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """
    Handle Stripe webhook events.
    
    This endpoint receives webhook events from Stripe and processes them accordingly.
    """
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    # Webhook secret should be set in the environment
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        if webhook_secret:
            # Verify the webhook signature
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        else:
            # If no webhook secret is set, parse the payload directly (only for development)
            event = stripe.Event.construct_from(
                request.json, stripe.api_key
            )
        
        # Handle the event
        if event.type == 'checkout.session.completed':
            session = event.data.object
            
            # Get the order ID from the metadata
            order_id = session.metadata.get('order_id')
            
            if order_id:
                # Update the order status based on the payment status
                try:
                    from pycommerce.models.order import OrderManager
                    order_manager = OrderManager()
                    
                    # Update the order status to paid
                    order_manager.update_order_status(order_id, OrderStatus.PAID)
                    
                    logger.info(f"Order {order_id} marked as paid")
                except Exception as e:
                    logger.error(f"Error updating order status: {e}")
            
            # Log the completed checkout
            logger.info(f"Checkout session {session.id} completed")
        
        # Return a success response
        return jsonify({'status': 'success', 'event': event.type})
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

@stripe_checkout_bp.route('/success', methods=['GET'])
def payment_success():
    """
    Handle successful payment.
    
    This endpoint is called when a payment is successful.
    """
    return render_template('storefront/checkout/success.html')

@stripe_checkout_bp.route('/cancel', methods=['GET'])
def payment_cancel():
    """
    Handle cancelled payment.
    
    This endpoint is called when a payment is cancelled.
    """
    return render_template('storefront/checkout/cancel.html')

def setup_routes(app):
    """
    Register the Stripe checkout routes with the Flask app.
    
    Args:
        app: The Flask application
    """
    app.register_blueprint(stripe_checkout_bp, url_prefix='/checkout/stripe')
    logger.info("Stripe checkout routes registered successfully")
    return stripe_checkout_bp