"""
API Documentation Builder for PyCommerce.

This module provides utilities for building comprehensive API documentation,
including language-specific code examples, schema visualization, and reference
materials.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Code example templates for various programming languages
CODE_EXAMPLES = {
    "python": {
        "authentication": '''
import requests

def get_auth_token(api_url, username, password):
    """
    Get authentication token from the PyCommerce API.
    
    Args:
        api_url: Base API URL (e.g., https://api.example.com)
        username: User email or username
        password: User password
        
    Returns:
        Dict containing the authentication token and expiry
    """
    auth_url = f"{api_url}/api/auth/login"
    
    # Set up the request data
    data = {
        "username": username,
        "password": password
    }
    
    # Make the request
    response = requests.post(auth_url, json=data)
    
    # Check for success
    response.raise_for_status()
    
    # Return the token data
    return response.json()

# Example usage
try:
    token_data = get_auth_token(
        api_url="https://example.com",
        username="admin@example.com",
        password="your_secure_password"
    )
    
    # Extract token for future requests
    token = token_data["access_token"]
    print(f"Successfully authenticated. Token expires in {token_data['expires_in']} seconds")
except requests.exceptions.HTTPError as e:
    print(f"Authentication failed: {e}")
''',
        "multi_tenant": '''
import requests

class PyCommerceClient:
    """Client for interacting with the PyCommerce API in multi-tenant mode."""
    
    def __init__(self, api_url, token=None, tenant_id=None):
        """
        Initialize the client with authentication and tenant information.
        
        Args:
            api_url: Base API URL (e.g., https://api.example.com)
            token: JWT authentication token (optional)
            tenant_id: ID of the tenant to work with (optional)
        """
        self.api_url = api_url.rstrip('/')
        self.token = token
        self.tenant_id = tenant_id
        
    def _get_headers(self):
        """Build headers with authentication and tenant information."""
        headers = {"Accept": "application/json"}
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            
        if self.tenant_id:
            headers["X-Tenant-ID"] = self.tenant_id
            
        return headers
    
    def list_products(self, category=None, min_price=None, max_price=None, limit=100, offset=0):
        """
        Get products with optional filtering.
        
        Args:
            category: Filter by category (optional)
            min_price: Minimum price filter (optional)
            max_price: Maximum price filter (optional)
            limit: Maximum number of products to return (default 100)
            offset: Pagination offset (default 0)
            
        Returns:
            List of product objects
        """
        url = f"{self.api_url}/api/products"
        
        # Build query parameters
        params = {"limit": limit, "offset": offset}
        if category:
            params["category"] = category
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price
        
        # Make the request
        response = requests.get(url, params=params, headers=self._get_headers())
        
        # Check for success
        response.raise_for_status()
        
        # Return the data
        return response.json()

# Example usage for a specific tenant
client = PyCommerceClient(
    api_url="https://example.com",
    token="your_jwt_token",
    tenant_id="tenant-123"
)

try:
    # Get electronics products under $100
    products = client.list_products(
        category="electronics",
        max_price=100.0
    )
    print(f"Found {len(products)} products")
except requests.exceptions.HTTPError as e:
    print(f"Error: {e}")
'''
    },
    "javascript": {
        "authentication": '''
/**
 * Get authentication token from the PyCommerce API.
 * 
 * @param {string} apiUrl - Base API URL (e.g., https://api.example.com)
 * @param {string} username - User email or username
 * @param {string} password - User password
 * @returns {Promise<Object>} - Object containing the authentication token and expiry
 */
async function getAuthToken(apiUrl, username, password) {
  const authUrl = `${apiUrl}/api/auth/login`;
  
  // Set up the request data
  const data = {
    username,
    password
  };
  
  // Make the request
  const response = await fetch(authUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    },
    body: JSON.stringify(data)
  });
  
  // Check for success
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Authentication failed: ${response.status}`);
  }
  
  // Return the token data
  return response.json();
}

// Example usage
async function authenticate() {
  try {
    const tokenData = await getAuthToken(
      'https://example.com',
      'admin@example.com',
      'your_secure_password'
    );
    
    // Extract token for future requests
    const token = tokenData.access_token;
    console.log(`Successfully authenticated. Token expires in ${tokenData.expires_in} seconds`);
    
    return token;
  } catch (error) {
    console.error(`Authentication failed: ${error.message}`);
    return null;
  }
}

authenticate();
''',
        "multi_tenant": '''
/**
 * Client for interacting with the PyCommerce API in multi-tenant mode.
 */
class PyCommerceClient {
  /**
   * Initialize the client with authentication and tenant information.
   * 
   * @param {string} apiUrl - Base API URL (e.g., https://api.example.com)
   * @param {string} [token] - JWT authentication token (optional)
   * @param {string} [tenantId] - ID of the tenant to work with (optional)
   */
  constructor(apiUrl, token = null, tenantId = null) {
    this.apiUrl = apiUrl.endsWith('/') ? apiUrl.slice(0, -1) : apiUrl;
    this.token = token;
    this.tenantId = tenantId;
  }
  
  /**
   * Build headers with authentication and tenant information.
   * 
   * @returns {Object} - Headers for API requests
   */
  _getHeaders() {
    const headers = {
      'Accept': 'application/json'
    };
    
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    
    if (this.tenantId) {
      headers['X-Tenant-ID'] = this.tenantId;
    }
    
    return headers;
  }
  
  /**
   * Get products with optional filtering.
   * 
   * @param {Object} [options] - Filter options
   * @param {string} [options.category] - Filter by category
   * @param {number} [options.minPrice] - Minimum price filter
   * @param {number} [options.maxPrice] - Maximum price filter
   * @param {number} [options.limit=100] - Maximum number of products to return
   * @param {number} [options.offset=0] - Pagination offset
   * @returns {Promise<Object[]>} - List of product objects
   */
  async listProducts({
    category = null,
    minPrice = null,
    maxPrice = null,
    limit = 100,
    offset = 0
  } = {}) {
    const url = `${this.apiUrl}/api/products`;
    
    // Build query parameters
    const params = new URLSearchParams();
    params.append('limit', limit);
    params.append('offset', offset);
    
    if (category) params.append('category', category);
    if (minPrice !== null) params.append('min_price', minPrice);
    if (maxPrice !== null) params.append('max_price', maxPrice);
    
    // Make the request
    const response = await fetch(`${url}?${params.toString()}`, {
      headers: this._getHeaders()
    });
    
    // Check for success
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `API error: ${response.status}`);
    }
    
    // Return the data
    return response.json();
  }
}

// Example usage for a specific tenant
async function getProductsForTenant() {
  const client = new PyCommerceClient(
    'https://example.com',
    'your_jwt_token',
    'tenant-123'
  );
  
  try {
    // Get electronics products under $100
    const products = await client.listProducts({
      category: 'electronics',
      maxPrice: 100.0
    });
    
    console.log(`Found ${products.length} products`);
    return products;
  } catch (error) {
    console.error(`Error: ${error.message}`);
    return [];
  }
}

getProductsForTenant();
'''
    },
    "curl": {
        "authentication": '''
# Get authentication token from the PyCommerce API
curl -X POST "https://example.com/api/auth/login" \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json" \\
  -d '{
    "username": "admin@example.com",
    "password": "your_secure_password"
  }'

# Example success response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer",
#   "expires_in": 3600,
#   "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
# }
''',
        "multi_tenant": '''
# List products for a specific tenant
curl -X GET "https://example.com/api/products?category=electronics&max_price=100.0&limit=100&offset=0" \\
  -H "Accept: application/json" \\
  -H "Authorization: Bearer your_jwt_token" \\
  -H "X-Tenant-ID: tenant-123"

# Get a specific product with tenant context
curl -X GET "https://example.com/api/products/product-456" \\
  -H "Accept: application/json" \\
  -H "Authorization: Bearer your_jwt_token" \\
  -H "X-Tenant-ID: tenant-123"

# Create a new product for a tenant
curl -X POST "https://example.com/api/products" \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json" \\
  -H "Authorization: Bearer your_jwt_token" \\
  -H "X-Tenant-ID: tenant-123" \\
  -d '{
    "name": "Wireless Headphones",
    "description": "High-quality wireless headphones with noise cancellation",
    "price": 129.99,
    "sku": "HDPHN-001",
    "stock": 50,
    "categories": ["electronics", "audio"]
  }'
'''
    }
}

def get_code_example(language: str, section: str) -> str:
    """
    Get a code example for a specific language and section.
    
    Args:
        language: Programming language (python, javascript, curl)
        section: Section identifier (authentication, multi_tenant, etc.)
        
    Returns:
        Code example as a string
    """
    try:
        return CODE_EXAMPLES.get(language, {}).get(section, "Example not available")
    except Exception as e:
        logger.error(f"Error retrieving code example: {str(e)}")
        return "Error retrieving example"

def get_schema_documentation() -> Dict[str, Any]:
    """
    Get comprehensive schema documentation with descriptions.
    
    Returns:
        Dictionary containing schema documentation
    """
    return {
        "tenants": {
            "description": "Tenants represent separate stores or businesses within the multi-tenant architecture.",
            "endpoints": [
                {"method": "GET", "path": "/api/tenants", "description": "List all tenants"},
                {"method": "GET", "path": "/api/tenants/{tenant_id}", "description": "Get a specific tenant"},
                {"method": "POST", "path": "/api/tenants", "description": "Create a new tenant"},
                {"method": "PUT", "path": "/api/tenants/{tenant_id}", "description": "Update a tenant"},
                {"method": "DELETE", "path": "/api/tenants/{tenant_id}", "description": "Delete a tenant"}
            ],
            "schema": {
                "id": {"type": "string", "format": "uuid", "description": "Unique identifier"},
                "name": {"type": "string", "description": "Display name"},
                "slug": {"type": "string", "description": "URL-friendly identifier"},
                "domain": {"type": "string", "description": "Custom domain (optional)"},
                "settings": {"type": "object", "description": "Tenant-specific settings"},
                "active": {"type": "boolean", "description": "Whether the tenant is active"},
                "created_at": {"type": "string", "format": "date-time", "description": "Creation timestamp"}
            }
        },
        "products": {
            "description": "Products that can be purchased through the e-commerce platform.",
            "endpoints": [
                {"method": "GET", "path": "/api/products", "description": "List products with filtering"},
                {"method": "GET", "path": "/api/products/{product_id}", "description": "Get a specific product"},
                {"method": "POST", "path": "/api/products", "description": "Create a new product"},
                {"method": "PUT", "path": "/api/products/{product_id}", "description": "Update a product"},
                {"method": "DELETE", "path": "/api/products/{product_id}", "description": "Delete a product"}
            ],
            "schema": {
                "id": {"type": "string", "format": "uuid", "description": "Unique identifier"},
                "tenant_id": {"type": "string", "format": "uuid", "description": "Tenant this product belongs to"},
                "name": {"type": "string", "description": "Product name"},
                "description": {"type": "string", "description": "Product description (optional)"},
                "price": {"type": "number", "format": "float", "description": "Price in the store's currency"},
                "sku": {"type": "string", "description": "Stock keeping unit (unique per tenant)"},
                "stock": {"type": "integer", "description": "Available quantity"},
                "categories": {"type": "array", "items": {"type": "string"}, "description": "Category IDs"},
                "created_at": {"type": "string", "format": "date-time", "description": "Creation timestamp"},
                "updated_at": {"type": "string", "format": "date-time", "description": "Last update timestamp"},
                "cost_price": {"type": "number", "format": "float", "description": "Cost price for profit calculation"},
                "is_material": {"type": "boolean", "description": "Whether this is a material"},
                "is_labor": {"type": "boolean", "description": "Whether this represents labor"}
            }
        },
        "orders": {
            "description": "Customer orders containing purchased products.",
            "endpoints": [
                {"method": "GET", "path": "/api/orders", "description": "List orders"},
                {"method": "GET", "path": "/api/orders/{order_id}", "description": "Get a specific order"},
                {"method": "POST", "path": "/api/orders", "description": "Create a new order"},
                {"method": "PUT", "path": "/api/orders/{order_id}", "description": "Update an order's status"},
                {"method": "DELETE", "path": "/api/orders/{order_id}", "description": "Delete an order"}
            ],
            "schema": {
                "id": {"type": "string", "format": "uuid", "description": "Unique identifier"},
                "tenant_id": {"type": "string", "format": "uuid", "description": "Tenant this order belongs to"},
                "user_id": {"type": "string", "format": "uuid", "description": "User who placed the order (optional)"},
                "status": {"type": "string", "description": "Order status (pending, processing, shipped, etc.)"},
                "total": {"type": "number", "format": "float", "description": "Order total amount"},
                "items": {"type": "array", "description": "Line items in the order"},
                "shipping_address": {"type": "object", "description": "Shipping information"},
                "billing_address": {"type": "object", "description": "Billing information (optional)"},
                "payment_status": {"type": "string", "description": "Payment status"},
                "created_at": {"type": "string", "format": "date-time", "description": "Order placement timestamp"},
                "updated_at": {"type": "string", "format": "date-time", "description": "Last update timestamp"},
                "total_cost": {"type": "number", "format": "float", "description": "Combined cost of materials and labor"},
                "profit": {"type": "number", "format": "float", "description": "Total profit (total - total_cost)"},
                "profit_margin": {"type": "number", "format": "float", "description": "Percentage profit margin"}
            }
        },
        "users": {
            "description": "User accounts for customers and administrators.",
            "endpoints": [
                {"method": "GET", "path": "/api/users", "description": "List users"},
                {"method": "GET", "path": "/api/users/{user_id}", "description": "Get a specific user"},
                {"method": "POST", "path": "/api/users", "description": "Create a new user"},
                {"method": "PUT", "path": "/api/users/{user_id}", "description": "Update a user"},
                {"method": "DELETE", "path": "/api/users/{user_id}", "description": "Delete a user"}
            ],
            "schema": {
                "id": {"type": "string", "format": "uuid", "description": "Unique identifier"},
                "tenant_id": {"type": "string", "format": "uuid", "description": "Tenant this user belongs to"},
                "email": {"type": "string", "format": "email", "description": "Email address (used for login)"},
                "username": {"type": "string", "description": "Username"},
                "role": {"type": "string", "description": "User role (admin, customer, etc.)"},
                "active": {"type": "boolean", "description": "Whether the account is active"},
                "created_at": {"type": "string", "format": "date-time", "description": "Account creation timestamp"},
                "last_login": {"type": "string", "format": "date-time", "description": "Last login timestamp"}
            }
        },
        "categories": {
            "description": "Product categories for organizing the catalog.",
            "endpoints": [
                {"method": "GET", "path": "/api/categories", "description": "List categories"},
                {"method": "GET", "path": "/api/categories/{category_id}", "description": "Get a specific category"},
                {"method": "POST", "path": "/api/categories", "description": "Create a new category"},
                {"method": "PUT", "path": "/api/categories/{category_id}", "description": "Update a category"},
                {"method": "DELETE", "path": "/api/categories/{category_id}", "description": "Delete a category"}
            ],
            "schema": {
                "id": {"type": "string", "format": "uuid", "description": "Unique identifier"},
                "tenant_id": {"type": "string", "format": "uuid", "description": "Tenant this category belongs to"},
                "name": {"type": "string", "description": "Category name"},
                "slug": {"type": "string", "description": "URL-friendly identifier"},
                "description": {"type": "string", "description": "Category description (optional)"},
                "parent_id": {"type": "string", "format": "uuid", "description": "Parent category ID (optional)"},
                "created_at": {"type": "string", "format": "date-time", "description": "Creation timestamp"}
            }
        },
        "pages": {
            "description": "Custom storefront pages created with the page builder.",
            "endpoints": [
                {"method": "GET", "path": "/api/pages", "description": "List pages"},
                {"method": "GET", "path": "/api/pages/{page_id}", "description": "Get a specific page"},
                {"method": "POST", "path": "/api/pages", "description": "Create a new page"},
                {"method": "PUT", "path": "/api/pages/{page_id}", "description": "Update a page"},
                {"method": "DELETE", "path": "/api/pages/{page_id}", "description": "Delete a page"}
            ],
            "schema": {
                "id": {"type": "string", "format": "uuid", "description": "Unique identifier"},
                "tenant_id": {"type": "string", "format": "uuid", "description": "Tenant this page belongs to"},
                "title": {"type": "string", "description": "Page title"},
                "slug": {"type": "string", "description": "URL path"},
                "status": {"type": "string", "description": "Publication status (draft, published)"},
                "template_id": {"type": "string", "format": "uuid", "description": "Page template ID (optional)"},
                "sections": {"type": "array", "description": "Sections in the page"},
                "created_at": {"type": "string", "format": "date-time", "description": "Creation timestamp"},
                "updated_at": {"type": "string", "format": "date-time", "description": "Last update timestamp"}
            }
        },
        "media": {
            "description": "Uploaded files and images for products, pages, and other content.",
            "endpoints": [
                {"method": "GET", "path": "/api/media", "description": "List media files"},
                {"method": "GET", "path": "/api/media/{media_id}", "description": "Get a specific media file"},
                {"method": "POST", "path": "/api/media", "description": "Upload a new media file"},
                {"method": "PUT", "path": "/api/media/{media_id}", "description": "Update media metadata"},
                {"method": "DELETE", "path": "/api/media/{media_id}", "description": "Delete a media file"}
            ],
            "schema": {
                "id": {"type": "string", "format": "uuid", "description": "Unique identifier"},
                "tenant_id": {"type": "string", "format": "uuid", "description": "Tenant this media belongs to"},
                "name": {"type": "string", "description": "File name"},
                "type": {"type": "string", "description": "Media type (image, document, etc.)"},
                "path": {"type": "string", "description": "Storage path"},
                "url": {"type": "string", "format": "uri", "description": "Access URL"},
                "metadata": {"type": "object", "description": "Additional information"},
                "sharing_level": {"type": "string", "description": "Access control level"},
                "created_at": {"type": "string", "format": "date-time", "description": "Upload timestamp"}
            }
        }
    }

def generate_postman_collection(base_url: str) -> Dict[str, Any]:
    """
    Generate a Postman collection for the API.
    
    Args:
        base_url: Base URL for the API (e.g., https://example.com)
        
    Returns:
        Dictionary containing Postman collection
    """
    collection = {
        "info": {
            "name": "PyCommerce API",
            "description": "Complete API collection for the PyCommerce e-commerce platform",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "version": "1.0.0"
        },
        "item": [
            {
                "name": "Authentication",
                "item": [
                    {
                        "name": "Login",
                        "request": {
                            "method": "POST",
                            "url": f"{base_url}/api/auth/login",
                            "description": "Authenticate and get a JWT token",
                            "header": [
                                {"key": "Content-Type", "value": "application/json"},
                                {"key": "Accept", "value": "application/json"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "username": "admin@example.com",
                                    "password": "your_password"
                                }, indent=2)
                            }
                        },
                        "response": []
                    },
                    {
                        "name": "Refresh Token",
                        "request": {
                            "method": "POST",
                            "url": f"{base_url}/api/auth/refresh",
                            "description": "Refresh an expired JWT token",
                            "header": [
                                {"key": "Content-Type", "value": "application/json"},
                                {"key": "Accept", "value": "application/json"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "refresh_token": "your_refresh_token"
                                }, indent=2)
                            }
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
                            "url": f"{base_url}/api/tenants",
                            "description": "Get a list of all tenants",
                            "header": [
                                {"key": "Authorization", "value": "Bearer {{token}}"},
                                {"key": "Accept", "value": "application/json"}
                            ]
                        },
                        "response": []
                    },
                    {
                        "name": "Get Tenant",
                        "request": {
                            "method": "GET",
                            "url": f"{base_url}/api/tenants/{{tenant_id}}",
                            "description": "Get a specific tenant by ID",
                            "header": [
                                {"key": "Authorization", "value": "Bearer {{token}}"},
                                {"key": "Accept", "value": "application/json"}
                            ]
                        },
                        "response": []
                    },
                    {
                        "name": "Create Tenant",
                        "request": {
                            "method": "POST",
                            "url": f"{base_url}/api/tenants",
                            "description": "Create a new tenant",
                            "header": [
                                {"key": "Authorization", "value": "Bearer {{token}}"},
                                {"key": "Content-Type", "value": "application/json"},
                                {"key": "Accept", "value": "application/json"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "name": "New Store",
                                    "slug": "new-store",
                                    "domain": "new-store.example.com",
                                    "active": True
                                }, indent=2)
                            }
                        },
                        "response": []
                    }
                ]
            },
            {
                "name": "Products",
                "item": [
                    {
                        "name": "List Products",
                        "request": {
                            "method": "GET",
                            "url": {
                                "raw": f"{base_url}/api/products",
                                "query": [
                                    {"key": "category", "value": "", "disabled": True},
                                    {"key": "min_price", "value": "", "disabled": True},
                                    {"key": "max_price", "value": "", "disabled": True},
                                    {"key": "in_stock", "value": "true", "disabled": True},
                                    {"key": "limit", "value": "50"},
                                    {"key": "offset", "value": "0"}
                                ]
                            },
                            "description": "Get a list of products with optional filtering",
                            "header": [
                                {"key": "Authorization", "value": "Bearer {{token}}"},
                                {"key": "X-Tenant-ID", "value": "{{tenant_id}}"},
                                {"key": "Accept", "value": "application/json"}
                            ]
                        },
                        "response": []
                    },
                    {
                        "name": "Get Product",
                        "request": {
                            "method": "GET",
                            "url": f"{base_url}/api/products/{{product_id}}",
                            "description": "Get a specific product by ID",
                            "header": [
                                {"key": "Authorization", "value": "Bearer {{token}}"},
                                {"key": "X-Tenant-ID", "value": "{{tenant_id}}"},
                                {"key": "Accept", "value": "application/json"}
                            ]
                        },
                        "response": []
                    },
                    {
                        "name": "Create Product",
                        "request": {
                            "method": "POST",
                            "url": f"{base_url}/api/products",
                            "description": "Create a new product",
                            "header": [
                                {"key": "Authorization", "value": "Bearer {{token}}"},
                                {"key": "X-Tenant-ID", "value": "{{tenant_id}}"},
                                {"key": "Content-Type", "value": "application/json"},
                                {"key": "Accept", "value": "application/json"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "name": "New Product",
                                    "description": "Product description",
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
                            "url": f"{base_url}/api/orders",
                            "description": "Get a list of orders",
                            "header": [
                                {"key": "Authorization", "value": "Bearer {{token}}"},
                                {"key": "X-Tenant-ID", "value": "{{tenant_id}}"},
                                {"key": "Accept", "value": "application/json"}
                            ]
                        },
                        "response": []
                    },
                    {
                        "name": "Get Order",
                        "request": {
                            "method": "GET",
                            "url": f"{base_url}/api/orders/{{order_id}}",
                            "description": "Get a specific order by ID",
                            "header": [
                                {"key": "Authorization", "value": "Bearer {{token}}"},
                                {"key": "X-Tenant-ID", "value": "{{tenant_id}}"},
                                {"key": "Accept", "value": "application/json"}
                            ]
                        },
                        "response": []
                    },
                    {
                        "name": "Create Order",
                        "request": {
                            "method": "POST",
                            "url": f"{base_url}/api/orders",
                            "description": "Create a new order",
                            "header": [
                                {"key": "Authorization", "value": "Bearer {{token}}"},
                                {"key": "X-Tenant-ID", "value": "{{tenant_id}}"},
                                {"key": "Content-Type", "value": "application/json"},
                                {"key": "Accept", "value": "application/json"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "user_id": "optional_user_id",
                                    "status": "pending",
                                    "shipping_address": {
                                        "name": "Customer Name",
                                        "street": "123 Main St",
                                        "city": "Anytown",
                                        "state": "CA",
                                        "postal_code": "12345",
                                        "country": "USA",
                                        "phone": "555-123-4567"
                                    },
                                    "items": [
                                        {
                                            "product_id": "product_id_1",
                                            "quantity": 2,
                                            "price": 29.99,
                                            "name": "Product Name",
                                            "sku": "PROD-001"
                                        }
                                    ]
                                }, indent=2)
                            }
                        },
                        "response": []
                    }
                ]
            }
        ]
    }
    
    return collection

def generate_openapi_extension(app_description: str) -> Dict[str, Any]:
    """
    Generate OpenAPI extension with enhanced documentation.
    
    Args:
        app_description: Description of the API application
        
    Returns:
        Dictionary containing OpenAPI extension
    """
    return {
        "info": {
            "x-logo": {
                "url": "/static/logo.png",
                "backgroundColor": "#FFFFFF",
                "altText": "PyCommerce Logo"
            },
            "x-documentation": [
                {
                    "name": "Introduction",
                    "content": app_description
                },
                {
                    "name": "Authentication",
                    "content": """
                    # Authentication

                    Most endpoints in the PyCommerce API require authentication using JWT tokens.

                    ## Obtaining a Token

                    To obtain a token, make a POST request to `/api/auth/login` with your username and password:

                    ```json
                    {
                      "username": "admin@example.com",
                      "password": "your_password"
                    }
                    ```

                    ## Using the Token

                    Include the token in the `Authorization` header of your requests:

                    ```
                    Authorization: Bearer your_token_here
                    ```

                    ## Token Expiration

                    Tokens expire after a set period (usually 1 hour). When a token expires, use the refresh token to get a new one by making a POST request to `/api/auth/refresh`.
                    """
                },
                {
                    "name": "Multi-tenancy",
                    "content": """
                    # Multi-tenancy

                    PyCommerce uses a multi-tenant architecture where each tenant represents a separate store or business.

                    ## Tenant Context

                    When making API requests, specify the tenant context in one of these ways:

                    1. **Header**: Include the `X-Tenant-ID` header with the tenant ID
                    2. **Subdomain**: Use a tenant-specific subdomain (e.g., `tenant-name.example.com`)
                    3. **URL Path**: Some API endpoints include the tenant ID in the URL path

                    ## Tenant Isolation

                    Data is strictly isolated between tenants. You cannot access data from one tenant while operating in the context of another tenant.
                    """
                },
                {
                    "name": "Rate Limiting",
                    "content": """
                    # Rate Limiting

                    The API enforces rate limiting to ensure fair usage. The limits vary by endpoint and authentication status.

                    ## Rate Limit Headers

                    Rate limit information is included in response headers:

                    - `X-RateLimit-Limit`: Maximum number of requests allowed in the time window
                    - `X-RateLimit-Remaining`: Number of requests remaining in the current window
                    - `X-RateLimit-Reset`: Time in seconds until the rate limit window resets

                    ## Rate Limit Exceeded

                    If you exceed the rate limit, the API will respond with a 429 (Too Many Requests) status code.
                    """
                },
                {
                    "name": "Error Handling",
                    "content": """
                    # Error Handling

                    The API uses standard HTTP status codes and returns detailed error responses.

                    ## Error Response Format

                    ```json
                    {
                      "detail": "Error message explaining what went wrong",
                      "code": "ERROR_CODE",
                      "field": "field_with_error"
                    }
                    ```

                    ## Common Error Codes

                    - `400 Bad Request`: Invalid request data
                    - `401 Unauthorized`: Authentication required
                    - `403 Forbidden`: Permission denied
                    - `404 Not Found`: Resource not found
                    - `409 Conflict`: Resource conflict (e.g., duplicate entry)
                    - `422 Unprocessable Entity`: Validation error
                    - `429 Too Many Requests`: Rate limit exceeded
                    - `500 Internal Server Error`: Server error
                    """
                }
            ]
        },
        "components": {
            "securitySchemes": {
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
            },
            "parameters": {
                "tenantId": {
                    "name": "X-Tenant-ID",
                    "in": "header",
                    "description": "ID of the tenant to operate on",
                    "required": False,
                    "schema": {
                        "type": "string",
                        "format": "uuid"
                    }
                },
                "limitParam": {
                    "name": "limit",
                    "in": "query",
                    "description": "Maximum number of items to return",
                    "required": False,
                    "schema": {
                        "type": "integer",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 1000
                    }
                },
                "offsetParam": {
                    "name": "offset",
                    "in": "query",
                    "description": "Number of items to skip for pagination",
                    "required": False,
                    "schema": {
                        "type": "integer",
                        "default": 0,
                        "minimum": 0
                    }
                }
            },
            "responses": {
                "UnauthorizedError": {
                    "description": "Authentication required",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "detail": {
                                        "type": "string",
                                        "example": "Not authenticated"
                                    }
                                }
                            }
                        }
                    }
                },
                "ForbiddenError": {
                    "description": "Permission denied",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "detail": {
                                        "type": "string",
                                        "example": "Not enough permissions"
                                    }
                                }
                            }
                        }
                    }
                },
                "NotFoundError": {
                    "description": "Resource not found",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "detail": {
                                        "type": "string",
                                        "example": "Resource not found"
                                    }
                                }
                            }
                        }
                    }
                },
                "ValidationError": {
                    "description": "Validation error",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "detail": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "loc": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "string"
                                                    },
                                                    "example": ["body", "name"]
                                                },
                                                "msg": {
                                                    "type": "string",
                                                    "example": "field required"
                                                },
                                                "type": {
                                                    "type": "string",
                                                    "example": "value_error.missing"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "security": [
            {"bearerAuth": []}
        ],
        "tags": [
            {
                "name": "Authentication",
                "description": "Authentication endpoints"
            },
            {
                "name": "Tenants",
                "description": "Operations related to tenant management"
            },
            {
                "name": "Products",
                "description": "Operations related to product management"
            },
            {
                "name": "Orders",
                "description": "Operations related to order management"
            },
            {
                "name": "Categories",
                "description": "Operations related to product categories"
            },
            {
                "name": "Users",
                "description": "Operations related to user management"
            },
            {
                "name": "Media",
                "description": "Operations related to media management"
            },
            {
                "name": "Pages",
                "description": "Operations related to content pages"
            }
        ]
    }