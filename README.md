# PyCommerce SDK

PyCommerce is a modular Python ecommerce SDK with a plugin architecture and FastAPI integration. It provides a flexible framework for building ecommerce applications with support for extensibility through plugins.

## Features

- 🧩 Modular design with a plugin architecture
- 🚀 FastAPI integration for API endpoints
- 🛒 Core ecommerce functionality (products, cart, checkout)
- 🔌 Extensible via plugins (payment gateways, shipping methods, etc.)
- 📝 Clean API design with proper error handling
- ⚡ Support for both synchronous and asynchronous operations
- 💳 Robust payment integrations with Stripe and PayPal
- 🔄 JSON API-based checkout for improved browser compatibility

## Installation

```bash
# TODO: Add installation instructions once package is published
```

## Payment Processing

PyCommerce supports multiple payment processors through its extensible plugin system.

### Stripe Integration

PyCommerce provides seamless integration with Stripe for secure payment processing:

#### Key Features

- JSON API-based Stripe checkout process
- Client-side fetch requests for improved browser compatibility
- Comprehensive error handling with detailed error responses
- Automatic content-encoding handling to prevent decoding issues
- Support for both direct form submission and JavaScript API approaches

#### Checkout Flow

1. Client collects cart data and order information
2. Client sends a JSON request to the `/stripe-demo/create-checkout-session-json` endpoint
3. Server creates a Stripe checkout session and returns the session URL
4. Client redirects the user to the Stripe-hosted checkout page
5. After payment, Stripe redirects back to the success or cancel URL

#### Client-Side Implementation

```javascript
// Example JavaScript for initiating Stripe checkout
async function handleCheckout() {
  try {
    const response = await fetch('/stripe-demo/create-checkout-session-json', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        items: cartItems,
        order_id: orderId
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Unknown error');
    }
    
    const data = await response.json();
    
    // Redirect to Stripe checkout page in a new tab
    if (data.checkout_url) {
      window.open(data.checkout_url, '_blank');
    }
  } catch (error) {
    console.error('Checkout error:', error);
  }
}
```

### PayPal Integration

PyCommerce also includes PayPal integration for additional payment options. This integration follows a similar pattern to the Stripe integration, providing a consistent developer experience across payment providers.
