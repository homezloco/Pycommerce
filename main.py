"""
Main entry point for the PyCommerce application.

This script is designed to be run by a WSGI server like gunicorn.
It imports the FastAPI application and adapts it to work with WSGI.
"""
import logging

from asgi_wsgi_app import proxy_to_uvicorn, start_uvicorn_server

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Start the uvicorn server in a separate process
start_uvicorn_server()

# Create app variable for WSGI server to import
# This is a WSGI app that proxies requests to the uvicorn server
app = proxy_to_uvicorn

if __name__ == "__main__":
    import uvicorn
    from fastapi.templating import Jinja2Templates
    from routes.storefront import home, products, cart, checkout, pages
    from routes.admin import dashboard, products as admin_products, orders, customers, settings, plugins, tenants, media, inventory, analytics, page_builder

    templates = Jinja2Templates(directory="templates")

    from web_app import app as fastapi_app, templates
    
    # Set up storefront routes
    home_router = home.setup_routes(templates)
    fastapi_app.include_router(home_router)
    products.setup_routes(fastapi_app)
    cart.setup_routes(fastapi_app)
    checkout.setup_routes(fastapi_app)
    
    # Add explicit root path check
    @fastapi_app.get("/")
    async def root_redirect(request: Request):
        """Root endpoint to ensure application is running."""
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "title": "PyCommerce - A Python Ecommerce Platform",
                "cart_item_count": request.session.get("cart_item_count", 0)
            }
        )
    pages.setup_routes(templates)

    # Set up admin routes with the templates
    dashboard.setup_routes(templates)
    admin_products.setup_routes(templates)
    orders.setup_routes(templates)
    customers.setup_routes(templates)
    settings.setup_routes(templates)
    plugins.setup_routes(templates)
    tenants.setup_routes(templates)
    media.setup_routes(templates)
    inventory.setup_routes(templates)
    analytics.setup_routes(templates)
    
    # Register page_builder routes with FastAPI app
    page_builder_router = page_builder.setup_routes(templates)
    fastapi_app.include_router(page_builder_router)
    
    # Note: No need to include the router in the WSGI app, it's already included in the FastAPI app


    # Run with uvicorn directly when file is executed
    # Pass application as an import string to enable 'reload' or 'workers'
    uvicorn.run("web_app:app", host="0.0.0.0", port=5000, reload=True)