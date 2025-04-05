
"""
Payment plugin configuration.

This module provides configuration settings for payment plugins.
"""

import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Stripe Configuration
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_ENABLED = os.getenv("STRIPE_ENABLED", "true").lower() in ("true", "1", "yes")

# PayPal Configuration
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "")
PAYPAL_ENABLED = os.getenv("PAYPAL_ENABLED", "true").lower() in ("true", "1", "yes")
PAYPAL_SANDBOX = os.getenv("PAYPAL_SANDBOX", "true").lower() in ("true", "1", "yes")

# Default configurations for testing/development
if not STRIPE_API_KEY and os.environ.get("ENVIRONMENT", "development") == "development":
    logger.info("Using development Stripe credentials")
    STRIPE_API_KEY = "sk_test_development_only"
    STRIPE_ENABLED = True

if not (PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET) and os.environ.get("ENVIRONMENT", "development") == "development":
    logger.info("Using development PayPal credentials")
    PAYPAL_CLIENT_ID = "test_client_id"
    PAYPAL_CLIENT_SECRET = "test_client_secret"
    PAYPAL_ENABLED = True
    PAYPAL_SANDBOX = True
