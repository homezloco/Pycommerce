"""
Main entry point for the PyCommerce application.

This script is designed to be run by a WSGI server like gunicorn.
It imports the FastAPI application and adapts it to work with WSGI.
"""
import logging
import os
import sys
from pathlib import Path

from asgi_wsgi_app import proxy_to_uvicorn, start_uvicorn_server
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath("."))

# Start the uvicorn server in a separate process
start_uvicorn_server()

# Create app variable for WSGI server to import
# This is a WSGI app that proxies requests to the uvicorn server
app = proxy_to_uvicorn

if __name__ == "__main__":
    import uvicorn
    from fastapi import Request
    from fastapi.templating import Jinja2Templates
    from fastapi.responses import HTMLResponse, RedirectResponse
    from fastapi.staticfiles import StaticFiles

    # Import our application from web_app.py
    # This is important as it ensures we're using the same FastAPI instance
    from web_app import app as fastapi_app, templates

    # Explicitly ensure static files are mounted
    try:
        if not any(getattr(route, "path", "") == "/static" for route in fastapi_app.routes):
            logger.info("Mounting static files directory")
            fastapi_app.mount("/static", StaticFiles(directory="static"), name="static")
            logger.info("Static files mounted successfully")
    except Exception as e:
        logger.error(f"Error mounting static files: {e}")

    # Make sure we have an explicit root path handler
    @fastapi_app.get("/", response_class=HTMLResponse)
    async def explicit_root(request: Request):
        """Root endpoint to ensure application is running."""
        try:
            return templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "title": "PyCommerce - A Python Ecommerce Platform",
                    "cart_item_count": request.session.get("cart_item_count", 0)
                }
            )
        except Exception as e:
            logger.error(f"Error rendering home page: {e}")
            return HTMLResponse(
                content=f"""
                <html>
                <head><title>PyCommerce</title></head>
                <body>
                    <h1>PyCommerce Platform</h1>
                    <p>The application is running, but there was an error rendering the home page.</p>
                    <p>Error: {str(e)}</p>
                    <p><a href="/admin/dashboard">Go to Admin Dashboard</a></p>
                    <p><a href="/frontend-debug">View Debug Information</a></p>
                </body>
                </html>
                """,
                status_code=200
            )

    # Add a catch-all route for admin paths
    @fastapi_app.get("/admin/{path:path}", response_class=HTMLResponse)
    async def admin_catch_all(request: Request, path: str):
        """Catch-all handler for admin routes to ensure they can be accessed directly."""
        try:
            # Try to serve the admin template
            template_path = f"admin/{path}.html"
            logger.info(f"Attempting to serve template: {template_path}")
            return templates.TemplateResponse(
                template_path,
                {"request": request}
            )
        except Exception as e:
            logger.error(f"Error in admin catch-all route ({path}): {e}")
            # Redirect to dashboard if template not found
            return RedirectResponse(url="/admin/dashboard")

    # Set up storefront routes
    home_router = home.setup_routes(templates)
    fastapi_app.include_router(home_router)
    products.setup_routes(fastapi_app)
    cart.setup_routes(fastapi_app)
    checkout.setup_routes(fastapi_app)
    pages.setup_routes(templates)

    # Set up admin routes with the templates
    dashboard_router = dashboard.setup_routes(templates)
    fastapi_app.include_router(dashboard_router)
    products_router = admin_products.setup_routes(templates)
    fastapi_app.include_router(products_router)
    orders_router = orders.setup_routes(templates)
    fastapi_app.include_router(orders_router)
    customers_router = customers.setup_routes(templates)
    fastapi_app.include_router(customers_router)
    settings_router = settings.setup_routes(templates)
    fastapi_app.include_router(settings_router)
    plugins_router = plugins.setup_routes(templates)
    fastapi_app.include_router(plugins_router)
    tenants_router = tenants.setup_routes(templates)
    fastapi_app.include_router(tenants_router)
    media_router = media.setup_routes(templates)
    fastapi_app.include_router(media_router)
    inventory_router = inventory.setup_routes(templates)
    fastapi_app.include_router(inventory_router)
    analytics_router = analytics.setup_routes(templates)
    fastapi_app.include_router(analytics_router)

    # Register page_builder routes with FastAPI app
    page_builder_router = page_builder.setup_routes(templates)
    fastapi_app.include_router(page_builder_router)

    # Note: No need to include the router in the WSGI app, it's already included in the FastAPI app


    # Run with uvicorn directly when file is executed
    # Pass application as an import string to enable 'reload' or 'workers'
    uvicorn.run(fastapi_app, host="0.0.0.0", port=5000, reload=True)