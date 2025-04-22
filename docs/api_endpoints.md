# API Endpoints Reference

This document provides detailed information about PyCommerce's API endpoints, with a specific focus on the payment processing endpoints.

## Authentication

Most API endpoints require authentication using JWT tokens. Include your token in the Authorization header:

```
Authorization: Bearer YOUR_JWT_TOKEN
```

You can obtain a JWT token by authenticating through the `/api/auth/login` endpoint.

## Base URL

All API endpoints are relative to your PyCommerce instance's base URL.

## Core API Endpoints

### Health Check

```
GET /api/health
```

Check if the API is operational. Does not require authentication.

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "message": "PyCommerce API is running"
}
```

### Get Tenants

```
GET /api/tenants
```

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

### Get Products

```
GET /api/products?tenant=tech&category=Electronics&min_price=50&max_price=200&in_stock=true
```

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

## Payment API Endpoints

### Create Stripe Checkout Session (Form-Based)

```
POST /checkout/stripe/create-checkout-session
```

Create a Stripe checkout session using form submission.

**Form Parameters:**
- `order_id`: The ID of the order
- `items`: JSON string containing items in the cart
- `success_url`: (Optional) URL to redirect to on successful payment
- `cancel_url`: (Optional) URL to redirect to on cancelled payment

**Response:**
Redirects to the Stripe checkout page.

### Create Stripe Checkout Session (JSON API)

```
POST /stripe-demo/create-checkout-session-json
```

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

```
POST /checkout/stripe/webhook
```

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

## Order API Endpoints

### Get Orders

```
GET /api/orders?tenant=tech&status=completed
```

Get orders for a specific tenant with optional filtering.

**Parameters:**
- `tenant`: The tenant slug (required)
- `status`: Filter by order status (optional)
- `customer_id`: Filter by customer ID (optional)

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

```
GET /api/orders/{order_id}
```

Get detailed information about a specific order.

**Path Parameters:**
- `order_id`: The ID of the order

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
      "total_price": 129.99
    },
    {
      "id": "b1c2d3e4-f5a6-4b7c-9d8e-9f0a1b2c3d4e",
      "product_id": "c6d7e8f9-a0b1-4c2d-8e3f-4a5b6c7d8e9f",
      "name": "Bluetooth Speaker",
      "quantity": 1,
      "unit_price": 79.99,
      "total_price": 79.99
    }
  ],
  "tenant_id": "ea6c4bc0-d5aa-4f5c-b769-c51c812a5037"
}
```

### Create Order

```
POST /api/orders
```

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
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error