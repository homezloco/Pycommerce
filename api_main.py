"""
FastAPI application for PyCommerce.

This standalone FastAPI application provides access to the e-commerce platform
via a modern REST API.
"""

import os
import logging
from typing import Dict, List, Optional, Any
import uvicorn
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field

import models
from managers import TenantManager, ProductManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="PyCommerce API",
    description="Multi-tenant ecommerce API",
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
    
    class Config:
        orm_mode = True

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
    
    class Config:
        orm_mode = True

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
                        <h3>FastAPI Integration</h3>
                        <p>Modern REST API with async support</p>
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
                                API Documentation
                                <a href="/docs" class="btn btn-sm btn-info">Docs</a>
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

# Sample data creation function
def create_sample_tenant(name: str, slug: str, domain: Optional[str] = None):
    """Create a sample tenant with products."""
    try:
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
        
        # Create sample products for each tenant
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
        "version": "0.1.0",
        "message": "PyCommerce API is running"
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

if __name__ == "__main__":
    uvicorn.run("api_main:app", host="0.0.0.0", port=5000, reload=True)