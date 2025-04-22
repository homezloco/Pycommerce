"""
Integrated Stripe Checkout Demo Routes

This module provides routes for a fully integrated Stripe checkout demo
that doesn't rely on a separate server.
"""
import os
import json
import logging
import traceback
from uuid import uuid4
from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

# Configure more detailed logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# We'll import stripe in functions to avoid issues with missing modules
try:
    import stripe
    # Log but don't store the key directly in a variable at the module level
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    logger.info(f"Stripe module imported successfully. API key is {'present' if STRIPE_SECRET_KEY else 'missing'}")
    if not STRIPE_SECRET_KEY:
        logger.warning("STRIPE_SECRET_KEY environment variable not set. Checkout will not work.")
except ImportError as e:
    logger.error(f"Failed to import stripe module: {e}")
    stripe = None
    STRIPE_SECRET_KEY = None

def setup_routes(templates):
    """
    Setup routes for integrated Stripe demo.
    
    Args:
        templates: Jinja2Templates instance
        
    Returns:
        APIRouter: The router with stripe demo routes
    """
    router = APIRouter()
    
    @router.get("/stripe-demo", response_class=HTMLResponse)
    async def stripe_demo(request: Request):
        """
        Render the Stripe demo page.
        
        Args:
            request (Request): The incoming request
            
        Returns:
            HTMLResponse: The rendered template
        """
        logger.info("Serving integrated Stripe demo page")
        return templates.TemplateResponse("stripe_demo.html", {"request": request})
    
    @router.get("/demo", response_class=HTMLResponse)
    async def demo_page(request: Request):
        """
        Alternative route to the Stripe demo page.
        
        Args:
            request (Request): The incoming request
            
        Returns:
            HTMLResponse: The rendered template
        """
        logger.info("Serving integrated Stripe demo page via /demo route")
        return templates.TemplateResponse("stripe_demo.html", {"request": request})
    
    @router.get("/stripe-demo/create-checkout-session")
    async def explain_checkout_session(request: Request):
        """
        Display information about the checkout session endpoint.
        
        Args:
            request (Request): The incoming request
            
        Returns:
            HTMLResponse: Information about how to use the endpoint
        """
        logger.info("GET request to create-checkout-session - providing usage information")
        
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Checkout Session Information</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container py-5">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h3>Stripe Checkout Session Endpoint</h3>
                    </div>
                    <div class="card-body">
                        <h5 class="card-title">This endpoint requires a POST request</h5>
                        <p class="card-text">You are accessing this endpoint with a GET request, but it requires a POST request with form data.</p>
                        
                        <div class="alert alert-info">
                            <h6>Required Form Fields:</h6>
                            <ul>
                                <li><strong>items</strong>: JSON string containing the cart items</li>
                                <li><strong>order_id</strong>: A unique identifier for the order</li>
                            </ul>
                        </div>
                        
                        <p>To use this endpoint correctly, visit the <a href="/stripe-demo">Stripe Demo Page</a>, add products to your cart, and click the "Checkout with Stripe" button.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
    
    @router.post("/stripe-demo/create-checkout-session")
    async def create_checkout_session(request: Request, items: str = Form(...), order_id: str = Form(...)):
        """
        Create a Stripe checkout session and redirect to the Stripe hosted checkout page.
        
        Args:
            request (Request): The incoming request
            items (str): JSON string containing items in the cart
            order_id (str): Order ID to identify this checkout session
            
        Returns:
            RedirectResponse: Redirect to Stripe checkout page
        """
        logger.info(f"Creating Stripe checkout session for order {order_id}")
        logger.info(f"Received items data: {items}")
        
        # First, make sure Stripe was imported successfully
        if not stripe:
            logger.error("Stripe module is not available.")
            return JSONResponse(
                status_code=500,
                content={"error": "Stripe payment processing is not available. Please contact support."}
            )
            
        # Initialize Stripe API key
        try:
            stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
            logger.info(f"Stripe API key status: {'Set' if stripe.api_key else 'Missing'}")
            # Print only the first few characters of the key for security reasons
            if stripe.api_key:
                safe_key_prefix = stripe.api_key[:4] + "..." if len(stripe.api_key) > 4 else "[HIDDEN]"
                logger.info(f"Using Stripe API key with prefix: {safe_key_prefix}")
        except Exception as key_error:
            logger.error(f"Error setting Stripe API key: {str(key_error)}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Error initializing Stripe: {str(key_error)}"}
            )
            
        # Check if the API key is set
        if not stripe.api_key:
            logger.error("STRIPE_SECRET_KEY not set. Cannot proceed with checkout.")
            return JSONResponse(
                status_code=500,
                content={"error": "Stripe API key not configured. Please set STRIPE_SECRET_KEY environment variable."}
            )
        
        try:
            # Parse the JSON items data
            items_data = json.loads(items)
            logger.debug(f"Parsed items data: {items_data}")
            
            # Create line items for Stripe
            line_items = []
            for item in items_data:
                # Convert price to cents for Stripe
                price_in_cents = int(item["price"] * 100)
                
                line_items.append({
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": item["name"],
                            "description": item.get("description", "")
                        },
                        "unit_amount": price_in_cents,
                    },
                    "quantity": item["quantity"],
                })
            
            # Generate a unique ID for this session
            session_id = str(uuid4())
            
            # Get the domain for success/cancel URLs
            host_url = str(request.base_url).rstrip('/')
            
            logger.info("Creating Stripe checkout session...")
            # Set the Stripe API key again just before using it to ensure it's fresh
            stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
            
            # Try to create the checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=line_items,
                mode="payment",
                success_url=f"{host_url}/stripe-demo/success?session_id={session_id}",
                cancel_url=f"{host_url}/stripe-demo/cancel",
                metadata={
                    "order_id": order_id,
                    "session_id": session_id
                }
            )
            
            logger.info(f"Stripe checkout session created successfully with ID: {checkout_session.id}")
            
            # Redirect to the Stripe checkout page
            return RedirectResponse(url=checkout_session.url, status_code=303)
            
        except Exception as e:
            # Capture any kind of error with full details
            error_type = type(e).__name__
            error_message = str(e)
            error_traceback = traceback.format_exc()
            
            logger.error(f"Error creating checkout session: {error_type}: {error_message}")
            logger.error(f"Error traceback: {error_traceback}")
            
            # Return a user-friendly error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "There was an error processing your payment request.",
                    "details": error_message,
                    "type": error_type
                }
            )
    
    @router.get("/stripe-demo/success", response_class=HTMLResponse)
    async def checkout_success(request: Request, session_id: str):
        """
        Handle successful checkout.
        
        Args:
            request (Request): The incoming request
            session_id (str): The session ID from the checkout session
            
        Returns:
            HTMLResponse: Success page
        """
        logger.info(f"Stripe checkout successful for session {session_id}")
        
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
            <div class="container py-5 text-center">
                <div class="card mx-auto" style="max-width: 600px;">
                    <div class="card-body">
                        <div class="mb-4">
                            <i class="fas fa-check-circle text-success fa-5x"></i>
                        </div>
                        <h1 class="mb-4">Payment Successful!</h1>
                        <p class="lead mb-4">Your payment has been processed successfully. Thank you for your purchase!</p>
                        <hr>
                        <div class="d-flex justify-content-between">
                            <a href="/stripe-demo" class="btn btn-outline-primary">Return to Demo</a>
                            <a href="/" class="btn btn-primary">Go to Homepage</a>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=success_html)
    
    @router.get("/stripe-demo/cancel", response_class=HTMLResponse)
    async def checkout_cancel(request: Request):
        """
        Handle cancelled checkout.
        
        Args:
            request (Request): The incoming request
            
        Returns:
            HTMLResponse: Cancel page
        """
        logger.info("Stripe checkout cancelled")
        
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
            <div class="container py-5 text-center">
                <div class="card mx-auto" style="max-width: 600px;">
                    <div class="card-body">
                        <div class="mb-4">
                            <i class="fas fa-times-circle text-danger fa-5x"></i>
                        </div>
                        <h1 class="mb-4">Payment Cancelled</h1>
                        <p class="lead mb-4">Your payment has been cancelled. No charges were made to your card.</p>
                        <hr>
                        <div class="d-flex justify-content-between">
                            <a href="/stripe-demo" class="btn btn-outline-primary">Return to Demo</a>
                            <a href="/" class="btn btn-primary">Go to Homepage</a>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=cancel_html)
    
    return router