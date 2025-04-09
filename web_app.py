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

# Add health endpoint required by the ASGI-WSGI adapter
@app.get("/api/health")
async def health_check():
    """Health check endpoint that the proxy uses to determine if the app is running."""
    return JSONResponse({
        "status": "ok",
        "version": "0.1.0",
        "message": "PyCommerce API is running"
    })

# Add root endpoint
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Home page for PyCommerce."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "PyCommerce - A Python Ecommerce Platform",
            "cart_item_count": request.session.get("cart_item_count", 0)
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