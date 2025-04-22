"""
Simple Flask application to demonstrate Stripe checkout.

This standalone Flask application demonstrates the Stripe checkout integration
without the complexity of the full PyCommerce platform.
"""
import os
import json
import logging
import stripe
from flask import Flask, render_template, request, redirect, url_for

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app with template folder explicitly set
app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get("SESSION_SECRET", "stripe-demo-secret")

# Configure Stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
# Log a masked version of the API key for debugging (showing only last 4 characters)
if stripe.api_key:
    masked_key = '*' * (len(stripe.api_key) - 4) + stripe.api_key[-4:]
    logger.info(f"Stripe API key configured: {masked_key}")
else:
    logger.warning("Stripe API key not set!")

@app.route('/')
def index():
    """Home page with redirect to demo page."""
    return redirect(url_for('demo'))

@app.route('/demo')
def demo():
    """Show the Stripe checkout demo page."""
    try:
        return render_template('stripe_demo.html')
    except Exception as e:
        logger.error(f"Error serving Stripe checkout demo page: {e}")
        return f"""
        <html>
        <head><title>Stripe Demo Error</title></head>
        <body>
            <h1>Error Loading Demo</h1>
            <p>There was an error loading the Stripe checkout demo page.</p>
            <p>Error: {str(e)}</p>
        </body>
        </html>
        """

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """Create a Stripe checkout session and redirect to the Stripe hosted checkout page."""
    try:
        # Get form data
        items_json = request.form.get('items')
        order_id = request.form.get('order_id')
        
        # Parse the items
        if not items_json:
            return "No items provided", 400
            
        items = json.loads(items_json)
        
        # Prepare line items for Stripe
        line_items = []
        for item in items:
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item.get('name', 'Product'),
                        'description': item.get('description', ''),
                    },
                    'unit_amount': int(float(item.get('price', 0)) * 100),  # Stripe expects amount in cents
                },
                'quantity': item.get('quantity', 1),
            })
        
        # Get the domain for success and cancel URLs
        domain_url = os.environ.get('REPLIT_DEV_DOMAIN')
        if not domain_url:
            domains = os.environ.get('REPLIT_DOMAINS', '').split(',')
            domain_url = domains[0] if domains else request.host
        
        # Create the checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=f'https://{domain_url}/success',
            cancel_url=f'https://{domain_url}/cancel',
            metadata={
                'order_id': order_id
            },
            automatic_tax={'enabled': True},
        )
        
        # Log the checkout session creation
        logger.info(f"Created Stripe checkout session {checkout_session.id} for order {order_id}")
        
        # Redirect to the Stripe checkout page
        return redirect(checkout_session.url)
        
    except Exception as e:
        logger.error(f"Error creating Stripe checkout session: {e}")
        return f"""
        <html>
        <head><title>Checkout Error</title></head>
        <body>
            <h1>Checkout Error</h1>
            <p>There was an error creating the checkout session.</p>
            <p>Error: {str(e)}</p>
            <p><a href="/demo">Return to Demo</a></p>
        </body>
        </html>
        """

@app.route('/success')
def success():
    """Show the success page."""
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
                                <a href="/demo" class="btn btn-primary btn-lg px-4 me-sm-3">Continue Shopping</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return success_html

@app.route('/cancel')
def cancel():
    """Show the cancel page."""
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
                                <a href="/demo" class="btn btn-primary btn-lg px-4 me-sm-3">Return to Demo</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return cancel_html

# Webhook endpoint to handle events from Stripe
@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhook events."""
    payload = request.data
    sig_header = request.headers.get('stripe-signature')
    
    # Use webhook secret from environment
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        if webhook_secret:
            # Verify the webhook signature
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        else:
            # If no webhook secret is set, parse the payload directly (only for development)
            event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
        
        # Handle the event
        if event.type == 'checkout.session.completed':
            session = event.data.object
            
            # Get the order ID from the metadata
            order_id = session.metadata.get('order_id')
            
            if order_id:
                # In a real app, you would update the order status
                logger.info(f"Order {order_id} marked as paid")
            
            # Log the completed checkout
            logger.info(f"Checkout session {session.id} completed")
        
        # Return a success response
        return {'status': 'success', 'event': event.type}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {'status': 'error', 'message': str(e)}, 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)