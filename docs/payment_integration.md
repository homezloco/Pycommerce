# Payment Integration Guide

This document provides detailed instructions for integrating payment providers with PyCommerce, focusing on the new JSON-based checkout flow.

## Table of Contents

- [Overview](#overview)
- [Stripe Integration](#stripe-integration)
  - [Configuration](#stripe-configuration)
  - [Client-Side Implementation](#stripe-client-side)
  - [Server-Side Implementation](#stripe-server-side)
  - [Webhook Handling](#stripe-webhooks)
- [PayPal Integration](#paypal-integration)
- [Testing Payments](#testing-payments)
- [Troubleshooting](#troubleshooting)

## Overview

PyCommerce supports multiple payment processors through its extensible plugin system. The platform provides built-in integrations for popular payment providers, including Stripe and PayPal. This guide focuses on the enhanced JSON-based checkout flow that improves browser compatibility and error handling.

## Stripe Integration

### Stripe Configuration

1. Set up your Stripe account at [stripe.com](https://stripe.com)
2. Obtain your API keys from the Stripe dashboard
3. Configure the PyCommerce environment with your Stripe API keys:
   - `STRIPE_SECRET_KEY`: Your Stripe secret key (sensitive, never expose in client-side code)

### Stripe Client-Side

The new JSON API-based checkout uses client-side JavaScript with fetch requests to create a checkout session, avoiding browser content decoding issues that could occur with form submissions.

#### Example Client Implementation

```html
<!-- Include in your checkout page HTML -->
<script>
async function handleCheckout() {
  try {
    // Disable the checkout button to prevent multiple submissions
    const checkoutButton = document.getElementById('checkout-button');
    checkoutButton.disabled = true;
    checkoutButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
    
    // Get the cart items from the page (this will vary based on your implementation)
    const cartItems = JSON.parse(document.getElementById('items-input').value);
    const orderId = document.getElementById('order-id-input').value;
    
    // Create the request options
    const options = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        items: cartItems,
        order_id: orderId
      })
    };
    
    // Send the request to the JSON API endpoint
    const response = await fetch('/stripe-demo/create-checkout-session-json', options);
    
    if (!response.ok) {
      // Try to get error details
      const contentType = response.headers.get('content-type');
      let errorText;
      
      if (contentType && contentType.includes('application/json')) {
        const errorData = await response.json();
        errorText = errorData.error || 'Unknown error occurred';
      } else {
        errorText = await response.text();
      }
      
      throw new Error(errorText || `Request failed with status: ${response.status}`);
    }
    
    // Parse the response as JSON
    const data = await response.json();
    
    // Check if we got a checkout URL
    if (data && data.checkout_url) {
      // Open the checkout URL in a new tab
      window.open(data.checkout_url, '_blank');
    } else {
      throw new Error('No checkout URL received from server');
    }
    
  } catch (error) {
    console.error('Checkout error:', error);
    // Display error to the user
    const errorDiv = document.getElementById('api-error');
    const errorMessage = document.getElementById('error-message');
    if (errorDiv && errorMessage) {
      errorDiv.style.display = 'block';
      errorMessage.textContent = error.message || 'An unexpected error occurred. Please try again.';
    }
    
    // Reset checkout button
    const checkoutButton = document.getElementById('checkout-button');
    if (checkoutButton) {
      checkoutButton.disabled = false;
      checkoutButton.innerHTML = '<i class="fab fa-stripe me-2"></i>Checkout with Stripe';
    }
  }
}
</script>
```

### Stripe Server-Side

The server implementation creates a Stripe checkout session and returns a JSON response with the checkout URL.

#### Key Components

1. **Endpoint**: `/stripe-demo/create-checkout-session-json`
2. **Method**: POST
3. **Request Body**: JSON object with `items` array and `order_id`
4. **Response**: JSON object with `checkout_url` and `session_id`

#### Error Handling

The server-side implementation should handle various error scenarios:

- Missing Stripe API key
- Invalid request data
- Stripe API errors
- Server errors

All errors should be returned as JSON responses with appropriate HTTP status codes and detailed error messages.

### Stripe Webhooks

To handle payment events asynchronously, configure Stripe webhooks to notify your application when payments are completed, failed, or when other significant events occur.

1. Set up a webhook endpoint in your application
2. Configure the webhook in the Stripe dashboard
3. Verify webhook signatures to ensure security

## PayPal Integration

PyCommerce also supports PayPal integration, following a similar pattern to the Stripe integration. See the PayPal integration documentation for details.

## Testing Payments

### Stripe Test Cards

Use these test cards to simulate different payment scenarios in Stripe:

| Card Number         | Scenario           |
|---------------------|-------------------|
| 4242 4242 4242 4242 | Successful payment |
| 4000 0000 0000 0002 | Card declined      |
| 4000 0025 0000 3155 | 3D Secure authentication |

Use any future expiration date, any 3-digit CVC, and any 5-digit postal code for testing.

## Troubleshooting

### Common Issues

#### ERR_CONTENT_DECODING_FAILED

This browser error occurs when there's a mismatch between the declared and actual content encoding of a response. The JSON API approach resolves this by:

1. Using fetch API with JSON explicitly
2. Setting the `Content-Encoding` header to `identity` to disable compression
3. Using a dedicated JSON endpoint instead of form submission

#### Webhook Testing

Use the Stripe CLI to test webhooks locally:

```bash
stripe listen --forward-to http://localhost:5000/webhook
```

#### Server-Side Logging

Enable detailed logging to diagnose issues with checkout creation:

```python
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
```