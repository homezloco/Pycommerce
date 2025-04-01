"""
Web server with FastAPI and Jinja2 templates for PyCommerce.

This file provides a web interface for the PyCommerce platform using FastAPI
and HTML templates.
"""

import os
import logging
import uvicorn
from fastapi import FastAPI, Depends, Query, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional, List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize PyCommerce SDK
from pycommerce.core.db import init_db
from pycommerce.core.migrations import init_migrations
from pycommerce.models.tenant import TenantManager
from pycommerce.models.product import ProductManager
from pycommerce.models.user import UserManager
from pycommerce.api.routes import products as products_router
from pycommerce.api.routes import cart as cart_router
from pycommerce.api.routes import checkout as checkout_router
from pycommerce.api.routes import users as users_router

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
user_manager = UserManager()

# Create the FastAPI app
app = FastAPI(
    title="PyCommerce Web",
    description="Web interface for PyCommerce Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Setup user manager in the routes
users_router.set_user_manager(user_manager)

# Include API routes
app.include_router(products_router.router, prefix="/api/products", tags=["products"])
app.include_router(cart_router.router, prefix="/api/cart", tags=["cart"])
app.include_router(checkout_router.router, prefix="/api/checkout", tags=["checkout"])
app.include_router(users_router.router, prefix="/api/users", tags=["users"])

# Set up templates
templates = Jinja2Templates(directory="templates")

# Endpoints for HTML templates
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html", 
        {"request": request}
    )

@app.get("/stores", response_class=HTMLResponse)
async def stores(request: Request):
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
        logger.error(f"Error fetching tenants: {str(e)}")
    
    return templates.TemplateResponse(
        "stores.html", 
        {"request": request, "tenants": tenants}
    )

@app.get("/products", response_class=HTMLResponse)
async def products(
    request: Request,
    tenant: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None
):
    # Get all tenants for the dropdown
    tenants = []
    try:
        tenants_list = tenant_manager.list() or []
        tenants = [
            {
                "id": str(t.id),
                "name": t.name,
                "slug": t.slug
            }
            for t in tenants_list if t and hasattr(t, 'id')
        ]
    except Exception as e:
        logger.error(f"Error fetching tenants: {str(e)}")
    
    # Get filtered products
    products_list = []
    tenant_obj = None
    
    if tenant:
        # Try to get tenant by slug
        try:
            tenant_obj = tenant_manager.get_by_slug(tenant)
        except Exception as e:
            logger.warning(f"Tenant not found with slug '{tenant}': {str(e)}")
    
    try:
        # Get all products with filters
        all_products = product_manager.list(
            category=category,
            min_price=min_price,
            max_price=max_price,
            in_stock=in_stock
        )
        
        # Filter by tenant if specified
        if tenant_obj and hasattr(tenant_obj, 'id'):
            tenant_products = []
            for p in all_products:
                if hasattr(p, 'metadata') and p.metadata.get('tenant_id') == str(tenant_obj.id):
                    tenant_products.append(p)
            products_to_show = tenant_products
        else:
            products_to_show = all_products
        
        # Format products for template
        if products_to_show:
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
                for p in products_to_show if p
            ]
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
    
    # Prepare filter values for the template
    filters = {
        "category": category,
        "min_price": min_price,
        "max_price": max_price,
        "in_stock": in_stock
    }
    
    return templates.TemplateResponse(
        "products.html", 
        {
            "request": request, 
            "products": products_list,
            "tenants": tenants,
            "selected_tenant": tenant,
            "filters": filters
        }
    )

@app.get("/store/{slug}", response_class=HTMLResponse)
async def store(
    request: Request,
    slug: str,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None
):
    tenant_obj = None
    try:
        tenant_obj = tenant_manager.get_by_slug(slug)
    except Exception as e:
        logger.warning(f"Tenant not found with slug '{slug}': {str(e)}")
        # Redirect to stores page if tenant not found
        return RedirectResponse(url="/stores")
    
    tenant_data = {
        "id": str(tenant_obj.id),
        "name": tenant_obj.name,
        "slug": tenant_obj.slug,
        "domain": tenant_obj.domain if hasattr(tenant_obj, 'domain') else None
    }
    
    # Get products for this tenant
    products_list = []
    try:
        # Get all products with filters
        all_products = product_manager.list(
            category=category,
            min_price=min_price,
            max_price=max_price,
            in_stock=in_stock
        )
        
        # Filter by tenant
        tenant_products = []
        for p in all_products:
            if hasattr(p, 'metadata') and p.metadata.get('tenant_id') == str(tenant_obj.id):
                tenant_products.append(p)
        
        # Format products for template
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
    
    # Prepare filter values for the template
    filters = {
        "category": category,
        "min_price": min_price,
        "max_price": max_price,
        "in_stock": in_stock
    }
    
    return templates.TemplateResponse(
        "store/index.html", 
        {
            "request": request, 
            "tenant": tenant_data,
            "products": products_list,
            "filters": filters
        }
    )

# API endpoint to generate sample data
@app.get("/api/generate-sample-data")
async def generate_sample_data():
    try:
        created_tenants = []
        created_products = []
        
        # Check if tenants already exist - don't duplicate them
        try:
            existing_tenants = tenant_manager.list() or []
            existing_slugs = [t.slug for t in existing_tenants if t and hasattr(t, 'slug')] 
            
            # If we already have demo tenants, return them instead of creating duplicates
            if 'demo1' in existing_slugs and 'demo2' in existing_slugs:
                return RedirectResponse(url="/stores")
        except Exception as e:
            logger.warning(f"Error checking existing tenants: {str(e)}")
            existing_slugs = []
        
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
        
        return RedirectResponse(url="/stores")
    except Exception as e:
        logger.error(f"Error generating sample data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# API health check
@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "message": "PyCommerce Platform is running with FastAPI and uvicorn."
    }

if __name__ == "__main__":
    uvicorn.run("web_server:app", host="0.0.0.0", port=5000, reload=True)