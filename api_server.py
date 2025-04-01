"""
FastAPI server for PyCommerce.

This file is specifically designed to run with uvicorn.
"""

import os
import logging
import uvicorn
from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from pycommerce.core.base import PyCommerce

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize PyCommerce SDK
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

# Create the FastAPI app
app = FastAPI(
    title="PyCommerce Platform",
    description="Multi-tenant ecommerce platform powered by PyCommerce SDK",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
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

@app.get("/", response_class=JSONResponse)
async def index():
    return {
        "name": "PyCommerce Platform",
        "version": "1.0.0",
        "description": "Multi-tenant ecommerce platform powered by PyCommerce SDK",
        "api_docs": "/docs",
        "api_routes": [
            "/api/health",
            "/api/tenants",
            "/api/products?tenant=<tenant_slug>",
            "/api/generate-sample-data (POST)"
        ]
    }

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "message": "PyCommerce Platform is running. Visit /docs for API documentation."
    }

@app.get("/api/products", response_model=ProductsResponse)
async def get_products(
    tenant: str = Query("default", description="Tenant slug"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock availability")
):
    tenant_obj = None
    
    try:
        # Try to get tenant by slug
        tenant_obj = tenant_manager.get_by_slug(tenant)
    except Exception as e:
        # Handle case where tenant doesn't exist
        logger.warning(f"Tenant not found with slug '{tenant}': {str(e)}")
    
    products_list = []
    if tenant_obj and hasattr(tenant_obj, 'id'):
        try:
            # Get all products and filter by tenant
            all_products = product_manager.list(
                category=category,
                min_price=min_price,
                max_price=max_price,
                in_stock=in_stock
            )
            
            # Filter products by tenant_id from metadata
            tenant_products = []
            for p in all_products:
                if hasattr(p, 'metadata') and p.metadata.get('tenant_id') == str(tenant_obj.id):
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
    return {
        "products": products_list, 
        "tenant": tenant,
        "count": len(products_list),
        "filters": {
            "category": category,
            "min_price": min_price,
            "max_price": max_price,
            "in_stock": in_stock
        }
    }

@app.get("/api/tenants", response_model=TenantsResponse)
async def get_tenants():
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
        
        return {"tenants": tenants_list, "count": len(tenants_list)}
    except Exception as e:
        logger.error(f"Error fetching tenants: {str(e)}")
        return {"tenants": [], "count": 0}

@app.post("/api/generate-sample-data", response_model=SampleDataResponse)
async def generate_sample_data():
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
                
                return {
                    "success": True,
                    "message": "Sample data already exists",
                    "tenants": [
                        {"id": str(t.id), "name": t.name, "slug": t.slug}
                        for t in [tenant1, tenant2] if t
                    ]
                }
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
            
        return {
            "success": True,
            "message": f"Sample data generated successfully. Created {len(created_tenants)} tenants and {len(created_products)} products.",
            "tenants": tenant_list
        }
    except Exception as e:
        logger.error(f"Error generating sample data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=5000, reload=True)