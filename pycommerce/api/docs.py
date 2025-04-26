"""
API Documentation Integration for PyCommerce.

This module provides enhanced OpenAPI documentation integration for the PyCommerce API,
including interactive documentation with Swagger UI and ReDoc, comprehensive schema
definitions, and code examples.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles

# Import schemas for documentation
try:
    from pycommerce.api.schemas import (
        HealthCheck, Tenant, TenantList, Product, ProductList,
        Category, CategoryList, Order, OrderList, User, UserList,
        Media, MediaList, Page, PageList, PageTemplate, PageTemplateList,
        PaymentMethod, ShippingMethod, Estimate, EstimateList, Token
    )
    SCHEMAS_AVAILABLE = True
except ImportError:
    SCHEMAS_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create documentation router
docs_router = APIRouter(prefix="/api", tags=["API Documentation"])

# Documentation routes
@docs_router.get("/docs", response_class=HTMLResponse, include_in_schema=False)
async def custom_swagger_ui_html(request: Request):
    """
    Serve the enhanced Swagger UI documentation page.
    
    This endpoint provides an interactive API documentation interface using Swagger UI,
    with custom styling and branding for PyCommerce.
    
    Args:
        request: The request object
        
    Returns:
        The Swagger UI HTML page
    """
    root_path = request.scope.get("root_path", "").rstrip("/")
    openapi_url = f"{root_path}/api/openapi.json"
    
    return get_swagger_ui_html(
        openapi_url=openapi_url,
        title="PyCommerce API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui.css",
        swagger_favicon_url=f"{root_path}/static/favicon.ico" if os.path.exists("static/favicon.ico") else None,
        swagger_ui_parameters={
            "docExpansion": "none",
            "defaultModelsExpandDepth": 0,
            "deepLinking": True,
            "persistAuthorization": True,
            "syntaxHighlight.theme": "monokai",
            "filter": True
        }
    )

@docs_router.get("/redoc", response_class=HTMLResponse, include_in_schema=False)
async def custom_redoc_html(request: Request):
    """
    Serve the enhanced ReDoc documentation page.
    
    This endpoint provides a more readable API documentation interface using ReDoc,
    with custom styling and branding for PyCommerce.
    
    Args:
        request: The request object
        
    Returns:
        The ReDoc HTML page
    """
    root_path = request.scope.get("root_path", "").rstrip("/")
    openapi_url = f"{root_path}/api/openapi.json"
    
    return get_redoc_html(
        openapi_url=openapi_url,
        title="PyCommerce API Documentation - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
        redoc_favicon_url=f"{root_path}/static/favicon.ico" if os.path.exists("static/favicon.ico") else None,
        with_google_fonts=True
    )

@docs_router.get("/documentation", response_class=JSONResponse, include_in_schema=False)
async def api_documentation_links(request: Request):
    """
    Return links to API documentation resources.
    
    This endpoint provides a convenient JSON listing of all available
    documentation resources for the PyCommerce API.
    
    Args:
        request: The request object
        
    Returns:
        JSON object with documentation links
    """
    root_path = request.scope.get("root_path", "").rstrip("/")
    
    return {
        "message": "PyCommerce API Documentation",
        "version": "1.0.0",
        "documentation_links": {
            "swagger": f"{root_path}/api/docs",
            "redoc": f"{root_path}/api/redoc",
            "openapi_json": f"{root_path}/api/openapi.json",
            "schema_overview": f"{root_path}/api/schema-overview",
            "postman_collection": f"{root_path}/api/postman-collection"
        },
        "code_examples": {
            "python": f"{root_path}/api/examples/python",
            "javascript": f"{root_path}/api/examples/javascript",
            "curl": f"{root_path}/api/examples/curl"
        }
    }

@docs_router.get("/schema-overview", response_class=HTMLResponse, include_in_schema=False)
async def schema_overview(request: Request):
    """
    Provide a high-level overview of the API schema.
    
    This endpoint renders a custom HTML page showing the relationships
    between different API resources and their schemas.
    
    Args:
        request: The request object
        
    Returns:
        HTML page with schema overview
    """
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PyCommerce API Schema Overview</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { padding: 2rem; }
            .resource-card { margin-bottom: 1rem; }
            .schema-item { padding: 0.5rem; border-bottom: 1px solid #eee; }
            h1, h2, h3 { margin-bottom: 1rem; }
            .relationship-diagram { max-width: 100%; height: auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>PyCommerce API Schema Overview</h1>
            <p class="lead">This page provides a high-level overview of the PyCommerce API schema and resource relationships.</p>
            
            <h2 class="mt-4">Core Resources</h2>
            <div class="row">
                <div class="col-md-4">
                    <div class="card resource-card">
                        <div class="card-header bg-primary text-white">
                            <h5 class="card-title mb-0">Tenants</h5>
                        </div>
                        <div class="card-body">
                            <p>The foundation of multi-tenancy in PyCommerce. Each tenant represents a separate store or business.</p>
                            <div class="schema-item"><strong>id</strong>: string (UUID)</div>
                            <div class="schema-item"><strong>name</strong>: string</div>
                            <div class="schema-item"><strong>slug</strong>: string</div>
                            <div class="schema-item"><strong>domain</strong>: string (optional)</div>
                            <div class="schema-item"><strong>settings</strong>: object</div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card resource-card">
                        <div class="card-header bg-success text-white">
                            <h5 class="card-title mb-0">Products</h5>
                        </div>
                        <div class="card-body">
                            <p>Products offered for sale by tenants.</p>
                            <div class="schema-item"><strong>id</strong>: string (UUID)</div>
                            <div class="schema-item"><strong>tenant_id</strong>: string (UUID)</div>
                            <div class="schema-item"><strong>name</strong>: string</div>
                            <div class="schema-item"><strong>price</strong>: number</div>
                            <div class="schema-item"><strong>sku</strong>: string</div>
                            <div class="schema-item"><strong>categories</strong>: array</div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card resource-card">
                        <div class="card-header bg-info text-white">
                            <h5 class="card-title mb-0">Orders</h5>
                        </div>
                        <div class="card-body">
                            <p>Customer orders containing products.</p>
                            <div class="schema-item"><strong>id</strong>: string (UUID)</div>
                            <div class="schema-item"><strong>tenant_id</strong>: string (UUID)</div>
                            <div class="schema-item"><strong>status</strong>: string</div>
                            <div class="schema-item"><strong>total</strong>: number</div>
                            <div class="schema-item"><strong>items</strong>: array</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <h2 class="mt-4">Resource Relationships</h2>
            <p>The diagram below illustrates the relationships between core resources in the PyCommerce API:</p>
            
            <div class="relationship-diagram text-center mt-3">
                <pre class="bg-light p-3 text-start">
  ┌────────────┐     ┌────────────┐     ┌────────────┐
  │            │     │            │     │            │
  │   Tenant   │━━━━▶│   Product  │◀━━━━│   Order    │
  │            │     │            │     │            │
  └────────────┘     └────────────┘     └────────────┘
         ▲                  ▲                  │
         │                  │                  │
         │                  │                  ▼
  ┌────────────┐     ┌────────────┐     ┌────────────┐
  │            │     │            │     │            │
  │    User    │     │  Category  │     │ Order Item │
  │            │     │            │     │            │
  └────────────┘     └────────────┘     └────────────┘
                </pre>
            </div>
            
            <h2 class="mt-4">API Structure</h2>
            <p>The PyCommerce API follows a RESTful structure with these key areas:</p>
            
            <div class="list-group mt-3">
                <div class="list-group-item">
                    <h5 class="mb-1">Multi-Tenant Operations</h5>
                    <p class="mb-1">Create and manage stores with isolated data.</p>
                    <small>Base path: <code>/api/tenants</code></small>
                </div>
                <div class="list-group-item">
                    <h5 class="mb-1">Product Management</h5>
                    <p class="mb-1">Create, update, and organize products with categories.</p>
                    <small>Base path: <code>/api/products</code></small>
                </div>
                <div class="list-group-item">
                    <h5 class="mb-1">Order Processing</h5>
                    <p class="mb-1">Complete order lifecycle from creation to fulfillment.</p>
                    <small>Base path: <code>/api/orders</code></small>
                </div>
                <div class="list-group-item">
                    <h5 class="mb-1">User Management</h5>
                    <p class="mb-1">Customer and admin user accounts with role-based access.</p>
                    <small>Base path: <code>/api/users</code></small>
                </div>
                <div class="list-group-item">
                    <h5 class="mb-1">Content Management</h5>
                    <p class="mb-1">Create and manage storefront pages with a flexible page builder.</p>
                    <small>Base path: <code>/api/pages</code></small>
                </div>
            </div>
            
            <div class="mt-5 text-center">
                <p>For detailed API documentation, please visit:</p>
                <a href="/api/docs" class="btn btn-primary me-2">Swagger UI Documentation</a>
                <a href="/api/redoc" class="btn btn-secondary">ReDoc Documentation</a>
            </div>
        </div>
    </body>
    </html>
    """)

@docs_router.get("/postman-collection", response_class=JSONResponse, include_in_schema=False)
async def get_postman_collection(request: Request):
    """
    Generate a Postman collection for the API.
    
    This endpoint produces a Postman collection JSON file that can be imported
    into Postman for API testing and exploration.
    
    Args:
        request: The request object
        
    Returns:
        JSON object with Postman collection
    """
    host = request.headers.get("host", "localhost")
    protocol = "https" if request.headers.get("x-forwarded-proto") == "https" else "http"
    
    collection = {
        "info": {
            "name": "PyCommerce API",
            "description": "Collection for the PyCommerce e-commerce platform API",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "version": "1.0.0"
        },
        "item": [
            {
                "name": "Health Check",
                "request": {
                    "method": "GET",
                    "url": f"{protocol}://{host}/api/health",
                    "description": "Check the health of the API"
                },
                "response": []
            },
            {
                "name": "Products",
                "item": [
                    {
                        "name": "List Products",
                        "request": {
                            "method": "GET",
                            "url": {
                                "raw": f"{protocol}://{host}/api/products",
                                "query": [
                                    {"key": "category", "value": "", "disabled": True},
                                    {"key": "min_price", "value": "", "disabled": True},
                                    {"key": "max_price", "value": "", "disabled": True},
                                    {"key": "in_stock", "value": "true", "disabled": True},
                                    {"key": "limit", "value": "50"},
                                    {"key": "offset", "value": "0"}
                                ]
                            },
                            "description": "Get a list of products with optional filtering"
                        },
                        "response": []
                    },
                    {
                        "name": "Get Product",
                        "request": {
                            "method": "GET",
                            "url": f"{protocol}://{host}/api/products/{{product_id}}",
                            "description": "Get a single product by ID"
                        },
                        "response": []
                    },
                    {
                        "name": "Create Product",
                        "request": {
                            "method": "POST",
                            "url": f"{protocol}://{host}/api/products",
                            "description": "Create a new product",
                            "header": [
                                {"key": "Content-Type", "value": "application/json"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "name": "New Product",
                                    "description": "A new product description",
                                    "price": 29.99,
                                    "sku": "PROD-001",
                                    "stock": 100,
                                    "categories": []
                                }, indent=2)
                            }
                        },
                        "response": []
                    }
                ]
            },
            {
                "name": "Orders",
                "item": [
                    {
                        "name": "List Orders",
                        "request": {
                            "method": "GET",
                            "url": f"{protocol}://{host}/api/orders",
                            "description": "Get a list of orders"
                        },
                        "response": []
                    },
                    {
                        "name": "Get Order",
                        "request": {
                            "method": "GET",
                            "url": f"{protocol}://{host}/api/orders/{{order_id}}",
                            "description": "Get a single order by ID"
                        },
                        "response": []
                    }
                ]
            },
            {
                "name": "Tenants",
                "item": [
                    {
                        "name": "List Tenants",
                        "request": {
                            "method": "GET",
                            "url": f"{protocol}://{host}/api/tenants",
                            "description": "Get a list of tenants"
                        },
                        "response": []
                    }
                ]
            }
        ]
    }
    
    return collection

@docs_router.get("/examples/{language}", response_class=JSONResponse, include_in_schema=False)
async def get_code_examples(language: str, request: Request):
    """
    Get code examples for the API in a specific language.
    
    This endpoint provides ready-to-use code examples for
    common API operations in different programming languages.
    
    Args:
        language: Programming language for the examples (python, javascript, curl)
        request: The request object
        
    Returns:
        JSON object with code examples
    """
    host = request.headers.get("host", "localhost")
    protocol = "https" if request.headers.get("x-forwarded-proto") == "https" else "http"
    base_url = f"{protocol}://{host}"
    
    examples = {
        "python": {
            "list_products": f"""
import requests

def get_products(tenant_id=None, category=None, min_price=None, max_price=None):
    \"\"\"
    Get products from the PyCommerce API.
    
    Args:
        tenant_id: Optional tenant ID
        category: Optional category to filter by
        min_price: Optional minimum price
        max_price: Optional maximum price
        
    Returns:
        List of products
    \"\"\"
    url = "{base_url}/api/products"
    
    # Build query parameters
    params = {{"limit": 100, "offset": 0}}
    if category:
        params["category"] = category
    if min_price is not None:
        params["min_price"] = min_price
    if max_price is not None:
        params["max_price"] = max_price
    
    # Add tenant ID to headers if provided
    headers = {{"Accept": "application/json"}}
    if tenant_id:
        headers["X-Tenant-ID"] = tenant_id
    
    # Make the request
    response = requests.get(url, params=params, headers=headers)
    
    # Check for success
    response.raise_for_status()
    
    # Return the data
    return response.json()

# Example usage
try:
    products = get_products(category="electronics", min_price=10.0)
    print(f"Found {{len(products)}} products")
    for product in products:
        print(f"{{product['name']}}: ${{product['price']}}")
except requests.exceptions.HTTPError as e:
    print(f"Error: {{e}}")
            """,
            "create_product": f"""
import requests
import json

def create_product(token, product_data, tenant_id=None):
    \"\"\"
    Create a new product in the PyCommerce API.
    
    Args:
        token: JWT authentication token
        product_data: Dictionary with product details
        tenant_id: Optional tenant ID
        
    Returns:
        The created product
    \"\"\"
    url = "{base_url}/api/products"
    
    # Set headers with authentication
    headers = {{
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {{token}}"
    }}
    
    # Add tenant ID if provided
    if tenant_id:
        headers["X-Tenant-ID"] = tenant_id
    
    # Make the request
    response = requests.post(url, json=product_data, headers=headers)
    
    # Check for success
    response.raise_for_status()
    
    # Return the created product
    return response.json()

# Example usage
try:
    new_product = {{
        "name": "Wireless Headphones",
        "description": "High-quality wireless headphones with noise cancellation",
        "price": 129.99,
        "sku": "HDPHN-001",
        "stock": 50,
        "categories": ["electronics", "audio"]
    }}
    
    token = "your_jwt_token_here"
    created_product = create_product(token, new_product)
    print(f"Created product with ID: {{created_product['id']}}")
except requests.exceptions.HTTPError as e:
    print(f"Error: {{e}}")
            """,
            "get_order": f"""
import requests

def get_order(order_id, token, tenant_id=None):
    \"\"\"
    Get a specific order from the PyCommerce API.
    
    Args:
        order_id: The ID of the order to retrieve
        token: JWT authentication token
        tenant_id: Optional tenant ID
        
    Returns:
        The order details
    \"\"\"
    url = f"{base_url}/api/orders/{{order_id}}"
    
    # Set headers with authentication
    headers = {{
        "Accept": "application/json",
        "Authorization": f"Bearer {{token}}"
    }}
    
    # Add tenant ID if provided
    if tenant_id:
        headers["X-Tenant-ID"] = tenant_id
    
    # Make the request
    response = requests.get(url, headers=headers)
    
    # Check for success
    response.raise_for_status()
    
    # Return the order
    return response.json()

# Example usage
try:
    token = "your_jwt_token_here"
    order_id = "abc123"
    order = get_order(order_id, token)
    print(f"Order {{order['id']}} has {{len(order['items'])}} items")
    print(f"Total: ${{order['total']}}")
    print(f"Status: {{order['status']}}")
except requests.exceptions.HTTPError as e:
    print(f"Error: {{e}}")
            """
        },
        "javascript": {
            "list_products": f"""
/**
 * Get products from the PyCommerce API.
 * 
 * @param {{Object}} options - Options for the request
 * @param {{string}} options.tenantId - Optional tenant ID
 * @param {{string}} options.category - Optional category to filter by
 * @param {{number}} options.minPrice - Optional minimum price
 * @param {{number}} options.maxPrice - Optional maximum price
 * @param {{number}} options.limit - Maximum number of products to return
 * @param {{number}} options.offset - Pagination offset
 * @returns {{Promise<Object[]>}} List of products
 */
async function getProducts(options = {{}}) {{
  // Default options
  const {{
    tenantId = null,
    category = null,
    minPrice = null,
    maxPrice = null,
    limit = 100,
    offset = 0
  }} = options;
  
  // Build query parameters
  const params = new URLSearchParams();
  params.append('limit', limit);
  params.append('offset', offset);
  
  if (category) params.append('category', category);
  if (minPrice !== null) params.append('min_price', minPrice);
  if (maxPrice !== null) params.append('max_price', maxPrice);
  
  // Set up headers
  const headers = {{
    'Accept': 'application/json'
  }};
  
  if (tenantId) {{
    headers['X-Tenant-ID'] = tenantId;
  }}
  
  // Make the request
  const url = `{base_url}/api/products?${{params.toString()}}`;
  const response = await fetch(url, {{ headers }});
  
  // Check for success
  if (!response.ok) {{
    const error = await response.json();
    throw new Error(error.detail || `HTTP error! status: ${{response.status}}`);
  }}
  
  // Return the data
  return response.json();
}}

// Example usage
async function displayProducts() {{
  try {{
    const products = await getProducts({{
      category: 'electronics',
      minPrice: 10.0
    }});
    
    console.log(`Found ${{products.length}} products`);
    
    products.forEach(product => {{
      console.log(`${{product.name}}: $${{product.price}}`);
    }});
  }} catch (error) {{
    console.error('Error:', error.message);
  }}
}}

displayProducts();
            """,
            "create_product": f"""
/**
 * Create a new product in the PyCommerce API.
 * 
 * @param {{string}} token - JWT authentication token
 * @param {{Object}} productData - Product details
 * @param {{string}} [tenantId] - Optional tenant ID
 * @returns {{Promise<Object>}} The created product
 */
async function createProduct(token, productData, tenantId = null) {{
  // Set headers with authentication
  const headers = {{
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': `Bearer ${{token}}`
  }};
  
  // Add tenant ID if provided
  if (tenantId) {{
    headers['X-Tenant-ID'] = tenantId;
  }}
  
  // Make the request
  const url = '{base_url}/api/products';
  const response = await fetch(url, {{
    method: 'POST',
    headers,
    body: JSON.stringify(productData)
  }});
  
  // Check for success
  if (!response.ok) {{
    const error = await response.json();
    throw new Error(error.detail || `HTTP error! status: ${{response.status}}`);
  }}
  
  // Return the created product
  return response.json();
}}

// Example usage
async function addNewProduct() {{
  try {{
    const newProduct = {{
      name: 'Wireless Headphones',
      description: 'High-quality wireless headphones with noise cancellation',
      price: 129.99,
      sku: 'HDPHN-001',
      stock: 50,
      categories: ['electronics', 'audio']
    }};
    
    const token = 'your_jwt_token_here';
    const createdProduct = await createProduct(token, newProduct);
    console.log(`Created product with ID: ${{createdProduct.id}}`);
  }} catch (error) {{
    console.error('Error:', error.message);
  }}
}}

addNewProduct();
            """,
            "get_order": f"""
/**
 * Get a specific order from the PyCommerce API.
 * 
 * @param {{string}} orderId - The ID of the order to retrieve
 * @param {{string}} token - JWT authentication token
 * @param {{string}} [tenantId] - Optional tenant ID
 * @returns {{Promise<Object>}} The order details
 */
async function getOrder(orderId, token, tenantId = null) {{
  // Set headers with authentication
  const headers = {{
    'Accept': 'application/json',
    'Authorization': `Bearer ${{token}}`
  }};
  
  // Add tenant ID if provided
  if (tenantId) {{
    headers['X-Tenant-ID'] = tenantId;
  }}
  
  // Make the request
  const url = `{base_url}/api/orders/${{orderId}}`;
  const response = await fetch(url, {{ headers }});
  
  // Check for success
  if (!response.ok) {{
    const error = await response.json();
    throw new Error(error.detail || `HTTP error! status: ${{response.status}}`);
  }}
  
  // Return the order
  return response.json();
}}

// Example usage
async function displayOrderDetails() {{
  try {{
    const token = 'your_jwt_token_here';
    const orderId = 'abc123';
    const order = await getOrder(orderId, token);
    
    console.log(`Order ${{order.id}} has ${{order.items.length}} items`);
    console.log(`Total: $${{order.total}}`);
    console.log(`Status: ${{order.status}}`);
  }} catch (error) {{
    console.error('Error:', error.message);
  }}
}}

displayOrderDetails();
            """
        },
        "curl": {
            "list_products": f"""
# Get products from the PyCommerce API
curl -X GET "{base_url}/api/products?limit=100&offset=0" \\
  -H "Accept: application/json" \\
  -H "X-Tenant-ID: optional_tenant_id"

# With category and price filtering
curl -X GET "{base_url}/api/products?category=electronics&min_price=10.0&max_price=100.0&limit=50" \\
  -H "Accept: application/json"
            """,
            "create_product": f"""
# Create a new product in the PyCommerce API
curl -X POST "{base_url}/api/products" \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json" \\
  -H "Authorization: Bearer your_jwt_token_here" \\
  -H "X-Tenant-ID: optional_tenant_id" \\
  -d '{{
    "name": "Wireless Headphones",
    "description": "High-quality wireless headphones with noise cancellation",
    "price": 129.99,
    "sku": "HDPHN-001",
    "stock": 50,
    "categories": ["electronics", "audio"]
  }}'
            """,
            "get_order": f"""
# Get a specific order from the PyCommerce API
curl -X GET "{base_url}/api/orders/order_id_here" \\
  -H "Accept: application/json" \\
  -H "Authorization: Bearer your_jwt_token_here" \\
  -H "X-Tenant-ID: optional_tenant_id"
            """
        }
    }
    
    if language not in examples:
        raise HTTPException(status_code=404, detail=f"Code examples for {language} not found")
    
    return examples[language]

# Enhanced OpenAPI schema generation
def custom_openapi(app):
    """
    Generate a custom OpenAPI schema with improved documentation.
    
    Args:
        app: The FastAPI application
        
    Returns:
        Dict containing the enhanced OpenAPI schema
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
        servers=app.servers,
    )
    
    # Enhanced security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT authentication token"
        },
        "tenantHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "X-Tenant-ID",
            "description": "Tenant identifier for multi-tenant operations"
        }
    }
    
    # Apply global security requirements
    openapi_schema["security"] = [
        {"bearerAuth": []}
    ]
    
    # Add custom documentation sections
    if "info" in openapi_schema:
        openapi_schema["info"]["x-logo"] = {
            "url": "/static/logo.png",
            "backgroundColor": "#FFFFFF",
            "altText": "PyCommerce Logo"
        }
        
        openapi_schema["info"]["x-documentation"] = [
            {
                "name": "Introduction",
                "content": "Welcome to the PyCommerce API documentation. This API provides comprehensive access to the PyCommerce e-commerce platform."
            },
            {
                "name": "Authentication",
                "content": "Most endpoints require authentication using JWT tokens. Include the token in the Authorization header."
            },
            {
                "name": "Multi-tenancy",
                "content": "PyCommerce uses a multi-tenant architecture. Specify the tenant ID in the X-Tenant-ID header or as a subdomain."
            },
            {
                "name": "Rate Limiting",
                "content": "The API enforces rate limiting to ensure fair usage. Check the X-RateLimit-* headers for details."
            }
        ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

def setup_api_documentation(app):
    """
    Setup enhanced API documentation routes for the FastAPI application.
    
    This function configures comprehensive OpenAPI documentation with
    improved schema definitions, code examples, and interactive UI.
    
    Args:
        app: The FastAPI application
    """
    try:
        logger.info("Setting up API documentation routes")
        
        # Configure OpenAPI options
        app.openapi_tags = [
            {
                "name": "System",
                "description": "System-level operations and health checks"
            },
            {
                "name": "Tenants",
                "description": "Operations related to tenant management",
                "externalDocs": {
                    "description": "Multi-tenant architecture guide",
                    "url": "/docs/multi-tenancy.html"
                }
            },
            {
                "name": "Products",
                "description": "Operations related to product management",
                "externalDocs": {
                    "description": "Product management guide",
                    "url": "/docs/product-management.html"
                }
            },
            {
                "name": "Orders",
                "description": "Operations related to order management",
                "externalDocs": {
                    "description": "Order processing guide",
                    "url": "/docs/order-processing.html"
                }
            },
            {
                "name": "Categories",
                "description": "Operations related to product categories"
            },
            {
                "name": "Users",
                "description": "Operations related to user management",
                "externalDocs": {
                    "description": "User authentication and permissions",
                    "url": "/docs/user-management.html"
                }
            },
            {
                "name": "Media",
                "description": "Operations related to media management"
            },
            {
                "name": "Pages",
                "description": "Operations related to content pages"
            },
            {
                "name": "API Documentation",
                "description": "API documentation endpoints"
            }
        ]
        
        # Update app metadata
        app.title = "PyCommerce API"
        app.description = """
        # PyCommerce API
        
        The official API for the PyCommerce platform, a multi-tenant ecommerce solution built with Python.
        
        ## Core Features
        
        * **Multi-Tenant Architecture**: Complete data isolation between tenants
        * **Product Management**: Comprehensive product catalog with categories
        * **Order Management**: Complete order lifecycle with status tracking
        * **User Management**: Customer accounts and admin controls
        * **Content Management**: Flexible page builder for storefront content
        * **Media Management**: Image and asset management with AI capabilities
        
        ## Authentication
        
        Most endpoints require authentication using JWT tokens. To authenticate:
        
        1. Obtain a token through the `/api/auth/login` endpoint
        2. Include the token in the `Authorization` header as `Bearer {token}`
        
        ## Multi-tenancy
        
        PyCommerce is designed for multiple isolated stores (tenants). Specify the tenant in:
        
        1. The `X-Tenant-ID` header
        2. A subdomain (e.g., `tenant-name.example.com`)
        3. The request URL for tenant-specific API paths
        
        ## Error Handling
        
        The API uses standard HTTP status codes and returns detailed error responses:
        
        ```json
        {
          "detail": "Error message",
          "code": "ERROR_CODE",
          "field": "field_with_error"
        }
        ```
        
        ## Pagination
        
        List endpoints support pagination using `limit` and `offset` parameters:
        
        ```
        GET /api/products?limit=50&offset=100
        ```
        """
        app.version = "1.0.0"
        app.contact = {
            "name": "PyCommerce Support",
            "url": "https://pycommerce.example.com/support",
            "email": "support@pycommerce.example.com",
        }
        app.license_info = {
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        }
        
        # Set up custom OpenAPI schema
        app.openapi = lambda: custom_openapi(app)
        
        # Include documentation router
        app.include_router(docs_router)
        
        logger.info("API documentation routes set up successfully")
    except Exception as e:
        logger.error(f"Error setting up API documentation: {str(e)}")
        raise