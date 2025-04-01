"""
FastAPI wrapper for PyCommerce platform.

This module provides a FastAPI application with endpoints for the PyCommerce platform.
"""

import os
import sys
import logging
import inspect
import fastapi
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse, HTMLResponse
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

from pycommerce import PyCommerce
from pycommerce.models.tenant import TenantManager
from pycommerce.models.product import ProductManager
from pycommerce.models.cart import CartManager
from pycommerce.models.order import OrderManager
from pycommerce.models.user import UserManager
from pycommerce.plugins.payment.stripe import StripePaymentPlugin
from pycommerce.plugins.shipping.standard import StandardShippingPlugin
from prestart import setup_database
from initialize_db import initialize_database, create_sample_tenant

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create and initialize PyCommerce instance
pycommerce = PyCommerce(name="PyCommerce Platform")

# Set up database and migrations
setup_database()

# Register plugins
pycommerce.register_plugin(StripePaymentPlugin())
pycommerce.register_plugin(StandardShippingPlugin())

# Create FastAPI app
app = FastAPI(
    title="PyCommerce API",
    description="Multi-tenant ecommerce API powered by PyCommerce",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API response models
class TenantResponse(BaseModel):
    id: str
    name: str
    slug: str
    domain: Optional[str] = None
    active: bool = True

class TenantsResponse(BaseModel):
    tenants: List[TenantResponse]
    count: int

class ProductResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    price: float
    sku: str
    stock: int = 0
    categories: List[str] = Field(default_factory=list)

class ProductsResponse(BaseModel):
    products: List[ProductResponse]
    tenant: str
    count: int
    filters: Dict[str, Any]

class SampleDataResponse(BaseModel):
    success: bool
    message: str
    tenants: List[Dict[str, str]]

class HealthResponse(BaseModel):
    status: str
    version: str
    message: str

# HTML template for the home page
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PyCommerce Platform</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .header { padding: 2rem 1rem; background-color: #f8f9fa; }
        .feature-icon { font-size: 2rem; color: #0d6efd; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header text-center mb-5">
            <h1>PyCommerce Platform</h1>
            <p class="lead">A modular Python ecommerce SDK with plugin architecture</p>
        </div>
        
        <div class="row mb-5">
            <div class="col-md-4">
                <div class="card mb-4">
                    <div class="card-body text-center">
                        <div class="feature-icon mb-3">🛍️</div>
                        <h3>Multi-tenant</h3>
                        <p>Support for multiple stores with data isolation</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card mb-4">
                    <div class="card-body text-center">
                        <div class="feature-icon mb-3">🔌</div>
                        <h3>Plugin Architecture</h3>
                        <p>Extensible with payment and shipping plugins</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card mb-4">
                    <div class="card-body text-center">
                        <div class="feature-icon mb-3">⚡</div>
                        <h3>FastAPI Integration</h3>
                        <p>Modern REST API with async support</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mb-5">
            <div class="col-md-6 mx-auto">
                <div class="card">
                    <div class="card-header">
                        <h3>Demo API Links</h3>
                    </div>
                    <div class="card-body">
                        <ul class="list-group list-group-flush">
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Health Check
                                <a href="/health" class="btn btn-sm btn-primary">View</a>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                All Tenants
                                <a href="/tenants" class="btn btn-sm btn-primary">View</a>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Products (Default Tenant)
                                <a href="/products?tenant=default" class="btn btn-sm btn-primary">View</a>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Generate Sample Data
                                <a href="/generate-sample-data" class="btn btn-sm btn-success">Create</a>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                API Documentation
                                <a href="/docs" class="btn btn-sm btn-info">Docs</a>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <footer class="bg-light py-4">
        <div class="container text-center">
            <p>PyCommerce Platform &copy; 2025</p>
        </div>
    </footer>
</body>
</html>
"""

# API Routes

@app.get("/", include_in_schema=False)
async def index():
    """Home page with links to API endpoints."""
    return HTMLResponse(content=HOME_TEMPLATE)

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check if the API is running."""
    return {
        "status": "ok",
        "version": pycommerce.version,
        "message": f"PyCommerce API is running: {pycommerce.name}"
    }

@app.get("/products", response_model=ProductsResponse, tags=["Products"])
async def get_products(
    tenant: str = Query("default", description="Tenant slug"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock availability")
):
    """
    Get products for a tenant with optional filtering.
    
    Args:
        tenant: The tenant slug
        category: Filter products by category
        min_price: Filter products by minimum price
        max_price: Filter products by maximum price
        in_stock: Filter products that are in stock
    """
    tenant_manager = TenantManager()
    product_manager = ProductManager()
    
    # Get tenant ID from slug
    tenant_obj = tenant_manager.get_tenant_by_slug(tenant)
    if not tenant_obj:
        raise HTTPException(
            status_code=404, detail=f"Tenant not found: {tenant}"
        )

    # Build filters
    filters = {}
    if category:
        filters["category"] = category
    if min_price is not None:
        filters["min_price"] = min_price
    if max_price is not None:
        filters["max_price"] = max_price
    if in_stock is not None:
        filters["in_stock"] = in_stock
    
    # Get products with filters
    products = product_manager.get_products_by_tenant(tenant_obj.id, filters)
    
    return {
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
        "tenant": tenant,
        "count": len(products),
        "filters": filters
    }

@app.get("/tenants", response_model=TenantsResponse, tags=["Tenants"])
async def get_tenants():
    """Get all tenants."""
    tenant_manager = TenantManager()
    tenants = tenant_manager.get_all_tenants()
    
    return {
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
    }

@app.get("/generate-sample-data", response_model=SampleDataResponse, tags=["System"])
async def generate_sample_data():
    """Generate sample data for testing."""
    tenant_manager = TenantManager()
    product_manager = ProductManager()
    
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
    
    return {
        "success": True,
        "message": "Sample data generated successfully" if len(existing_tenants) == 0 else "Sample data already exists",
        "tenants": result_tenants
    }

# Special case for favicon
@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    """Serve favicon."""
    try:
        return FileResponse('generated-icon.png')
    except:
        raise HTTPException(status_code=404, detail="Favicon not found")