# PyCommerce API Reference

## Overview

This document provides a comprehensive reference for all PyCommerce API endpoints, including authentication, core platform APIs, payment processing, and order management.

## Authentication

Most API endpoints require authentication using JWT tokens. Include your token in the Authorization header:

```
Authorization: Bearer YOUR_JWT_TOKEN
```

You can obtain a JWT token by authenticating through the `/api/auth/login` endpoint.

## Base URLs

- **API Base URL**: `/api`
- **Documentation**: `/api/docs` (Swagger UI) or `/api/redoc` (ReDoc)
- **OpenAPI Schema**: `/api/openapi.json`

## Endpoint Categories

- [System Endpoints](#system-endpoints)
- [Tenant Management](#tenant-management)
- [Product Management](#product-management)
- [Category Management](#category-management)
- [Order Management](#order-management)
- [User Management](#user-management)
- [Payment Processing](#payment-processing)
- [Shipping Management](#shipping-management)
- [Media Management](#media-management)
- [Page Builder](#page-builder)

## System Endpoints

### Health Check

**Endpoint:** `GET /api/health`

Check if the API is operational. Does not require authentication.

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "message": "PyCommerce API is running"
}
```

### API Documentation

**Endpoint:** `GET /api/documentation`

Returns links to all API documentation resources.

**Response:**
```json
{
  "message": "PyCommerce API Documentation",
  "version": "1.0.0",
  "documentation_links": {
    "swagger": "/api/docs",
    "redoc": "/api/redoc",
    "openapi_json": "/api/openapi.json"
  }
}
```

## Tenant Management

### List All Tenants

**Endpoint:** `GET /api/tenants`

Get a list of all tenants in the system.

**Response:**
```json
{
  "tenants": [
    {
      "id": "ea6c4bc0-d5aa-4f5c-b769-c51c812a5037",
      "name": "Tech Gadgets",
      "slug": "tech",
      "domain": "tech.pycommerce.com",
      "active": true
    },
    {
      "id": "f8a7b6c5-e4d3-4c2b-a1b0-9f8e7d6c5b4a",
      "name": "Outdoor Adventures",
      "slug": "outdoor",
      "domain": "outdoor.pycommerce.com",
      "active": true
    }
  ],
  "count": 2
}
```

### Get Tenant by ID

**Endpoint:** `GET /api/tenants/{tenant_id}`

Get a specific tenant by ID.

**Response:**
```json
{
  "id": "ea6c4bc0-d5aa-4f5c-b769-c51c812a5037",
  "name": "Tech Gadgets",
  "slug": "tech",
  "domain": "tech.pycommerce.com",
  "active": true,
  "settings": {
    "theme": "default",
    "currency": "USD",
    "shipping_countries": ["US", "CA"],
    "tax_settings": {
      "include_tax": true,
      "tax_rate": 0.08
    }
  }
}
```

### Create Tenant

**Endpoint:** `POST /api/tenants`

Create a new tenant.

**Request Body:**
```json
{
  "name": "Fashion Store",
  "slug": "fashion",
  "domain": "fashion.pycommerce.com"
}
```

**Response:**
```json
{
  "id": "d7e8f9a0-b1c2-4d3e-8f4a-5b6c7d8e9f0a",
  "name": "Fashion Store",
  "slug": "fashion",
  "domain": "fashion.pycommerce.com",
  "active": true,
  "created_at": "2025-03-15T10:30:00Z"
}
```

### Update Tenant

**Endpoint:** `PUT /api/tenants/{tenant_id}`

Update a tenant's information.

**Request Body:**
```json
{
  "name": "Fashion Boutique",
  "domain": "boutique.pycommerce.com",
  "active": true
}
```

**Response:**
```json
{
  "id": "d7e8f9a0-b1c2-4d3e-8f4a-5b6c7d8e9f0a",
  "name": "Fashion Boutique",
  "slug": "fashion",
  "domain": "boutique.pycommerce.com",
  "active": true,
  "updated_at": "2025-03-16T14:45:00Z"
}
```

### Delete Tenant

**Endpoint:** `DELETE /api/tenants/{tenant_id}`

Delete a tenant (soft delete).

**Response:** Status 204 No Content

## Product Management

### List Products

**Endpoint:** `GET /api/products`

Get products for a specific tenant with optional filtering.

**Parameters:**
- `tenant`: The tenant slug (required)
- `category`: Filter by category (optional)
- `min_price`: Filter by minimum price (optional)
- `max_price`: Filter by maximum price (optional)
- `in_stock`: Filter by stock availability (optional)

**Response:**
```json
{
  "products": [
    {
      "id": "b5c6d7e8-f9a0-4b1c-8d2e-3f4a5b6c7d8e",
      "name": "Wireless Headphones",
      "description": "Premium wireless headphones with noise cancellation",
      "price": 129.99,
      "sku": "WH-001",
      "stock": 25,
      "categories": ["Electronics", "Audio"]
    },
    {
      "id": "c6d7e8f9-a0b1-4c2d-8e3f-4a5b6c7d8e9f",
      "name": "Bluetooth Speaker",
      "description": "Waterproof portable Bluetooth speaker",
      "price": 79.99,
      "sku": "BS-002",
      "stock": 42,
      "categories": ["Electronics", "Audio"]
    }
  ],
  "tenant": "tech",
  "count": 2,
  "filters": {
    "category": "Electronics",
    "min_price": 50,
    "max_price": 200,
    "in_stock": true
  }
}
```

### Get Product by ID

**Endpoint:** `GET /api/products/{product_id}`

Get a specific product by ID.

**Response:**
```json
{
  "id": "b5c6d7e8-f9a0-4b1c-8d2e-3f4a5b6c7d8e",
  "name": "Wireless Headphones",
  "description": "Premium wireless headphones with noise cancellation",
  "price": 129.99,
  "sku": "WH-001",
  "stock": 25,
  "categories": ["Electronics", "Audio"],
  "images": [
    {
      "id": "img-1",
      "url": "https://example.com/images/headphones-1.jpg",
      "alt": "Main product image"
    }
  ],
  "metadata": {
    "brand": "AudioTech",
    "color": "Black",
    "warranty": "2 years"
  },
  "created_at": "2025-02-10T15:30:00Z",
  "updated_at": "2025-03-05T11:20:00Z",
  "tenant_id": "ea6c4bc0-d5aa-4f5c-b769-c51c812a5037"
}
```

### Create Product

**Endpoint:** `POST /api/products`

Create a new product.

**Request Body:**
```json
{
  "name": "Smartwatch Pro",
  "description": "Advanced smartwatch with health monitoring",
  "price": 199.99,
  "sku": "SW-001",
  "stock": 50,
  "categories": ["Electronics", "Wearables"],
  "metadata": {
    "tenant_id": "ea6c4bc0-d5aa-4f5c-b769-c51c812a5037",
    "brand": "TechWear",
    "color": "Silver"
  }
}
```

**Response:**
```json
{
  "id": "e8f9a0b1-c2d3-4e4f-9a5b-6c7d8e9f0a1b",
  "name": "Smartwatch Pro",
  "description": "Advanced smartwatch with health monitoring",
  "price": 199.99,
  "sku": "SW-001",
  "stock": 50,
  "categories": ["Electronics", "Wearables"],
  "created_at": "2025-03-20T10:00:00Z",
  "tenant_id": "ea6c4bc0-d5aa-4f5c-b769-c51c812a5037"
}
```

### Update Product

**Endpoint:** `PUT /api/products/{product_id}`

Update a product's information.

**Request Body:**
```json
{
  "name": "Smartwatch Pro 2",
  "price": 219.99,
  "stock": 75,
  "categories": ["Electronics", "Wearables", "Premium"]
}
```

**Response:**
```json
{
  "id": "e8f9a0b1-c2d3-4e4f-9a5b-6c7d8e9f0a1b",
  "name": "Smartwatch Pro 2",
  "description": "Advanced smartwatch with health monitoring",
  "price": 219.99,
  "sku": "SW-001",
  "stock": 75,
  "categories": ["Electronics", "Wearables", "Premium"],
  "updated_at": "2025-03-21T09:30:00Z"
}
```

### Delete Product

**Endpoint:** `DELETE /api/products/{product_id}`

Delete a product.

**Response:** Status 204 No Content

## Category Management

### List Categories

**Endpoint:** `GET /api/categories`

Get categories for a specific tenant.

**Parameters:**
- `tenant`: The tenant slug (required)
- `parent_id`: Filter by parent category ID (optional)

**Response:**
```json
{
  "categories": [
    {
      "id": "cat-1",
      "name": "Electronics",
      "slug": "electronics",
      "description": "Electronic devices and gadgets",
      "parent_id": null,
      "has_children": true
    },
    {
      "id": "cat-2",
      "name": "Audio",
      "slug": "audio",
      "description": "Audio equipment",
      "parent_id": "cat-1",
      "has_children": false
    }
  ],
  "tenant": "tech",
  "count": 2
}
```

### Get Category by ID

**Endpoint:** `GET /api/categories/{category_id}`

Get a specific category by ID.

**Response:**
```json
{
  "id": "cat-1",
  "name": "Electronics",
  "slug": "electronics",
  "description": "Electronic devices and gadgets",
  "parent_id": null,
  "has_children": true,
  "children": [
    {
      "id": "cat-2",
      "name": "Audio",
      "slug": "audio"
    },
    {
      "id": "cat-3",
      "name": "Wearables",
      "slug": "wearables"
    }
  ],
  "tenant_id": "ea6c4bc0-d5aa-4f5c-b769-c51c812a5037",
  "created_at": "2025-02-01T10:00:00Z",
  "updated_at": "2025-02-15T14:30:00Z"
}
```

### Create Category

**Endpoint:** `POST /api/categories`

Create a new category.

**Request Body:**
```json
{
  "name": "Smart Home",
  "slug": "smart-home",
  "description": "Smart home devices and accessories",
  "parent_id": "cat-1",
  "tenant_id": "ea6c4bc0-d5aa-4f5c-b769-c51c812a5037"
}
```

**Response:**
```json
{
  "id": "cat-4",
  "name": "Smart Home",
  "slug": "smart-home",
  "description": "Smart home devices and accessories",
  "parent_id": "cat-1",
  "has_children": false,
  "tenant_id": "ea6c4bc0-d5aa-4f5c-b769-c51c812a5037",
  "created_at": "2025-03-22T11:15:00Z"
}
```

### Update Category

**Endpoint:** `PUT /api/categories/{category_id}`

Update a category's information.

**Request Body:**
```json
{
  "name": "Smart Home & IoT",
  "description": "Smart home devices and Internet of Things products"
}
```

**Response:**
```json
{
  "id": "cat-4",
  "name": "Smart Home & IoT",
  "slug": "smart-home",
  "description": "Smart home devices and Internet of Things products",
  "parent_id": "cat-1",
  "has_children": false,
  "updated_at": "2025-03-23T09:45:00Z"
}
```

### Delete Category

**Endpoint:** `DELETE /api/categories/{category_id}`

Delete a category.

**Response:** Status 204 No Content

## Order Management

### List Orders

**Endpoint:** `GET /api/orders`

Get orders for a specific tenant with optional filtering.

**Parameters:**
- `tenant`: The tenant slug (required)
- `status`: Filter by order status (optional)
- `customer_id`: Filter by customer ID (optional)
- `date_from`: Filter by start date (optional)
- `date_to`: Filter by end date (optional)

**Response:**
```json
{
  "orders": [
    {
      "id": "d7e8f9a0-b1c2-4d3e-8f4a-5b6c7d8e9f0a",
      "customer_name": "Jane Smith",
      "customer_email": "jane.smith@example.com",
      "status": "completed",
      "total": 209.98,
      "created_at": "2025-03-15T10:30:00Z",
      "items_count": 2,
      "shipping_method": "standard"
    },
    {
      "id": "e8f9a0b1-c2d3-4e4f-9a5b-6c7d8e9f0a1b",
      "customer_name": "John Doe",
      "customer_email": "john.doe@example.com",
      "status": "completed",
      "total": 129.99,
      "created_at": "2025-03-16T14:45:00Z",
      "items_count": 1,
      "shipping_method": "express"
    }
  ],
  "tenant": "tech",
  "count": 2,
  "filters": {
    "status": "completed",
    "customer_id": null
  }
}
```

### Get Order Details

**Endpoint:** `GET /api/orders/{order_id}`

Get detailed information about a specific order.

**Response:**
```json
{
  "id": "d7e8f9a0-b1c2-4d3e-8f4a-5b6c7d8e9f0a",
  "customer": {
    "id": "f9a0b1c2-d3e4-4f5a-9b6c-7d8e9f0a1b2c",
    "name": "Jane Smith",
    "email": "jane.smith@example.com",
    "phone": "+1234567890"
  },
  "status": "completed",
  "total": 209.98,
  "subtotal": 189.98,
  "tax": 10.00,
  "shipping_cost": 10.00,
  "material_cost": 95.00,
  "labor_cost": 30.00,
  "profit_margin": 64.98,
  "profit_percentage": 34.2,
  "created_at": "2025-03-15T10:30:00Z",
  "updated_at": "2025-03-15T14:20:00Z",
  "shipping_address": {
    "line1": "123 Main St",
    "line2": "Apt 4B",
    "city": "Metropolis",
    "state": "NY",
    "postal_code": "10001",
    "country": "USA"
  },
  "billing_address": {
    "line1": "123 Main St",
    "line2": "Apt 4B",
    "city": "Metropolis",
    "state": "NY",
    "postal_code": "10001",
    "country": "USA"
  },
  "shipping_method": "standard",
  "payment_method": "credit_card",
  "payment_status": "paid",
  "notes": "Please leave at front door",
  "items": [
    {
      "id": "a0b1c2d3-e4f5-4a6b-9c7d-8e9f0a1b2c3d",
      "product_id": "b5c6d7e8-f9a0-4b1c-8d2e-3f4a5b6c7d8e",
      "name": "Wireless Headphones",
      "quantity": 1,
      "unit_price": 129.99,
      "total_price": 129.99,
      "material_cost": 65.00,
      "labor_cost": 20.00,
      "profit": 44.99
    },
    {
      "id": "b1c2d3e4-f5a6-4b7c-9d8e-9f0a1b2c3d4e",
      "product_id": "c6d7e8f9-a0b1-4c2d-8e3f-4a5b6c7d8e9f",
      "name": "Bluetooth Speaker",
      "quantity": 1,
      "unit_price": 79.99,
      "total_price": 79.99,
      "material_cost": 30.00,
      "labor_cost": 10.00,
      "profit": 39.99
    }
  ],
  "tenant_id": "ea6c4bc0-d5aa-4f5c-b769-c51c812a5037"
}
```

### Create Order

**Endpoint:** `POST /api/orders`

Create a new order.

**Request Body:**
```json
{
  "tenant_id": "ea6c4bc0-d5aa-4f5c-b769-c51c812a5037",
  "customer": {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1234567890"
  },
  "shipping_address": {
    "line1": "456 Oak St",
    "line2": "",
    "city": "Springfield",
    "state": "IL",
    "postal_code": "62701",
    "country": "USA"
  },
  "billing_address": {
    "line1": "456 Oak St",
    "line2": "",
    "city": "Springfield",
    "state": "IL",
    "postal_code": "62701",
    "country": "USA"
  },
  "shipping_method": "express",
  "notes": "Please call before delivery",
  "items": [
    {
      "product_id": "b5c6d7e8-f9a0-4b1c-8d2e-3f4a5b6c7d8e",
      "quantity": 2
    }
  ]
}
```

**Response:**
```json
{
  "id": "g0h1i2j3-k4l5-6m7n-8o9p-0q1r2s3t4u5v",
  "customer": {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1234567890"
  },
  "status": "pending",
  "total": 269.98,
  "subtotal": 259.98,
  "tax": 0.00,
  "shipping_cost": 10.00,
  "created_at": "2025-03-20T10:00:00Z",
  "updated_at": "2025-03-20T10:00:00Z",
  "shipping_address": {
    "line1": "456 Oak St",
    "line2": "",
    "city": "Springfield",
    "state": "IL",
    "postal_code": "62701",
    "country": "USA"
  },
  "billing_address": {
    "line1": "456 Oak St",
    "line2": "",
    "city": "Springfield",
    "state": "IL",
    "postal_code": "62701",
    "country": "USA"
  },
  "shipping_method": "express",
  "payment_method": null,
  "payment_status": "pending",
  "notes": "Please call before delivery",
  "items": [
    {
      "id": "c2d3e4f5-g6h7-8i9j-0k1l-2m3n4o5p6q7r",
      "product_id": "b5c6d7e8-f9a0-4b1c-8d2e-3f4a5b6c7d8e",
      "name": "Wireless Headphones",
      "quantity": 2,
      "unit_price": 129.99,
      "total_price": 259.98
    }
  ],
  "tenant_id": "ea6c4bc0-d5aa-4f5c-b769-c51c812a5037"
}
```

### Update Order Status

**Endpoint:** `PATCH /api/orders/{order_id}/status`

Update an order's status.

**Request Body:**
```json
{
  "status": "shipped",
  "tracking_number": "1Z999AA10123456784",
  "notify_customer": true
}
```

**Response:**
```json
{
  "id": "d7e8f9a0-b1c2-4d3e-8f4a-5b6c7d8e9f0a",
  "status": "shipped",
  "previous_status": "processing",
  "updated_at": "2025-03-16T09:30:00Z",
  "tracking_number": "1Z999AA10123456784",
  "notification_sent": true
}
```

### Add Order Note

**Endpoint:** `POST /api/orders/{order_id}/notes`

Add a note to an order.

**Request Body:**
```json
{
  "content": "Customer requested special packaging",
  "is_internal": true,
  "author": "Jane (Support Team)"
}
```

**Response:**
```json
{
  "id": "note-123",
  "content": "Customer requested special packaging",
  "is_internal": true,
  "author": "Jane (Support Team)",
  "created_at": "2025-03-16T10:45:00Z",
  "order_id": "d7e8f9a0-b1c2-4d3e-8f4a-5b6c7d8e9f0a"
}
```

## Payment Processing

### Create Stripe Checkout Session (JSON API)

**Endpoint:** `POST /stripe-demo/create-checkout-session-json`

Create a Stripe checkout session and return a JSON response with the checkout URL. This endpoint is optimized for client-side JavaScript applications using fetch API and resolves browser content decoding issues.

**Request Body:**
```json
{
  "items": [
    {
      "id": "prod_1",
      "name": "Premium Headphones",
      "price": 149.99,
      "quantity": 1
    },
    {
      "id": "prod_2",
      "name": "Wireless Speaker",
      "price": 79.99,
      "quantity": 2
    }
  ],
  "order_id": "order-123-abc"
}
```

**Success Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/pay/cs_test_a1b2c3...",
  "session_id": "cs_test_a1b2c3..."
}
```

**Error Response:**
```json
{
  "error": "Detailed error message describing the issue"
}
```

### Stripe Webhook

**Endpoint:** `POST /checkout/stripe/webhook`

Stripe webhook endpoint for handling payment events. This endpoint is called by Stripe when payment events occur.

**Headers:**
- `Stripe-Signature`: The signature header from Stripe

**Body:**
Raw JSON body from Stripe.

**Response:**
```json
{
  "received": true
}
```

### Get Payment Methods

**Endpoint:** `GET /api/payment-methods`

Get available payment methods for a tenant.

**Parameters:**
- `tenant`: The tenant slug (required)

**Response:**
```json
{
  "payment_methods": [
    {
      "id": "stripe",
      "name": "Credit Card (Stripe)",
      "description": "Pay securely with your credit card",
      "enabled": true,
      "icon": "https://example.com/icons/stripe.svg"
    },
    {
      "id": "paypal",
      "name": "PayPal",
      "description": "Pay using your PayPal account",
      "enabled": true,
      "icon": "https://example.com/icons/paypal.svg"
    }
  ],
  "tenant": "tech",
  "count": 2
}
```

## Shipping Management

### Get Shipping Methods

**Endpoint:** `GET /api/shipping-methods`

Get available shipping methods for a tenant.

**Parameters:**
- `tenant`: The tenant slug (required)
- `country`: Destination country (optional)

**Response:**
```json
{
  "shipping_methods": [
    {
      "id": "standard",
      "name": "Standard Shipping",
      "description": "5-7 business days",
      "price": 5.99,
      "estimated_days": 7
    },
    {
      "id": "express",
      "name": "Express Shipping",
      "description": "2-3 business days",
      "price": 12.99,
      "estimated_days": 3
    },
    {
      "id": "premium",
      "name": "Premium Shipping",
      "description": "Next-day delivery (domestic)",
      "price": 19.99,
      "estimated_days": 1
    }
  ],
  "tenant": "tech",
  "country": "US",
  "count": 3
}
```

### Calculate Shipping Rate

**Endpoint:** `POST /api/shipping/calculate`

Calculate shipping rates for a specific order.

**Request Body:**
```json
{
  "tenant_id": "ea6c4bc0-d5aa-4f5c-b769-c51c812a5037",
  "items": [
    {
      "product_id": "b5c6d7e8-f9a0-4b1c-8d2e-3f4a5b6c7d8e",
      "quantity": 2
    }
  ],
  "shipping_address": {
    "country": "US",
    "state": "CA",
    "postal_code": "90210"
  }
}
```

**Response:**
```json
{
  "shipping_options": [
    {
      "id": "standard",
      "name": "Standard Shipping",
      "description": "5-7 business days",
      "price": 5.99,
      "estimated_days": 7
    },
    {
      "id": "express",
      "name": "Express Shipping",
      "description": "2-3 business days",
      "price": 10.49,
      "estimated_days": 3
    },
    {
      "id": "premium",
      "name": "Premium Shipping",
      "description": "Next-day delivery (domestic)",
      "price": 14.99,
      "estimated_days": 1
    }
  ],
  "tenant": "tech",
  "subtotal": 259.98,
  "total_weight": "1.2kg"
}
```

## Media Management

### List Media

**Endpoint:** `GET /api/media`

List media files for a tenant.

**Parameters:**
- `tenant`: The tenant slug (required)
- `type`: Filter by media type (image, video, document) (optional)
- `search`: Search by filename or description (optional)

**Response:**
```json
{
  "media": [
    {
      "id": "media-1",
      "filename": "product-image-1.jpg",
      "url": "https://example.com/media/product-image-1.jpg",
      "type": "image",
      "mime_type": "image/jpeg",
      "size": 245789,
      "dimensions": {
        "width": 1200,
        "height": 800
      },
      "created_at": "2025-02-10T12:30:00Z"
    },
    {
      "id": "media-2",
      "filename": "product-specs.pdf",
      "url": "https://example.com/media/product-specs.pdf",
      "type": "document",
      "mime_type": "application/pdf",
      "size": 1245678,
      "created_at": "2025-02-15T09:45:00Z"
    }
  ],
  "tenant": "tech",
  "count": 2
}
```

### Upload Media

**Endpoint:** `POST /api/media`

Upload a new media file.

**Request:** Multipart form data
- `file`: The file to upload
- `tenant_id`: The tenant ID
- `description`: Optional description
- `alt_text`: Optional alt text for accessibility (for images)
- `sharing_level`: Sharing level (private, tenant, all)

**Response:**
```json
{
  "id": "media-3",
  "filename": "new-product.jpg",
  "url": "https://example.com/media/new-product.jpg",
  "type": "image",
  "mime_type": "image/jpeg",
  "size": 345678,
  "dimensions": {
    "width": 1500,
    "height": 1000
  },
  "description": "New product image",
  "alt_text": "Image of the new smartwatch product",
  "sharing_level": "tenant",
  "created_at": "2025-03-20T14:30:00Z",
  "tenant_id": "ea6c4bc0-d5aa-4f5c-b769-c51c812a5037"
}
```

### Delete Media

**Endpoint:** `DELETE /api/media/{media_id}`

Delete a media file.

**Response:** Status 204 No Content

## Page Builder

### List Pages

**Endpoint:** `GET /api/pages`

List pages for a tenant.

**Parameters:**
- `tenant`: The tenant slug (required)
- `status`: Filter by page status (published, draft) (optional)

**Response:**
```json
{
  "pages": [
    {
      "id": "page-1",
      "title": "About Us",
      "slug": "about",
      "status": "published",
      "created_at": "2025-02-01T10:00:00Z",
      "updated_at": "2025-02-15T14:30:00Z"
    },
    {
      "id": "page-2",
      "title": "Contact Us",
      "slug": "contact",
      "status": "published",
      "created_at": "2025-02-05T11:15:00Z",
      "updated_at": "2025-02-20T09:45:00Z"
    }
  ],
  "tenant": "tech",
  "count": 2
}
```

### Get Page

**Endpoint:** `GET /api/pages/{page_id}`

Get a specific page with its content.

**Response:**
```json
{
  "id": "page-1",
  "title": "About Us",
  "slug": "about",
  "status": "published",
  "meta_title": "About Our Company | Tech Gadgets",
  "meta_description": "Learn about our company and our mission to provide the best tech gadgets.",
  "sections": [
    {
      "id": "section-1",
      "type": "hero",
      "content": {
        "heading": "About Tech Gadgets",
        "subheading": "Technology that enhances your life",
        "background_image": "https://example.com/media/about-banner.jpg"
      }
    },
    {
      "id": "section-2",
      "type": "text_block",
      "content": {
        "heading": "Our Mission",
        "text": "<p>At Tech Gadgets, our mission is to provide high-quality technology that enhances your daily life...</p>"
      }
    }
  ],
  "created_at": "2025-02-01T10:00:00Z",
  "updated_at": "2025-02-15T14:30:00Z",
  "tenant_id": "ea6c4bc0-d5aa-4f5c-b769-c51c812a5037",
  "created_by": "user-1",
  "updated_by": "user-2"
}
```

### Create Page

**Endpoint:** `POST /api/pages`

Create a new page.

**Request Body:**
```json
{
  "title": "Our Team",
  "slug": "team",
  "status": "draft",
  "meta_title": "Meet Our Team | Tech Gadgets",
  "meta_description": "Meet the dedicated team behind Tech Gadgets.",
  "sections": [
    {
      "type": "hero",
      "content": {
        "heading": "Meet Our Team",
        "subheading": "The passionate individuals behind our products"
      }
    }
  ],
  "tenant_id": "ea6c4bc0-d5aa-4f5c-b769-c51c812a5037"
}
```

**Response:**
```json
{
  "id": "page-3",
  "title": "Our Team",
  "slug": "team",
  "status": "draft",
  "meta_title": "Meet Our Team | Tech Gadgets",
  "meta_description": "Meet the dedicated team behind Tech Gadgets.",
  "sections": [
    {
      "id": "section-1",
      "type": "hero",
      "content": {
        "heading": "Meet Our Team",
        "subheading": "The passionate individuals behind our products"
      }
    }
  ],
  "created_at": "2025-03-22T10:00:00Z",
  "updated_at": "2025-03-22T10:00:00Z",
  "tenant_id": "ea6c4bc0-d5aa-4f5c-b769-c51c812a5037",
  "created_by": "user-1"
}
```

### Update Page

**Endpoint:** `PUT /api/pages/{page_id}`

Update a page.

**Request Body:**
```json
{
  "title": "Our Amazing Team",
  "status": "published",
  "sections": [
    {
      "id": "section-1",
      "type": "hero",
      "content": {
        "heading": "Meet Our Amazing Team",
        "subheading": "The passionate individuals behind our products"
      }
    },
    {
      "type": "team_members",
      "content": {
        "heading": "Team Members",
        "members": [
          {
            "name": "John Smith",
            "position": "CEO",
            "bio": "John founded Tech Gadgets in 2020...",
            "image": "https://example.com/media/john.jpg"
          },
          {
            "name": "Jane Doe",
            "position": "CTO",
            "bio": "Jane leads our engineering team...",
            "image": "https://example.com/media/jane.jpg"
          }
        ]
      }
    }
  ]
}
```

**Response:**
```json
{
  "id": "page-3",
  "title": "Our Amazing Team",
  "slug": "team",
  "status": "published",
  "meta_title": "Meet Our Team | Tech Gadgets",
  "meta_description": "Meet the dedicated team behind Tech Gadgets.",
  "sections": [
    {
      "id": "section-1",
      "type": "hero",
      "content": {
        "heading": "Meet Our Amazing Team",
        "subheading": "The passionate individuals behind our products"
      }
    },
    {
      "id": "section-2",
      "type": "team_members",
      "content": {
        "heading": "Team Members",
        "members": [
          {
            "name": "John Smith",
            "position": "CEO",
            "bio": "John founded Tech Gadgets in 2020...",
            "image": "https://example.com/media/john.jpg"
          },
          {
            "name": "Jane Doe",
            "position": "CTO",
            "bio": "Jane leads our engineering team...",
            "image": "https://example.com/media/jane.jpg"
          }
        ]
      }
    }
  ],
  "updated_at": "2025-03-23T11:30:00Z",
  "updated_by": "user-1"
}
```

### Delete Page

**Endpoint:** `DELETE /api/pages/{page_id}`

Delete a page.

**Response:** Status 204 No Content

## Error Handling

All API endpoints return appropriate HTTP status codes and descriptive error messages in JSON format:

```json
{
  "error": "Detailed error message",
  "code": "ERROR_CODE",
  "details": { 
    "field": "Additional error details"
  }
}
```

Common HTTP status codes:
- 200: OK
- 201: Created
- 204: No Content
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error

## API Rate Limiting

The API implements rate limiting to protect against abuse:

- Anonymous requests: 60 requests per hour
- Authenticated requests: 1000 requests per hour

Rate limit headers are included in all responses:
- `X-RateLimit-Limit`: Maximum requests per hour
- `X-RateLimit-Remaining`: Remaining requests in the current period
- `X-RateLimit-Reset`: Timestamp when the limit will reset

When a rate limit is exceeded, a 429 Too Many Requests status is returned with a Retry-After header indicating how long to wait before making another request.