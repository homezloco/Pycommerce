"""
Flask application for PyCommerce.

This standalone Flask application provides access to PyCommerce features.
It can be run directly without needing to proxy to a FastAPI server.
"""

import os
import logging
import threading
import time
from flask import Flask, render_template_string, jsonify, request, redirect, url_for
from database import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "pycommerce-dev-key")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

# Initialize database
with app.app_context():
    # Import models to create tables
    import models
    
    db.create_all()

# Register blueprints
from order_routes import order_routes
app.register_blueprint(order_routes)

# Register shipping and reports routes
from routes.admin.shipping import shipping_bp
from routes.admin.reports import reports_bp
app.register_blueprint(shipping_bp)
app.register_blueprint(reports_bp)

# HTML template for the home page
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PyCommerce Platform</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <style>
        .header { padding: 2rem 1rem; }
        .feature-icon { font-size: 2rem; color: var(--bs-info); }
    </style>
</head>
<body>
    <div class="container my-4">
        <div class="header text-center mb-5 rounded bg-dark">
            <h1 class="display-4">PyCommerce Platform</h1>
            <p class="lead">A modular Python ecommerce SDK with plugin architecture</p>
        </div>
        
        <div class="row mb-5">
            <div class="col-md-4">
                <div class="card mb-4 h-100">
                    <div class="card-body text-center">
                        <div class="feature-icon mb-3">🛍️</div>
                        <h3>Multi-tenant</h3>
                        <p>Support for multiple stores with data isolation</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card mb-4 h-100">
                    <div class="card-body text-center">
                        <div class="feature-icon mb-3">🔌</div>
                        <h3>Plugin Architecture</h3>
                        <p>Extensible with payment and shipping plugins</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card mb-4 h-100">
                    <div class="card-body text-center">
                        <div class="feature-icon mb-3">⚡</div>
                        <h3>API Integration</h3>
                        <p>Modern REST API with Flask support</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mb-5">
            <div class="col-md-6 mx-auto">
                <div class="card">
                    <div class="card-header bg-dark">
                        <h3>Demo API Links</h3>
                    </div>
                    <div class="card-body">
                        <ul class="list-group list-group-flush">
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Health Check
                                <a href="/health" class="btn btn-sm btn-info">View</a>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                All Tenants
                                <a href="/tenants" class="btn btn-sm btn-info">View</a>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Products (Default Tenant)
                                <a href="/products?tenant=default" class="btn btn-sm btn-info">View</a>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Generate Sample Data
                                <a href="/generate-sample-data" class="btn btn-sm btn-success">Create</a>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Order Management
                                <a href="/admin/orders" class="btn btn-sm btn-primary">View</a>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Inventory Management
                                <a href="/admin/inventory" class="btn btn-sm btn-primary">View</a>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <footer class="py-4 text-center">
        <div class="container">
            <p>PyCommerce Platform &copy; 2025</p>
        </div>
    </footer>
</body>
</html>
"""

# Sample data creation
def create_sample_tenant(name, slug, domain=None):
    """Create a sample tenant with products."""
    try:
        from managers import TenantManager, ProductManager
        tenant_manager = TenantManager()
        
        # Create tenant
        tenant = tenant_manager.create_tenant(name=name, slug=slug, domain=domain)
        
        # Create sample products for this tenant
        product_manager = ProductManager()
        categories = {
            "fashion": ["Clothing", "Shoes", "Accessories"],
            "electronics": ["Computers", "Phones", "Gadgets"],
            "home": ["Furniture", "Kitchen", "Decor"]
        }
        
        tenant_categories = categories.get(slug, ["General", "Featured", "Sale"])
        
        # Create 5-10 sample products for each tenant
        products_data = [
            {
                "name": f"{name} Product {i}",
                "description": f"This is a sample product for {name}",
                "price": (i * 10) + 9.99,
                "sku": f"{slug}-prod-{i:03d}",
                "stock": i * 5,
                "categories": [tenant_categories[i % len(tenant_categories)]]
            }
            for i in range(1, 8)  # 7 products per tenant
        ]
        
        for product_data in products_data:
            product_manager.create_product(
                tenant_id=tenant.id,
                name=product_data["name"],
                description=product_data["description"],
                price=product_data["price"],
                sku=product_data["sku"],
                stock=product_data["stock"],
                categories=product_data["categories"]
            )
        
        return tenant
    except Exception as e:
        logger.error(f"Error creating sample tenant: {e}")
        return None

# Routes
@app.route('/')
def index():
    """Home page showing PyCommerce info and links."""
    return render_template_string(HOME_TEMPLATE)

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "version": "0.1.0",
        "message": "PyCommerce Flask application is running"
    })

@app.route('/tenants')
def tenants():
    """Get all tenants."""
    from managers import TenantManager
    tenant_manager = TenantManager()
    tenants = tenant_manager.get_all_tenants()
    
    return jsonify({
        "tenants": [
            {
                "id": t.id,
                "name": t.name,
                "slug": t.slug,
                "domain": t.domain,
                "active": t.active,
            }
            for t in tenants
        ],
        "count": len(tenants)
    })

@app.route('/products')
def products():
    """Get products for a tenant with optional filtering."""
    from managers import TenantManager, ProductManager
    tenant_manager = TenantManager()
    product_manager = ProductManager()
    
    # Get query parameters
    tenant_slug = request.args.get("tenant", "default")
    category = request.args.get("category")
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")
    in_stock = request.args.get("in_stock")
    
    # Get tenant ID from slug
    tenant = tenant_manager.get_tenant_by_slug(tenant_slug)
    if not tenant:
        return jsonify({"error": f"Tenant not found: {tenant_slug}"}), 404

    # Build filters
    filters = {}
    if category:
        filters["category"] = category
    if min_price:
        filters["min_price"] = float(min_price)
    if max_price:
        filters["max_price"] = float(max_price)
    if in_stock:
        filters["in_stock"] = in_stock.lower() == "true"
    
    # Get products with filters
    products = product_manager.get_products_by_tenant(tenant.id, filters)
    
    return jsonify({
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "sku": p.sku,
                "stock": p.stock,
                "categories": p.categories,
            }
            for p in products
        ],
        "tenant": tenant_slug,
        "count": len(products),
        "filters": filters
    })

@app.route('/generate-sample-data')
def generate_sample_data():
    """Generate sample data for testing."""
    from managers import TenantManager
    tenant_manager = TenantManager()
    
    # Check if we already have sample tenants
    existing_tenants = tenant_manager.get_all_tenants()
    result_tenants = []
    
    if len(existing_tenants) == 0:
        # Create sample tenants
        tenants_data = [
            ("Fashion Store", "fashion", "fashion.example.com"),
            ("Electronics Shop", "electronics", "electronics.example.com"),
            ("Home Goods", "home", "home.example.com")
        ]
        
        for name, slug, domain in tenants_data:
            tenant = create_sample_tenant(name, slug, domain)
            if tenant:
                result_tenants.append({
                    "name": name, 
                    "slug": slug, 
                    "id": tenant.id
                })
    else:
        for tenant in existing_tenants:
            result_tenants.append({
                "name": tenant.name, 
                "slug": tenant.slug, 
                "id": tenant.id
            })
    
    return jsonify({
        "success": True,
        "message": "Sample data generated successfully" if len(existing_tenants) == 0 else "Sample data already exists",
        "tenants": result_tenants
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)