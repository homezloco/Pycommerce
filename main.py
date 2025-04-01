"""
Main entry point for the PyCommerce Platform.

This file creates and initializes a multi-tenant PyCommerce instance
and exposes the FastAPI app via Flask adapter for gunicorn.
"""

import os
import logging
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Flask application
app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        "name": "PyCommerce Platform",
        "version": "1.0.0",
        "description": "Multi-tenant ecommerce platform powered by PyCommerce SDK",
        "api_docs": "/api/docs",
        "api_routes": [
            "/api/health",
            "/api/tenants",
            "/api/products?tenant=<tenant_slug>",
            "/api/generate-sample-data (POST)"
        ]
    })

@app.route('/api/docs')
def api_docs():
    return """
    <html>
        <head>
            <title>PyCommerce API Documentation</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }
                h1 { color: #333; }
                h2 { color: #444; margin-top: 30px; }
                .endpoint { background: #f4f4f4; padding: 10px; border-radius: 4px; margin-bottom: 20px; }
                .method { font-weight: bold; color: #0066cc; }
                .path { font-family: monospace; margin-left: 10px; }
                .description { margin-top: 10px; }
                .params { margin-top: 10px; }
                .param { margin-left: 20px; font-family: monospace; }
            </style>
        </head>
        <body>
            <h1>PyCommerce API Documentation</h1>
            <p>This is the API documentation for the PyCommerce Multi-tenant E-commerce Platform.</p>
            
            <h2>API Endpoints</h2>
            
            <div class="endpoint">
                <div><span class="method">GET</span> <span class="path">/api/health</span></div>
                <div class="description">Check if the API is up and running.</div>
            </div>
            
            <div class="endpoint">
                <div><span class="method">GET</span> <span class="path">/api/tenants</span></div>
                <div class="description">List all tenants in the system.</div>
            </div>
            
            <div class="endpoint">
                <div><span class="method">GET</span> <span class="path">/api/products</span></div>
                <div class="description">List products, optionally filtered by tenant.</div>
                <div class="params">Query Parameters:</div>
                <div class="param">tenant: Tenant slug to filter products by</div>
            </div>
            
            <div class="endpoint">
                <div><span class="method">POST</span> <span class="path">/api/generate-sample-data</span></div>
                <div class="description">Generate sample data for testing (creates tenants and products).</div>
            </div>
        </body>
    </html>
    """

@app.route('/api/health')
def health_check():
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "message": "PyCommerce Platform is running. Visit /docs for API documentation."
    })

# Initialize PyCommerce SDK (just for data access)
from pycommerce.core.db import init_db
from pycommerce.core.migrations import init_migrations
from pycommerce.models.tenant import TenantManager
from pycommerce.models.product import ProductManager
import uuid

# Initialize the database
init_db()

# Initialize migrations
try:
    init_migrations()
except Exception as e:
    logger.warning(f"Error initializing migrations: {str(e)}")

# Initialize managers
tenant_manager = TenantManager()
product_manager = ProductManager()

@app.route('/api/products')
def get_products():
    tenant_slug = request.args.get('tenant', 'default')
    tenant = None
    
    # Extract filter parameters
    category = request.args.get('category')
    min_price = request.args.get('min_price')
    if min_price is not None:
        try:
            min_price = float(min_price)
        except ValueError:
            min_price = None
    
    max_price = request.args.get('max_price')
    if max_price is not None:
        try:
            max_price = float(max_price)
        except ValueError:
            max_price = None
    
    in_stock = request.args.get('in_stock')
    if in_stock is not None:
        in_stock = in_stock.lower() in ('true', '1', 'yes')
    
    try:
        # Try to get tenant by slug
        tenant = tenant_manager.get_by_slug(tenant_slug)
    except Exception as e:
        # Handle case where tenant doesn't exist
        logger.warning(f"Tenant not found with slug '{tenant_slug}': {str(e)}")
    
    products_list = []
    if tenant and hasattr(tenant, 'id'):
        try:
            # Get all products and filter by tenant 
            # (We don't have tenant_id parameter in product_manager.list())
            all_products = product_manager.list(
                category=category,
                min_price=min_price,
                max_price=max_price,
                in_stock=in_stock
            )
            
            # Filter products by tenant_id from metadata
            tenant_products = []
            for p in all_products:
                if hasattr(p, 'metadata') and p.metadata.get('tenant_id') == str(tenant.id):
                    tenant_products.append(p)
                
            if tenant_products:
                products_list = [
                    {
                        "id": str(p.id) if p and hasattr(p, 'id') else None,
                        "name": p.name if p and hasattr(p, 'name') else 'Unnamed Product',
                        "description": p.description if p and hasattr(p, 'description') else None,
                        "price": p.price if p and hasattr(p, 'price') else 0.0,
                        "sku": p.sku if p and hasattr(p, 'sku') else None,
                        "stock": p.stock if p and hasattr(p, 'stock') else 0,
                        "categories": p.categories if p and hasattr(p, 'categories') else []
                    }
                    for p in tenant_products if p
                ]
        except Exception as e:
            logger.error(f"Error fetching products: {str(e)}")
    
    # Return products (empty list if tenant not found or error)
    return jsonify({
        "products": products_list, 
        "tenant": tenant_slug,
        "count": len(products_list),
        "filters": {
            "category": category,
            "min_price": min_price,
            "max_price": max_price,
            "in_stock": in_stock
        }
    })

@app.route('/api/tenants')
def get_tenants():
    try:
        tenants = tenant_manager.list()
        tenants_list = []
        
        if tenants:
            for t in tenants:
                if t and hasattr(t, 'id'):
                    tenant_dict = {
                        "id": str(t.id),
                        "name": t.name if hasattr(t, 'name') else 'Unnamed Tenant',
                        "slug": t.slug if hasattr(t, 'slug') else None,
                        "domain": t.domain if hasattr(t, 'domain') else None,
                        "active": t.active if hasattr(t, 'active') else True
                    }
                    tenants_list.append(tenant_dict)
        
        return jsonify({"tenants": tenants_list, "count": len(tenants_list)})
    except Exception as e:
        logger.error(f"Error fetching tenants: {str(e)}")
        return jsonify({"tenants": [], "count": 0, "error": str(e)})

@app.route('/api/generate-sample-data', methods=['POST'])
def generate_sample_data():
    """Generate sample data for testing."""
    try:
        created_tenants = []
        created_products = []
        
        # Check if tenants already exist - don't duplicate them
        try:
            existing_tenants = tenant_manager.list() or []
            existing_slugs = [t.slug for t in existing_tenants if t and hasattr(t, 'slug')] 
            
            # If we already have demo tenants, return them instead of creating duplicates
            if 'demo1' in existing_slugs and 'demo2' in existing_slugs:
                tenant1 = next((t for t in existing_tenants if t.slug == 'demo1'), None)
                tenant2 = next((t for t in existing_tenants if t.slug == 'demo2'), None)
                
                return jsonify({
                    "success": True,
                    "message": "Sample data already exists",
                    "tenants": [
                        {"id": str(t.id), "name": t.name, "slug": t.slug}
                        for t in [tenant1, tenant2] if t
                    ]
                })
        except Exception as e:
            logger.warning(f"Error checking existing tenants: {str(e)}")
        
        # Create tenants
        tenant1 = None
        tenant2 = None
        
        if 'demo1' not in existing_slugs:
            try:
                tenant1 = tenant_manager.create(
                    name="Demo Store 1",
                    slug="demo1",
                    domain="demo1.pycommerce.example"
                )
                created_tenants.append(tenant1)
                logger.info(f"Created tenant: {tenant1.name}")
            except Exception as e:
                logger.error(f"Error creating tenant 'demo1': {str(e)}")
        
        if 'demo2' not in existing_slugs:
            try:
                tenant2 = tenant_manager.create(
                    name="Demo Store 2",
                    slug="demo2",
                    domain="demo2.pycommerce.example"
                )
                created_tenants.append(tenant2)
                logger.info(f"Created tenant: {tenant2.name}")
            except Exception as e:
                logger.error(f"Error creating tenant 'demo2': {str(e)}")
        
        # Create products for tenant 1
        if tenant1 and hasattr(tenant1, 'id'):
            for i in range(1, 6):
                try:
                    # Store tenant_id in metadata to associate with tenant
                    metadata = {"tenant_id": str(tenant1.id)}
                    categories = ["demo", f"price-tier-{i}", "store1"]
                    
                    product = product_manager.create({
                        "name": f"Product {i} for Demo Store 1",
                        "description": f"This is product {i} for tenant 1",
                        "price": 10.0 * i,
                        "sku": f"DEMO1-PROD-{i}",
                        "stock": 100,
                        "metadata": metadata,
                        "categories": categories
                    })
                    created_products.append(product)
                    logger.info(f"Created product for tenant1: {product.name}")
                except Exception as e:
                    logger.error(f"Error creating product for tenant1: {str(e)}")
            
        # Create products for tenant 2
        if tenant2 and hasattr(tenant2, 'id'):
            for i in range(1, 6):
                try:
                    # Store tenant_id in metadata to associate with tenant
                    metadata = {"tenant_id": str(tenant2.id)}
                    categories = ["demo", f"price-tier-{i}", "store2", "premium"]
                    
                    product = product_manager.create({
                        "name": f"Product {i} for Demo Store 2",
                        "description": f"This is product {i} for tenant 2",
                        "price": 20.0 * i,
                        "sku": f"DEMO2-PROD-{i}",
                        "stock": 100,
                        "metadata": metadata,
                        "categories": categories
                    })
                    created_products.append(product)
                    logger.info(f"Created product for tenant2: {product.name}")
                except Exception as e:
                    logger.error(f"Error creating product for tenant2: {str(e)}")
        
        # Get the final list of tenants (created or found)
        tenant_list = []
        if not tenant1 and 'demo1' in existing_slugs:
            tenant1 = next((t for t in existing_tenants if t.slug == 'demo1'), None)
        if not tenant2 and 'demo2' in existing_slugs:
            tenant2 = next((t for t in existing_tenants if t.slug == 'demo2'), None)
        
        if tenant1 and hasattr(tenant1, 'id'):
            tenant_list.append({"id": str(tenant1.id), "name": tenant1.name, "slug": tenant1.slug})
        if tenant2 and hasattr(tenant2, 'id'):
            tenant_list.append({"id": str(tenant2.id), "name": tenant2.name, "slug": tenant2.slug})
            
        return jsonify({
            "success": True,
            "message": f"Sample data generated successfully. Created {len(created_tenants)} tenants and {len(created_products)} products.",
            "tenants": tenant_list
        })
    except Exception as e:
        logger.error(f"Error generating sample data: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)