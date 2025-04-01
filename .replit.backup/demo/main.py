"""
Demo application for the PyCommerce SDK.

This module provides a simple Flask web application that demonstrates
the functionality of the PyCommerce SDK.
"""

import os
import logging
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

# Import from PyCommerce SDK
from pycommerce import PyCommerce
from pycommerce.plugins.payment import StripePaymentPlugin
from pycommerce.plugins.shipping import StandardShippingPlugin

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("pycommerce.demo")

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "pycommerce-demo-secret")

# Create PyCommerce instance
commerce = PyCommerce(debug=True)

# Register plugins
commerce.plugins.register(StripePaymentPlugin())
commerce.plugins.register(StandardShippingPlugin())

# Initialize session cart ID
def get_or_create_cart_id():
    """Get the current cart ID from session or create a new one."""
    if 'cart_id' not in session:
        # Create a new cart
        cart = commerce.carts.create()
        session['cart_id'] = str(cart.id)
        logger.debug(f"Created new cart with ID: {cart.id}")
    return session['cart_id']

# Add sample data
def add_sample_data():
    """Add sample data to the PyCommerce instance."""
    # Check if we already have products
    if commerce.products.list():
        logger.info("Sample data already exists")
        return
    
    # Add products
    products = [
        {
            "sku": "TSHIRT-RED-M",
            "name": "Red T-Shirt (M)",
            "description": "A comfortable red t-shirt made of 100% cotton.",
            "price": 19.99,
            "stock": 100,
            "categories": ["clothing", "t-shirts"]
        },
        {
            "sku": "TSHIRT-BLUE-M",
            "name": "Blue T-Shirt (M)",
            "description": "A comfortable blue t-shirt made of 100% cotton.",
            "price": 19.99,
            "stock": 80,
            "categories": ["clothing", "t-shirts"]
        },
        {
            "sku": "HOODIE-BLACK-L",
            "name": "Black Hoodie (L)",
            "description": "A warm black hoodie perfect for cold days.",
            "price": 39.99,
            "stock": 50,
            "categories": ["clothing", "hoodies"]
        },
        {
            "sku": "JEANS-BLUE-32",
            "name": "Blue Jeans (32)",
            "description": "Classic blue jeans with a comfortable fit.",
            "price": 49.99,
            "stock": 30,
            "categories": ["clothing", "jeans"]
        },
        {
            "sku": "SNEAKERS-WHITE-9",
            "name": "White Sneakers (Size 9)",
            "description": "Stylish white sneakers for everyday wear.",
            "price": 59.99,
            "stock": 25,
            "categories": ["footwear", "sneakers"]
        }
    ]
    
    for product_data in products:
        commerce.products.create(product_data)
    
    logger.info("Added sample data")

# Add sample data when the app starts
add_sample_data()

@app.route('/')
def index():
    """Render the home page."""
    return render_template('index.html')

@app.route('/products')
def products():
    """Render the products page."""
    # Get query parameters for filtering
    category = request.args.get('category')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    search = request.args.get('search')
    
    # Convert string parameters to appropriate types
    if min_price:
        try:
            min_price = float(min_price)
        except ValueError:
            min_price = None
    
    if max_price:
        try:
            max_price = float(max_price)
        except ValueError:
            max_price = None
    
    # Get products based on filters
    if search:
        product_list = commerce.products.search(search)
    else:
        product_list = commerce.products.list(
            category=category,
            min_price=min_price,
            max_price=max_price
        )
    
    # Get all categories for the filter dropdown
    all_products = commerce.products.list()
    categories = set()
    for product in all_products:
        for category in product.categories:
            categories.add(category)
    
    return render_template(
        'products.html', 
        products=product_list,
        categories=sorted(categories),
        current_category=category,
        current_min_price=min_price,
        current_max_price=max_price,
        current_search=search
    )

@app.route('/product/<product_id>')
def product_detail(product_id):
    """Render a product detail page."""
    try:
        product = commerce.products.get(product_id)
        return render_template('product_detail.html', product=product)
    except Exception as e:
        flash(f"Product not found: {str(e)}", "danger")
        return redirect(url_for('products'))

@app.route('/cart')
def cart():
    """Render the cart page."""
    cart_id = get_or_create_cart_id()
    
    try:
        # Get the cart and calculate totals
        cart = commerce.carts.get(cart_id)
        totals = commerce.carts.calculate_totals(cart_id, commerce.products)
        
        # Get product details for each item in the cart
        cart_items = []
        for item in cart.items:
            product = commerce.products.get(item.product_id)
            cart_items.append({
                'product': product,
                'quantity': item.quantity,
                'total': product.price * item.quantity
            })
        
        return render_template('cart.html', cart=cart, items=cart_items, totals=totals)
    except Exception as e:
        logger.error(f"Error retrieving cart: {str(e)}")
        flash(f"Error retrieving cart: {str(e)}", "danger")
        return redirect(url_for('products'))

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    """Add an item to the cart."""
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    cart_id = get_or_create_cart_id()
    
    try:
        commerce.carts.add_item(cart_id, product_id, quantity)
        product = commerce.products.get(product_id)
        flash(f"Added {quantity} x {product.name} to your cart", "success")
    except Exception as e:
        logger.error(f"Error adding item to cart: {str(e)}")
        flash(f"Error adding item to cart: {str(e)}", "danger")
    
    return redirect(url_for('cart'))

@app.route('/cart/update', methods=['POST'])
def update_cart():
    """Update the quantities of items in the cart."""
    cart_id = get_or_create_cart_id()
    
    # Get all product IDs and quantities from the form
    for key, value in request.form.items():
        if key.startswith('quantity_'):
            product_id = key.replace('quantity_', '')
            quantity = int(value)
            
            try:
                if quantity <= 0:
                    # Remove item if quantity is 0 or negative
                    commerce.carts.remove_item(cart_id, product_id)
                else:
                    # Update quantity
                    commerce.carts.update_item(cart_id, product_id, quantity)
            except Exception as e:
                logger.error(f"Error updating cart: {str(e)}")
                flash(f"Error updating cart: {str(e)}", "danger")
                return redirect(url_for('cart'))
    
    flash("Cart updated successfully", "success")
    return redirect(url_for('cart'))

@app.route('/cart/remove/<product_id>', methods=['POST'])
def remove_from_cart(product_id):
    """Remove an item from the cart."""
    cart_id = get_or_create_cart_id()
    
    try:
        commerce.carts.remove_item(cart_id, product_id)
        flash("Item removed from cart", "success")
    except Exception as e:
        logger.error(f"Error removing item from cart: {str(e)}")
        flash(f"Error removing item from cart: {str(e)}", "danger")
    
    return redirect(url_for('cart'))

@app.route('/cart/clear', methods=['POST'])
def clear_cart():
    """Clear all items from the cart."""
    cart_id = get_or_create_cart_id()
    
    try:
        commerce.carts.clear(cart_id)
        flash("Cart cleared", "success")
    except Exception as e:
        logger.error(f"Error clearing cart: {str(e)}")
        flash(f"Error clearing cart: {str(e)}", "danger")
    
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Render the checkout page and process checkout."""
    cart_id = get_or_create_cart_id()
    
    try:
        # Get the cart and calculate totals
        cart = commerce.carts.get(cart_id)
        totals = commerce.carts.calculate_totals(cart_id, commerce.products)
        
        # Get product details for each item in the cart
        cart_items = []
        for item in cart.items:
            product = commerce.products.get(item.product_id)
            cart_items.append({
                'product': product,
                'quantity': item.quantity,
                'total': product.price * item.quantity
            })
        
        # Check if the cart is empty
        if not cart_items:
            flash("Your cart is empty", "warning")
            return redirect(url_for('cart'))
        
        # Get shipping rates
        shipping_plugin = commerce.plugins.get("standard_shipping")
        shipping_rates = shipping_plugin.calculate_rates(
            items=[],  # Not used in the simple implementation
            destination={"country": "US", "postal_code": "10001"}
        )
        
        if request.method == 'POST':
            # Process the order
            shipping_address = {
                "first_name": request.form.get('first_name'),
                "last_name": request.form.get('last_name'),
                "address_line1": request.form.get('address_line1'),
                "address_line2": request.form.get('address_line2', ''),
                "city": request.form.get('city'),
                "state": request.form.get('state'),
                "postal_code": request.form.get('postal_code'),
                "country": request.form.get('country'),
                "phone": request.form.get('phone', '')
            }
            
            # Create the order
            order = commerce.orders.create_from_cart(
                cart_id, 
                commerce.products,
                commerce.carts,
                shipping_address
            )
            
            # Clear the cart after order creation
            session.pop('cart_id', None)
            
            flash("Order placed successfully!", "success")
            return render_template('order_confirmation.html', order=order, items=cart_items, totals=totals)
        
        return render_template(
            'checkout.html', 
            cart=cart, 
            items=cart_items, 
            totals=totals,
            shipping_rates=shipping_rates
        )
    
    except Exception as e:
        logger.error(f"Error processing checkout: {str(e)}")
        flash(f"Error processing checkout: {str(e)}", "danger")
        return redirect(url_for('cart'))

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.template_filter('currency')
def currency_filter(value):
    """Format a value as currency."""
    return f"${value:.2f}"

# Run the server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
