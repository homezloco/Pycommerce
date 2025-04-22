"""
Main web application for PyCommerce.

This file creates the main FastAPI application using the app factory.
It represents the entry point for uvicorn when running directly.
"""
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the application using the factory
from app_factory import create_app

app, templates = create_app()

# Explicitly mount static files
try:
    # Check if static files are already mounted
    if not any(getattr(route, "path", "") == "/static" for route in app.routes):
        logger.info("Mounting static files directory")
        from fastapi.staticfiles import StaticFiles
        app.mount("/static", StaticFiles(directory="static"), name="static")
        logger.info("Static files mounted successfully")
except Exception as e:
    logger.error(f"Error mounting static files: {e}")

# Register admin routes
try:
    from routes.admin.auth import setup_routes as setup_auth_routes
    from routes.admin.dashboard import setup_routes as setup_dashboard_routes
    from routes.admin.products import setup_routes as setup_products_routes
    from routes.admin.orders import setup_routes as setup_orders_routes
    from routes.admin.customers import setup_routes as setup_customers_routes
    from routes.admin.settings import setup_routes as setup_settings_routes
    from routes.admin.plugins import setup_routes as setup_plugins_routes
    from routes.admin.tenants import setup_routes as setup_tenants_routes
    from routes.admin.media import setup_routes as setup_media_routes
    from routes.admin.inventory import setup_routes as setup_inventory_routes
    from routes.admin.analytics import setup_routes as setup_analytics_routes
    from routes.admin.page_builder import setup_routes as setup_page_builder_routes
    from routes.admin.store_settings import setup_routes as setup_store_settings_routes
    from routes.admin.marketing import setup_routes as setup_marketing_routes
    from routes.admin.users import setup_routes as setup_users_routes
    from routes.admin.categories import setup_routes as setup_categories_routes
    from routes.admin.ai_config import setup_routes as setup_ai_config_routes
    from routes.admin.theme_settings import setup_routes as setup_theme_settings_routes
    from routes.admin.returns import setup_routes as setup_returns_routes
    from routes.admin.debug import setup_routes as setup_debug_routes # Added import for debug routes
    from routes.admin.ai_content import setup_routes as setup_ai_content_routes
    from routes.admin.security import setup_routes as setup_security_routes
    from routes.admin.estimates_setup import setup_routes as setup_estimates_routes

    # Include admin routers
    # First set up auth routes since other admin routes depend on them
    auth_router = setup_auth_routes(templates)
    app.include_router(auth_router)
    
    dashboard_router = setup_dashboard_routes(templates)
    app.include_router(dashboard_router)

    products_router = setup_products_routes(templates)
    app.include_router(products_router)

    orders_router = setup_orders_routes(templates)
    app.include_router(orders_router)

    customers_router = setup_customers_routes(templates)
    app.include_router(customers_router)

    settings_router = setup_settings_routes(templates)
    app.include_router(settings_router)

    plugins_router = setup_plugins_routes(templates)
    app.include_router(plugins_router)

    tenants_router = setup_tenants_routes(templates)
    app.include_router(tenants_router)

    media_router = setup_media_routes(templates)
    app.include_router(media_router)

    inventory_router = setup_inventory_routes(templates)
    app.include_router(inventory_router)

    analytics_router = setup_analytics_routes(templates)
    app.include_router(analytics_router)

    # Ensure templates is properly passed to page builder routes
    try:
        # Make sure the templates object is correctly initialized
        if templates is None:
            logger.error("Templates object is None, cannot initialize page builder routes properly")
            from fastapi.templating import Jinja2Templates
            import os
            templates = Jinja2Templates(directory=os.path.join(os.getcwd(), "templates"))
            logger.info("Created new templates object for page builder")

        page_builder_router = setup_page_builder_routes(templates)
        app.include_router(page_builder_router)
        logger.info("Page Builder routes initialized successfully with templates")
    except Exception as e:
        logger.error(f"Error setting up page builder routes: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

    # Add the additional routers
    store_settings_router = setup_store_settings_routes(templates)
    app.include_router(store_settings_router)

    marketing_router = setup_marketing_routes(templates)
    app.include_router(marketing_router)

    users_router = setup_users_routes(templates)
    app.include_router(users_router)

    categories_router = setup_categories_routes(templates)
    app.include_router(categories_router)

    ai_config_router = setup_ai_config_routes(templates)
    app.include_router(ai_config_router)

    theme_settings_router = setup_theme_settings_routes(templates)
    app.include_router(theme_settings_router)

    returns_router = setup_returns_routes(templates)
    app.include_router(returns_router)

    debug_router = setup_debug_routes(templates) # Initialize debug routes
    app.include_router(debug_router)
    
    security_router = setup_security_routes(templates) # Initialize security routes
    app.include_router(security_router)
    
    # Initialize estimates routes
    estimates_router = setup_estimates_routes(templates)
    app.include_router(estimates_router)

    logger.info("Admin routes registered successfully")
except ImportError as e:
    logger.warning(f"Failed to register admin routes: {str(e)}")

# Register storefront routes
try:
    from routes.storefront.home import setup_routes as setup_home_routes
    from routes.storefront.products import setup_routes as setup_storefront_products_routes
    from routes.storefront.cart import setup_routes as setup_cart_routes
    from routes.storefront.checkout import setup_routes as setup_checkout_routes
    from routes.storefront.pages import setup_routes as setup_pages_routes
    from routes.storefront.stores import setup_routes as setup_storefront_stores_routes

    # Include storefront routers
    home_router = setup_home_routes(templates)
    app.include_router(home_router)

    products_router = setup_storefront_products_routes(templates)
    app.include_router(products_router)

    cart_router = setup_cart_routes(templates)
    app.include_router(cart_router)

    checkout_router = setup_checkout_routes(templates)
    app.include_router(checkout_router)

    pages_router = setup_pages_routes(templates)
    app.include_router(pages_router)

    storefront_stores_router = setup_storefront_stores_routes(templates)
    app.include_router(storefront_stores_router)

    logger.info("Storefront routes registered successfully")
except ImportError as e:
    logger.warning(f"Failed to register storefront routes: {str(e)}")

# Register store settings test routes
try:
    from routes.admin.store_settings_test import setup_routes
    test_routes_router = setup_routes(templates)
    app.include_router(test_routes_router)
    logger.info("Store settings test routes registered successfully")
except ImportError as e:
    logger.warning(f"Failed to register store settings test routes: {str(e)}")

# Register API routes
try:
    # First attempt to use the old API route registration method
    try:
        from pycommerce.api.routes import register_api_routes
        register_api_routes(app)
    except ImportError:
        # Use the new structured API routes
        from routes.api import api_router
        app.include_router(api_router)
    
    # Setup API documentation
    try:
        from pycommerce.api.docs import setup_api_documentation
        setup_api_documentation(app)
        logger.info("API documentation setup successfully")
    except Exception as e:
        logger.warning(f"Failed to set up API documentation: {str(e)}")
    
    logger.info("API routes registered successfully")
except Exception as e:
    logger.warning(f"Failed to register API routes: {str(e)}")

# Health check endpoint required by the ASGI-WSGI adapter
@app.get("/api/health")
async def health_check():
    """Health check endpoint that the proxy uses to determine if the app is running."""
    return {"status": "ok", "version": "1.0.0", "message": "PyCommerce API is running"}

# Static API documentation route
@app.get("/api/docs", response_class=HTMLResponse)
async def get_api_docs():
    """Serve the static API documentation page."""
    try:
        with open("static/api-docs.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except Exception as e:
        logger.error(f"Error serving API documentation: {str(e)}")
        return HTMLResponse(
            content=f"""
            <html>
            <head><title>API Documentation Error</title></head>
            <body>
                <h1>API Documentation Error</h1>
                <p>There was an error loading the API documentation.</p>
                <p>Error: {str(e)}</p>
                <p><a href="/">Return to Homepage</a></p>
            </body>
            </html>
            """,
            status_code=500
        )

# Direct OpenAPI schema endpoint
@app.get("/api/openapi.json", include_in_schema=False)
async def get_openapi_schema():
    """
    Get the OpenAPI schema for the application.
    
    Returns:
        The OpenAPI schema as JSON
    """
    from fastapi.openapi.utils import get_openapi
    
    # Generate the OpenAPI schema dynamically
    openapi_schema = get_openapi(
        title="PyCommerce API",
        version="1.0.0",
        description="The official API for PyCommerce platform",
        routes=app.routes
    )
    
    # Add additional information
    openapi_schema["info"]["contact"] = {
        "name": "PyCommerce Support",
        "url": "https://pycommerce.example.com/support",
        "email": "support@pycommerce.example.com",
    }
    
    openapi_schema["info"]["license"] = {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    }
    
    # Add server URLs
    openapi_schema["servers"] = [
        {"url": "/", "description": "Current environment"}
    ]
    
    # Add security schemes
    openapi_schema["components"] = openapi_schema.get("components", {})
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter JWT token"
        }
    }
    
    return openapi_schema

@app.get("/health")
async def root_health_check():
    """Alternative health check endpoint."""
    return {"status": "ok", "version": "1.0.0", "message": "PyCommerce API is running"}

# API documentation routes (redirects)
@app.get("/api", include_in_schema=False, response_class=HTMLResponse)
async def api_docs_redirect():
    """Redirect to API documentation page."""
    logger.info("Redirecting to API documentation")
    return RedirectResponse(url="/api/docs")

# ReDoc UI
@app.get("/api/redoc", include_in_schema=False)
async def custom_redoc_html(request: Request):
    """
    Serve the ReDoc documentation page.
    
    Args:
        request: The request object
        
    Returns:
        The ReDoc HTML page
    """
    # Redirect to our static HTML file
    return RedirectResponse(url="/static/api-docs.html")

# Add root endpoint
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Home page for PyCommerce."""
    # Try to load data for the home page
    cart_item_count = 0
    try:
        cart_id = request.session.get("cart_id")
        if cart_id:
            from pycommerce.models.cart import CartManager
            cart_manager = CartManager()
            cart = cart_manager.get(cart_id)
            if cart and hasattr(cart, 'items'):
                cart_item_count = sum(item.quantity for item in cart.items)
    except Exception as e:
        logger.warning(f"Error getting cart data: {str(e)}")

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "PyCommerce - A Python Ecommerce Platform",
            "cart_item_count": cart_item_count
        }
    )

# Fallback for admin routes
@app.get("/admin")
@app.get("/admin/")
async def admin_redirect():
    """Redirect /admin to /admin/dashboard."""
    logger.info("Redirecting from /admin to /admin/dashboard")
    return RedirectResponse(url="/admin/dashboard")

# Add a health check route specifically for admin dashboard
@app.get("/admin/health")
async def admin_health():
    """Health check specifically for admin routes."""
    return {"status": "ok", "service": "admin", "message": "Admin routes are working"}

# Add a frontend debug route
@app.get("/frontend-debug")
async def frontend_debug(request: Request):
    """Frontend debug endpoint."""
    import os
    import sys

    # Check if templates directory exists
    templates_exist = os.path.exists("templates")
    admin_templates_exist = os.path.exists("templates/admin")

    # Check if static files directory exists
    static_exist = os.path.exists("static")
    css_exist = os.path.exists("static/css")
    js_exist = os.path.exists("static/js")

    # List all template files
    template_files = []
    if templates_exist:
        for root, dirs, files in os.walk("templates"):
            for file in files:
                if file.endswith(".html"):
                    template_files.append(os.path.join(root, file))

    # List all routes in a safe way
    routes_info = []
    for route in app.routes:
        try:
            route_info = {
                "path": getattr(route, "path", "Unknown"),
                "name": getattr(route, "name", None),
                "methods": getattr(route, "methods", []),
            }
            routes_info.append(route_info)
        except Exception as e:
            routes_info.append({"error": f"Error parsing route: {str(e)}"})

    # Check for important middleware
    middleware_types = [str(type(m)) for m in getattr(app, "middleware", [])]

    # Build response
    debug_info = {
        "status": "ok",
        "server_info": {
            "python_version": sys.version,
            "current_directory": os.getcwd(),
            "sys_path": sys.path[:5],  # First 5 elements of sys.path
        },
        "templates_info": {
            "templates_directory_exists": templates_exist,
            "admin_templates_exist": admin_templates_exist,
            "template_files_count": len(template_files),
            "template_files_sample": template_files[:10],  # Limit to 10 files
        },
        "static_files_info": {
            "static_directory_exists": static_exist,
            "css_directory_exists": css_exist,
            "js_directory_exists": js_exist,
            "static_files_list": os.listdir("static") if static_exist else [],
        },
        "routes_count": len(routes_info),
        "routes_sample": routes_info[:15],  # Limit to 15 routes
        "middleware": middleware_types,
    }

    # Return as JSON response with pretty formatting
    return JSONResponse(content=debug_info, status_code=200)

@app.get("/debug/products", response_class=HTMLResponse)
async def debug_products(request: Request):
    """Debug page for products."""
    from pycommerce.models.tenant import TenantManager
    from pycommerce.models.product import ProductManager

    tenant_manager = TenantManager()
    product_manager = ProductManager()

    selected_tenant_slug = "tech"  # Use Tech Gadgets store
    tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)

    # Get products for tenant
    products = product_manager.get_by_tenant(str(tenant_obj.id)) if tenant_obj else []

    # Format products for template
    products_list = []
    for product in products:
        product_dict = {
            "id": str(product.id),
            "name": product.name,
            "description": product.description if hasattr(product, "description") else "",
            "price": product.price,
            "stock": product.stock if hasattr(product, "stock") else 0,
            "sku": product.sku if hasattr(product, "sku") else "",
            "categories": product.categories if hasattr(product, "categories") else [],
            "image_url": product.image_url if hasattr(product, "image_url") else None,
            "tenant_name": tenant_obj.name if tenant_obj else "Unknown"
        }
        products_list.append(product_dict)

    # Create debug html directly
    debug_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Debug Products</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container py-4">
            <h1>Debug Products Page</h1>

            <div class="alert alert-info">
                <h3>Debug Information</h3>
                <p>Tenant: {selected_tenant_slug}</p>
                <p>Products count: {len(products_list)}</p>
            </div>

            <div class="card mt-4">
                <div class="card-header">
                    <h3>All Products</h3>
                </div>
                <div class="card-body">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Name</th>
                                <th>Tenant Name</th>
                                <th>Price</th>
                                <th>Stock</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join([f'''
                            <tr>
                                <td>{p["id"]}</td>
                                <td>{p["name"]}</td>
                                <td>{p["tenant_name"]}</td>
                                <td>${p["price"]}</td>
                                <td>{p["stock"]}</td>
                            </tr>
                            ''' for p in products_list]) if products_list else "<tr><td colspan='5'>No products found</td></tr>"}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=debug_html)

# Template debug route for products
@app.get("/debug/products/template", response_class=HTMLResponse)
async def debug_products_template(request: Request):
    """Debug page for products using the Jinja template."""
    from pycommerce.models.tenant import TenantManager
    from pycommerce.models.product import ProductManager

    tenant_manager = TenantManager()
    product_manager = ProductManager()

    selected_tenant_slug = "tech"  # Use Tech Gadgets store
    tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)

    # Get products for tenant
    products = product_manager.get_by_tenant(str(tenant_obj.id)) if tenant_obj else []

    # Format products for template
    products_list = []
    for product in products:
        product_dict = {
            "id": str(product.id),
            "name": product.name,
            "description": product.description if hasattr(product, "description") else "",
            "price": product.price,
            "stock": product.stock if hasattr(product, "stock") else 0,
            "sku": product.sku if hasattr(product, "sku") else "",
            "categories": product.categories if hasattr(product, "categories") else [],
            "image_url": product.image_url if hasattr(product, "image_url") else None,
            "tenant_name": tenant_obj.name if tenant_obj else "Unknown"
        }
        products_list.append(product_dict)

    # Get all tenants for the store selector
    tenants = []
    try:
        tenants_list = tenant_manager.list() or []
        tenants = [
            {
                "id": str(t.id),
                "name": t.name,
                "slug": t.slug,
                "domain": t.domain if hasattr(t, 'domain') else None,
                "active": t.active if hasattr(t, 'active') else True
            }
            for t in tenants_list if t and hasattr(t, 'id')
        ]
    except Exception as e:
        print(f"Error fetching tenants: {str(e)}")

    # Use the template directly
    context = {
        "request": request,
        "active_page": "products",
        "products": products_list,
        "tenant": tenant_obj,
        "selected_tenant": selected_tenant_slug,
        "tenants": tenants,
        "cart_item_count": request.session.get("cart_item_count", 0)
    }

    return templates.TemplateResponse("admin/products_debug.html", context)

# Direct HTML rendering for products (no template)
@app.get("/debug/products/inline", response_class=HTMLResponse)
async def debug_products_inline(request: Request):
    """Debug page for products with direct HTML output (no template)."""
    from pycommerce.models.tenant import TenantManager
    from pycommerce.models.product import ProductManager

    tenant_manager = TenantManager()
    product_manager = ProductManager()

    selected_tenant_slug = "tech"  # Use Tech Gadgets store
    tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)

    # Get products for tenant
    products = product_manager.get_by_tenant(str(tenant_obj.id)) if tenant_obj else []

    # Format products for HTML
    products_html_rows = ""
    for product in products:
        product_id = str(product.id)
        name = product.name
        description = product.description if hasattr(product, "description") else ""
        price = product.price
        stock = product.stock if hasattr(product, "stock") else 0
        sku = product.sku if hasattr(product, "sku") else ""
        tenant_name = tenant_obj.name if tenant_obj else "Unknown"

        # Create HTML table row for this product
        products_html_rows += f"""
        <tr>
            <td>{product_id}</td>
            <td>{name}</td>
            <td>{tenant_name}</td>
            <td>${price}</td>
            <td>{stock}</td>
            <td>
                <a href="/admin/products/edit/{product_id}" class="btn btn-sm btn-primary">Edit</a>
                <a href="/admin/products/delete/{product_id}" class="btn btn-sm btn-danger" 
                   onclick="return confirm('Are you sure you want to delete this product?')">Delete</a>
            </td>
        </tr>
        """

    # If no products found
    if not products_html_rows:
        products_html_rows = '<tr><td colspan="6" class="text-center">No products found for this tenant</td></tr>'

    # Complete HTML document
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Products Direct HTML</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ padding: 20px; }}
            .navbar {{ margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand" href="/">PyCommerce</a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link" href="/admin/dashboard">Dashboard</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link active" href="/admin/products">Products</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/admin/orders">Orders</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/admin/settings">Settings</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>

        <div class="container">
            <h1>Product Management (Inline HTML)</h1>

            <div class="alert alert-info">
                <h3>Debug Information</h3>
                <p>Tenant: {selected_tenant_slug}</p>
                <p>Products count: {len(products)}</p>
            </div>

            <div class="card mt-4">
                <div class="card-header">
                    <h3>All Products</h3>
                </div>
                <div class="card-body">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Name</th>
                                <th>Tenant</th>
                                <th>Price</th>
                                <th>Stock</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {products_html_rows}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="mt-4">
                <a href="/admin/products/add" class="btn btn-success">Add New Product</a>
                <a href="/admin/dashboard" class="btn btn-secondary">Back to Dashboard</a>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """

    return HTMLResponse(content=html)

    # Add a debug route to check page builder tables
    @app.get("/debug/page-builder-tables", response_class=JSONResponse)
    async def debug_page_builder_tables():
        """Debug endpoint to check if page builder tables exist."""
        from sqlalchemy import inspect
        from pycommerce.core.db import engine

        inspector = inspect(engine)
        all_tables = inspector.get_table_names()

        required_tables = ['pages', 'page_sections', 'content_blocks', 'page_templates']
        tables_status = {table: table in all_tables for table in required_tables}

        # Check counts
        from sqlalchemy import text
        table_counts = {}
        with engine.connect() as conn:
            for table in required_tables:
                if table in all_tables:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    table_counts[table] = result.scalar()
                else:
                    table_counts[table] = 0

        return {
            "tables_exist": tables_status,
            "all_tables": all_tables,
            "record_counts": table_counts
        }