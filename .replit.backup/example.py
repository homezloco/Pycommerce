"""
Example usage of the PyCommerce SDK.

This script demonstrates how to use the PyCommerce SDK to create a simple
ecommerce application with API endpoints.
"""

import uvicorn
import logging
from fastapi import FastAPI
from pycommerce import PyCommerce
from pycommerce.plugins.payment import StripePaymentPlugin
from pycommerce.plugins.shipping import StandardShippingPlugin
from uuid import uuid4

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pycommerce.example")

# Create PyCommerce instance
commerce = PyCommerce(debug=True)

# Register plugins
commerce.plugins.register(StripePaymentPlugin())
commerce.plugins.register(StandardShippingPlugin())

# Create FastAPI app
app = commerce.create_app(
    title="PyCommerce Example API",
    description="Example API for the PyCommerce SDK",
    version="0.1.0"
)

# Add some sample data
def add_sample_data():
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
        }
    ]
    
    for product_data in products:
        commerce.products.create(product_data)
    
    # Add a user
    user = commerce.users.create({
        "email": "customer@example.com",
        "first_name": "John",
        "last_name": "Doe"
    })
    
    # Create a cart for the user
    cart = commerce.carts.create(user.id)
    
    # Add items to the cart
    for product in commerce.products.list()[:2]:  # Add first two products
        commerce.carts.add_item(cart.id, product.id, 1)
    
    logger.info("Added sample data")
    
    return user, cart


# Add sample data when the app starts
@app.on_event("startup")
async def startup_event():
    logger.info("Adding sample data...")
    add_sample_data()


# Run the server
if __name__ == "__main__":
    uvicorn.run("example:app", host="0.0.0.0", port=8000, reload=True)
