
"""
Payment plugin configuration.

This module provides configuration settings for payment plugins, with support
for both environment variables and database-stored settings.
"""

import os
import logging
import asyncio
from typing import Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

# Initialize variables with default values
STRIPE_API_KEY = ""
STRIPE_PUBLIC_KEY = ""
STRIPE_WEBHOOK_SECRET = ""
STRIPE_ENABLED = False

PAYPAL_CLIENT_ID = ""
PAYPAL_CLIENT_SECRET = ""
PAYPAL_ENABLED = False
PAYPAL_SANDBOX = True

# Environment we're running in (development, production, etc.)
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

# Try to import settings service for database configuration
try:
    from pycommerce.services.settings_service import SettingsService
    has_settings_service = True
except ImportError:
    has_settings_service = False

async def _load_settings_from_db():
    """Load settings from database."""
    global STRIPE_API_KEY, STRIPE_PUBLIC_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_ENABLED
    global PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, PAYPAL_ENABLED, PAYPAL_SANDBOX
    
    if not has_settings_service:
        return
        
    try:
        # Load Stripe settings
        stripe_api_key = await SettingsService.get_setting("payment.stripe.api_key", "")
        if stripe_api_key:
            STRIPE_API_KEY = stripe_api_key
            STRIPE_PUBLIC_KEY = await SettingsService.get_setting("payment.stripe.public_key", "")
            STRIPE_WEBHOOK_SECRET = await SettingsService.get_setting("payment.stripe.webhook_secret", "")
            STRIPE_ENABLED = await SettingsService.get_setting("payment.stripe.enabled", False)
            
        # Load PayPal settings
        paypal_client_id = await SettingsService.get_setting("payment.paypal.client_id", "")
        if paypal_client_id:
            PAYPAL_CLIENT_ID = paypal_client_id
            PAYPAL_CLIENT_SECRET = await SettingsService.get_setting("payment.paypal.client_secret", "")
            PAYPAL_ENABLED = await SettingsService.get_setting("payment.paypal.enabled", False)
            PAYPAL_SANDBOX = await SettingsService.get_setting("payment.paypal.sandbox", True)
    except Exception as e:
        logger.error(f"Error loading payment settings from database: {str(e)}")

# Try to load settings from the database
try:
    asyncio.run(_load_settings_from_db())
except RuntimeError:
    # This happens when running inside an existing event loop
    # We'll fall back to environment variables in this case
    logger.info("Could not load settings from database (async loop error)")

# Fall back to environment variables if settings are not in database
if not STRIPE_API_KEY:
    STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")
    STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_ENABLED = os.getenv("STRIPE_ENABLED", "true").lower() in ("true", "1", "yes")

if not PAYPAL_CLIENT_ID:
    PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
    PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "")
    PAYPAL_ENABLED = os.getenv("PAYPAL_ENABLED", "true").lower() in ("true", "1", "yes")
    PAYPAL_SANDBOX = os.getenv("PAYPAL_SANDBOX", "true").lower() in ("true", "1", "yes")

# Default configurations for testing/development
if not STRIPE_API_KEY and ENVIRONMENT == "development":
    logger.info("Using development Stripe credentials")
    STRIPE_API_KEY = "sk_test_51NbHvWJL4GB7BpjzbBkHXhFJ1HQjnZTEGFSbRjixFcDLzSfV5xRBMPVcCnoCXYAQm4r8zhfYzNoTnXKk6Dp3R6X700L5qQjAkI"
    STRIPE_PUBLIC_KEY = "pk_test_51NbHvWJL4GB7BpjzyuRbcoCQa8aOTgipDQxKCnJkEZBfY62WjXVvXrJPkUQdYzsTFLxyWBqedSrP4gX9eYGGY3uA00JETEwOCf"
    STRIPE_ENABLED = True

if not (PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET) and ENVIRONMENT == "development":
    logger.info("Using development PayPal credentials")
    PAYPAL_CLIENT_ID = "AbXm9Ouxql_KLX65kkCYwGkdCODL5VhSDZjwbO-UgU-5_1t5yIH4y-oH7Qm-PXzfJ4YxcXyXwKK-WG0W"
    PAYPAL_CLIENT_SECRET = "EEZaXZ0m9MK7MuJnAw5w8E1QQQOVpnESqCvZBCveGqMmvY4JLPeusyrKOtQ4cvYoEHrv90YZpZvEpYJY"
    PAYPAL_ENABLED = True
    PAYPAL_SANDBOX = True

async def save_stripe_config(config: Dict[str, Any]) -> bool:
    """
    Save Stripe configuration to the database.
    
    Args:
        config: Dictionary containing Stripe configuration
            - api_key: Stripe API key
            - public_key: Stripe public key
            - webhook_secret: Stripe webhook secret
            - enabled: Whether Stripe is enabled
            
    Returns:
        bool: True if successful, False otherwise
    """
    global STRIPE_API_KEY, STRIPE_PUBLIC_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_ENABLED
    
    if not has_settings_service:
        logger.error("Cannot save Stripe config - settings service not available")
        return False
        
    try:
        # Update global variables
        STRIPE_API_KEY = config.get("api_key", STRIPE_API_KEY)
        STRIPE_PUBLIC_KEY = config.get("public_key", STRIPE_PUBLIC_KEY)
        STRIPE_WEBHOOK_SECRET = config.get("webhook_secret", STRIPE_WEBHOOK_SECRET)
        STRIPE_ENABLED = config.get("enabled", STRIPE_ENABLED)
        
        # Save to database
        await SettingsService.set_setting("payment.stripe.api_key", STRIPE_API_KEY, 
                                       "Stripe API secret key", "string")
        await SettingsService.set_setting("payment.stripe.public_key", STRIPE_PUBLIC_KEY, 
                                       "Stripe publishable key", "string")
        await SettingsService.set_setting("payment.stripe.webhook_secret", STRIPE_WEBHOOK_SECRET, 
                                       "Stripe webhook signing secret", "string")
        await SettingsService.set_setting("payment.stripe.enabled", STRIPE_ENABLED, 
                                       "Whether Stripe payments are enabled", "boolean")
        return True
    except Exception as e:
        logger.error(f"Error saving Stripe configuration: {str(e)}")
        return False

async def save_paypal_config(config: Dict[str, Any]) -> bool:
    """
    Save PayPal configuration to the database.
    
    Args:
        config: Dictionary containing PayPal configuration
            - client_id: PayPal client ID
            - client_secret: PayPal client secret
            - sandbox: Whether to use PayPal sandbox
            - enabled: Whether PayPal is enabled
            
    Returns:
        bool: True if successful, False otherwise
    """
    global PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, PAYPAL_ENABLED, PAYPAL_SANDBOX
    
    if not has_settings_service:
        logger.error("Cannot save PayPal config - settings service not available")
        return False
        
    try:
        # Update global variables
        PAYPAL_CLIENT_ID = config.get("client_id", PAYPAL_CLIENT_ID)
        PAYPAL_CLIENT_SECRET = config.get("client_secret", PAYPAL_CLIENT_SECRET)
        PAYPAL_SANDBOX = config.get("sandbox", PAYPAL_SANDBOX)
        PAYPAL_ENABLED = config.get("enabled", PAYPAL_ENABLED)
        
        # Save to database
        await SettingsService.set_setting("payment.paypal.client_id", PAYPAL_CLIENT_ID, 
                                       "PayPal client ID", "string")
        await SettingsService.set_setting("payment.paypal.client_secret", PAYPAL_CLIENT_SECRET, 
                                       "PayPal client secret", "string")
        await SettingsService.set_setting("payment.paypal.sandbox", PAYPAL_SANDBOX, 
                                       "Whether to use PayPal sandbox mode", "boolean")
        await SettingsService.set_setting("payment.paypal.enabled", PAYPAL_ENABLED, 
                                       "Whether PayPal payments are enabled", "boolean")
        return True
    except Exception as e:
        logger.error(f"Error saving PayPal configuration: {str(e)}")
        return False
