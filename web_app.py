"""
Main web application for PyCommerce.

This file creates the main FastAPI application using the app factory.
It represents the entry point for uvicorn when running directly.
"""
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the application using the factory
from app_factory import create_app

app, templates = create_app()

# Register store settings test routes
try:
    from routes.admin.store_settings_test import setup_routes
    test_routes_router = setup_routes(templates)
    app.include_router(test_routes_router)
    logger.info("Store settings test routes registered successfully")
except ImportError as e:
    logger.warning(f"Failed to register store settings test routes: {str(e)}")

# Register API routes

# Health check endpoint required by the ASGI-WSGI adapter
@app.get("/api/health")
async def health_check():
    """Health check endpoint that the proxy uses to determine if the app is running."""
    return {"status": "ok", "version": "0.1.0", "message": "PyCommerce API is running"}

@app.get("/health")
async def root_health_check():
    """Alternative health check endpoint."""
    return {"status": "ok", "version": "0.1.0", "message": "PyCommerce API is running"}

try:
    from pycommerce.api.routes import register_api_routes
    register_api_routes(app)
    logger.info("API routes registered successfully")
except ImportError as e:
    logger.warning(f"Failed to register API routes: {str(e)}")

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
    return RedirectResponse(url="/admin/dashboard")

# Debug route for products
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

#app_factory.py
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from database import get_db, db, db
from routes.admin import dashboard, store_settings, products, orders, stores
from routes.admin import categories, users, media, marketing, shipping, plugins
from routes.admin import inventory, settings, analytics, market_analysis, returns
from routes.admin import ai_config, theme_settings, page_builder

def create_app():
    app = FastAPI()
    templates = Jinja2Templates(directory="templates")
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.add_middleware(SessionMiddleware, secret_key="mysecretkey")

    # Register admin routes
    app.include_router(dashboard.setup_routes(templates))
    app.include_router(store_settings.setup_routes(templates))
    app.include_router(products.setup_routes(templates))
    app.include_router(orders.setup_routes(templates))
    app.include_router(stores.setup_routes(templates))
    app.include_router(media.setup_routes(templates))
    app.include_router(categories.setup_routes(templates))
    app.include_router(users.setup_routes(templates))
    app.include_router(marketing.setup_routes(templates))
    app.include_router(shipping.setup_routes(templates))
    app.include_router(plugins.setup_routes(templates))
    app.include_router(inventory.setup_routes(templates))
    app.include_router(settings.setup_routes(templates))
    app.include_router(analytics.setup_routes(templates))
    app.include_router(market_analysis.setup_routes(templates))
    app.include_router(returns.setup_routes(templates))
    app.include_router(ai_config.setup_routes(templates))
    app.include_router(theme_settings.setup_routes(templates))
    # Get the page builder router and include it
    pb_router = page_builder.setup_routes(templates)
    app.include_router(pb_router)
    logger.info("Page builder routes registered successfully")

    return app, templates
"""
Main FastAPI application for PyCommerce.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="PyCommerce API", description="PyCommerce Multi-Tenant E-commerce Platform API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")
