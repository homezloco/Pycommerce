"""
Stripe checkout integration for PyCommerce.

This module provides routes for integrating with Stripe's hosted checkout page.
"""

import os
import logging
import stripe
from flask import Blueprint, redirect, request, jsonify, url_for, render_template
from pycommerce.plugins.payment.config import STRIPE_API_KEY, STRIPE_PUBLIC_KEY, STRIPE_WEBHOOK_SECRET
from pycommerce.models.order import OrderStatus

# Configure Stripe API key
stripe.api_key = STRIPE_API_KEY or os.environ.get('STRIPE_SECRET_KEY')

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
    
    # Use webhook secret from config or environment
    webhook_secret = STRIPE_WEBHOOK_SECRET or os.environ.get('STRIPE_WEBHOOK_SECRET')
    
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
    Register the Stripe checkout routes with the application.
    
    This function supports both Flask and FastAPI applications.
    
    Args:
        app: The Flask or FastAPI application
    """
    # Check if this is a Flask app (has register_blueprint) or FastAPI
    if hasattr(app, 'register_blueprint'):
        # Flask app
        app.register_blueprint(stripe_checkout_bp, url_prefix='/checkout/stripe')
        logger.info("Stripe checkout routes registered successfully with Flask")
        return stripe_checkout_bp
    else:
        # Create FastAPI router
        from fastapi import APIRouter, Request, Form, Depends
        from fastapi.responses import RedirectResponse, JSONResponse
        from fastapi.templating import Jinja2Templates
        
        router = APIRouter(prefix="/checkout/stripe", tags=["stripe_checkout"])
        
        # Setup routes with FastAPI router
        @router.post("/create-checkout-session")
        async def api_create_checkout_session(
            request: Request,
            order_id: str = Form(None),
            items: str = Form(None),
            success_url: str = Form(None),
            cancel_url: str = Form(None)
        ):
            """Create a Stripe checkout session."""
            try:
                # Get the domain for success and cancel URLs
                domain_url = os.environ.get('REPLIT_DEV_DOMAIN')
                if not domain_url:
                    domains = os.environ.get('REPLIT_DOMAINS', '').split(',')
                    domain_url = domains[0] if domains else request.headers.get('host')
                
                # Default URLs if not provided
                success_url = success_url or f'https://{domain_url}/checkout/success'
                cancel_url = cancel_url or f'https://{domain_url}/checkout/cancel'
                
                # Parse items
                parsed_items = []
                if items:
                    import json
                    items_data = json.loads(items)
                    parsed_items = [
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
                
                # If no items were provided, return an error
                if not parsed_items:
                    return JSONResponse(content={"error": "No items provided"}, status_code=400)
                
                # Create a new Stripe checkout session
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=parsed_items,
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
                return RedirectResponse(url=checkout_session.url, status_code=303)
            except Exception as e:
                logger.error(f"Error creating Stripe checkout session: {e}")
                return JSONResponse(content={"error": str(e)}, status_code=500)
        
        @router.post("/webhook")
        async def api_stripe_webhook(request: Request):
            """Handle Stripe webhook events."""
            payload = await request.body()
            sig_header = request.headers.get('stripe-signature')
            
            # Use webhook secret from config or environment
            webhook_secret = STRIPE_WEBHOOK_SECRET or os.environ.get('STRIPE_WEBHOOK_SECRET')
            
            try:
                if webhook_secret:
                    # Verify the webhook signature
                    event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
                else:
                    # If no webhook secret is set, parse the payload directly (only for development)
                    body = await request.json()
                    event = stripe.Event.construct_from(body, stripe.api_key)
                
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
                            
                            # Update the order status to paid - use the correct method
                            if hasattr(order_manager, 'update_status'):
                                order_manager.update_status(order_id, OrderStatus.PAID)
                            elif hasattr(order_manager, 'update_order_status'):
                                order_manager.update_order_status(order_id, OrderStatus.PAID)
                            else:
                                # Fallback - try to update directly in the database
                                logger.warning("OrderManager missing update method, using direct DB update")
                                from sqlalchemy import text
                                from pycommerce.core.db import get_engine
                                engine = get_engine()
                                with engine.connect() as conn:
                                    conn.execute(
                                        text("UPDATE orders SET status = :status WHERE id = :order_id"),
                                        {"status": OrderStatus.PAID.value, "order_id": order_id}
                                    )
                                    conn.commit()
                            
                            logger.info(f"Order {order_id} marked as paid")
                        except Exception as e:
                            logger.error(f"Error updating order status: {e}")
                    
                    # Log the completed checkout
                    logger.info(f"Checkout session {session.id} completed")
                
                # Return a success response
                return JSONResponse(content={'status': 'success', 'event': event.type})
            except Exception as e:
                logger.error(f"Error processing webhook: {e}")
                return JSONResponse(content={'status': 'error', 'message': str(e)}, status_code=400)
        
        @router.get("/success")
        async def api_payment_success(request: Request):
            """Handle successful payment."""
            # Use the template function to render the success page
            from fastapi.responses import HTMLResponse
            success_html = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Payment Successful</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            </head>
            <body>
                <div class="container mt-5">
                    <div class="row justify-content-center">
                        <div class="col-md-8">
                            <div class="card border-success">
                                <div class="card-header bg-success text-white">
                                    <h4 class="mb-0"><i class="fas fa-check-circle me-2"></i>Payment Successful</h4>
                                </div>
                                <div class="card-body text-center py-5">
                                    <div class="mb-4">
                                        <i class="fas fa-check-circle text-success" style="font-size: 5rem;"></i>
                                    </div>
                                    <h2 class="mb-4">Thank You for Your Order!</h2>
                                    <p class="lead mb-4">Your payment has been processed successfully.</p>
                                    <p class="mb-5">We've sent a confirmation email with your order details. Your order is now being processed.</p>
                                    
                                    <div class="d-grid gap-2 d-sm-flex justify-content-sm-center">
                                        <a href="/" class="btn btn-primary btn-lg px-4 me-sm-3">Continue Shopping</a>
                                        <a href="/account/orders" class="btn btn-outline-secondary btn-lg px-4">View My Orders</a>
                                    </div>
                                </div>
                                <div class="card-footer bg-light">
                                    <div class="small text-muted">
                                        <span>If you have any questions about your order, please contact our <a href="/support">customer support</a>.</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=success_html)
        
        @router.get("/cancel")
        async def api_payment_cancel(request: Request):
            """Handle cancelled payment."""
            # Use the template function to render the cancel page
            from fastapi.responses import HTMLResponse
            cancel_html = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Payment Cancelled</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            </head>
            <body>
                <div class="container mt-5">
                    <div class="row justify-content-center">
                        <div class="col-md-8">
                            <div class="card border-secondary">
                                <div class="card-header bg-secondary text-white">
                                    <h4 class="mb-0"><i class="fas fa-times-circle me-2"></i>Payment Cancelled</h4>
                                </div>
                                <div class="card-body text-center py-5">
                                    <div class="mb-4">
                                        <i class="fas fa-times-circle text-secondary" style="font-size: 5rem;"></i>
                                    </div>
                                    <h2 class="mb-4">Your Payment Was Cancelled</h2>
                                    <p class="lead mb-4">Don't worry, your order has been saved but no payment has been processed.</p>
                                    <p class="mb-5">You can try again or choose a different payment method whenever you're ready.</p>
                                    
                                    <div class="d-grid gap-2 d-sm-flex justify-content-sm-center">
                                        <a href="/checkout" class="btn btn-primary btn-lg px-4 me-sm-3">Return to Checkout</a>
                                        <a href="/cart" class="btn btn-outline-secondary btn-lg px-4">Edit Cart</a>
                                    </div>
                                </div>
                                <div class="card-footer bg-light">
                                    <div class="small text-muted">
                                        <span>If you experienced issues with payment, please contact our <a href="/support">customer support</a>.</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=cancel_html)
        
        # Include the router
        app.include_router(router)
        logger.info("Stripe checkout routes registered successfully with FastAPI")
        return router