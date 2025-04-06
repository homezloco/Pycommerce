
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
    STRIPE_API_KEY = "sk_test_51NbHvWJL4GB7BpjzbBkHXhFJ1HQjnZTEGFSbRjixFcDLzSfV5xRBMPVcCnoCXYAQm4r8zhfYzNoTnXKk6Dp3R6X700L5qQjAkI"
    STRIPE_ENABLED = True
    
    # Add a public key for the frontend
    STRIPE_PUBLIC_KEY = "pk_test_51NbHvWJL4GB7BpjzyuRbcoCQa8aOTgipDQxKCnJkEZBfY62WjXVvXrJPkUQdYzsTFLxyWBqedSrP4gX9eYGGY3uA00JETEwOCf"
else:
    STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "")

if not (PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET) and os.environ.get("ENVIRONMENT", "development") == "development":
    logger.info("Using development PayPal credentials")
    PAYPAL_CLIENT_ID = "AbXm9Ouxql_KLX65kkCYwGkdCODL5VhSDZjwbO-UgU-5_1t5yIH4y-oH7Qm-PXzfJ4YxcXyXwKK-WG0W"
    PAYPAL_CLIENT_SECRET = "EEZaXZ0m9MK7MuJnAw5w8E1QQQOVpnESqCvZBCveGqMmvY4JLPeusyrKOtQ4cvYoEHrv90YZpZvEpYJY"
    PAYPAL_ENABLED = True
    PAYPAL_SANDBOX = True
