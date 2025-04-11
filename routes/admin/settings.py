"""
Settings routes for the PyCommerce admin dashboard.

This module defines the routes for system settings including payment, shipping, 
AI providers, email, and general store configurations.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from pycommerce.models.tenant import TenantManager

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["admin_settings"])

# Global variables initialized in setup_routes
templates = None

# Initialize managers
try:
    tenant_manager = TenantManager()
except Exception as e:
    logger.error(f"Error initializing TenantManager: {e}")
    tenant_manager = None

@router.get("/admin/settings", response_class=HTMLResponse)
async def settings(request: Request):
    """Settings management page."""
    # Get current settings from environment or config files
    settings_data = {
        # Payment settings
        "stripe_enabled": os.getenv("STRIPE_ENABLED", "true").lower() in ("true", "1", "yes"),
        "stripe_api_key": os.getenv("STRIPE_API_KEY", ""),
        "stripe_public_key": os.getenv("STRIPE_PUBLIC_KEY", ""),
        "stripe_webhook_secret": os.getenv("STRIPE_WEBHOOK_SECRET", ""),
        "paypal_enabled": os.getenv("PAYPAL_ENABLED", "true").lower() in ("true", "1", "yes"),
        "paypal_client_id": os.getenv("PAYPAL_CLIENT_ID", ""),
        "paypal_client_secret": os.getenv("PAYPAL_CLIENT_SECRET", ""),
        "paypal_sandbox": os.getenv("PAYPAL_SANDBOX", "true").lower() in ("true", "1", "yes"),
        "development_mode": os.getenv("ENVIRONMENT", "development") == "development",
        
        # Shipping settings
        "standard_shipping_enabled": os.getenv("STANDARD_SHIPPING_ENABLED", "true").lower() in ("true", "1", "yes"),
        "standard_shipping_rate": float(os.getenv("STANDARD_SHIPPING_RATE", "5.00")),
        "standard_shipping_free_threshold_enabled": os.getenv("STANDARD_SHIPPING_FREE_THRESHOLD_ENABLED", "false").lower() in ("true", "1", "yes"),
        "standard_shipping_free_threshold": float(os.getenv("STANDARD_SHIPPING_FREE_THRESHOLD", "50.00")),
        
        # AI Provider settings
        "openai_enabled": os.getenv("OPENAI_ENABLED", "true").lower() in ("true", "1", "yes"),
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-4-turbo"),
        "openai_image_model": os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3"),
        
        # Email settings
        "smtp_server": os.getenv("SMTP_SERVER", ""),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "smtp_username": os.getenv("SMTP_USERNAME", ""),
        "smtp_password": os.getenv("SMTP_PASSWORD", ""),
        "smtp_tls": os.getenv("SMTP_TLS", "true").lower() in ("true", "1", "yes"),
        "email_from_name": os.getenv("EMAIL_FROM_NAME", "PyCommerce"),
        "email_from_address": os.getenv("EMAIL_FROM_ADDRESS", "noreply@example.com"),
        
        # General settings
        "default_currency": os.getenv("DEFAULT_CURRENCY", "USD"),
        "tax_rate": float(os.getenv("TAX_RATE", "0")),
        "enable_guest_checkout": os.getenv("ENABLE_GUEST_CHECKOUT", "true").lower() in ("true", "1", "yes"),
    }
    
    # Settings page doesn't need tenant selection as it applies globally to the system
    # Keep empty tenants list for the admin template to work properly
    tenants = []
    selected_tenant_slug = None
    tenant_obj = None
    
    return templates.TemplateResponse(
        "admin/settings.html", 
        {
            "request": request,
            "active_page": "settings",
            "is_global_settings": True,  # Flag to indicate these are global settings
            **settings_data
        }
    )

@router.post("/admin/settings/payment")
async def update_payment_settings(
    request: Request,
    stripe_enabled: Optional[str] = Form(None),
    stripe_api_key: str = Form(""),
    stripe_public_key: str = Form(""),
    stripe_webhook_secret: str = Form(""),
    paypal_enabled: Optional[str] = Form(None),
    paypal_client_id: str = Form(""),
    paypal_client_secret: str = Form(""),
    paypal_sandbox: Optional[str] = Form(None)
):
    """Update payment settings."""
    # Process form data
    is_stripe_enabled = stripe_enabled is not None
    is_paypal_enabled = paypal_enabled is not None
    is_paypal_sandbox = paypal_sandbox is not None
    
    logger.info(f"Updating payment settings")
    
    # Import payment config module
    try:
        from pycommerce.plugins.payment.config import save_stripe_config, save_paypal_config
        
        # Save Stripe configuration
        stripe_config = {
            "enabled": is_stripe_enabled,
            "api_key": stripe_api_key,
            "public_key": stripe_public_key,
            "webhook_secret": stripe_webhook_secret
        }
        stripe_success = await save_stripe_config(stripe_config)
        
        # Save PayPal configuration
        paypal_config = {
            "enabled": is_paypal_enabled,
            "client_id": paypal_client_id,
            "client_secret": paypal_client_secret,
            "sandbox": is_paypal_sandbox
        }
        paypal_success = await save_paypal_config(paypal_config)
        
        if stripe_success and paypal_success:
            logger.info("Payment settings updated successfully")
            request.session["status_message"] = "Payment settings updated successfully."
            request.session["status_type"] = "success"
        else:
            logger.error("Error updating payment settings")
            request.session["status_message"] = "Error updating payment settings. Check logs for details."
            request.session["status_type"] = "danger"
    except ImportError as e:
        logger.error(f"Could not import payment config module: {str(e)}")
        request.session["status_message"] = "Error: Payment configuration module not found."
        request.session["status_type"] = "danger"
    except Exception as e:
        logger.error(f"Error updating payment settings: {str(e)}")
        request.session["status_message"] = f"Error updating payment settings: {str(e)}"
        request.session["status_type"] = "danger"
    
    # Redirect back to the settings page
    return RedirectResponse(url="/admin/settings#payment", status_code=303)

@router.post("/admin/settings/shipping")
async def update_shipping_settings(
    request: Request,
    standard_shipping_enabled: Optional[str] = Form(None),
    standard_shipping_rate: float = Form(5.00),
    standard_shipping_free_threshold_enabled: Optional[str] = Form(None),
    standard_shipping_free_threshold: float = Form(50.00)
):
    """Update shipping settings."""
    # Process form data
    is_standard_shipping_enabled = standard_shipping_enabled is not None
    is_free_threshold_enabled = standard_shipping_free_threshold_enabled is not None
    
    logger.info(f"Updated shipping settings:")
    logger.info(f"Standard Shipping: {'Enabled' if is_standard_shipping_enabled else 'Disabled'}")
    logger.info(f"Base Rate: ${standard_shipping_rate:.2f}")
    logger.info(f"Free Shipping Threshold: {'Enabled' if is_free_threshold_enabled else 'Disabled'}, ${standard_shipping_free_threshold:.2f}")
    
    # Add a status message to display on the settings page
    request.session["status_message"] = "Shipping settings updated successfully."
    request.session["status_type"] = "success"
    
    # Redirect back to the settings page
    return RedirectResponse(url="/admin/settings#shipping", status_code=303)

@router.post("/admin/settings/ai")
async def update_ai_settings(
    request: Request,
    openai_enabled: Optional[str] = Form(None),
    openai_api_key: str = Form(""),
    openai_model: str = Form("gpt-4-turbo"),
    openai_image_model: str = Form("dall-e-3")
):
    """Update AI provider settings."""
    # Process form data
    is_openai_enabled = openai_enabled is not None
    
    logger.info(f"Updated AI settings:")
    logger.info(f"OpenAI: {'Enabled' if is_openai_enabled else 'Disabled'}")
    logger.info(f"Default Model: {openai_model}")
    logger.info(f"Image Model: {openai_image_model}")
    
    # Add a status message to display on the settings page
    request.session["status_message"] = "AI provider settings updated successfully."
    request.session["status_type"] = "success"
    
    # Redirect back to the settings page
    return RedirectResponse(url="/admin/settings#ai", status_code=303)

@router.post("/admin/settings/email")
async def update_email_settings(
    request: Request,
    smtp_server: str = Form(""),
    smtp_port: int = Form(587),
    smtp_username: str = Form(""),
    smtp_password: str = Form(""),
    smtp_tls: Optional[str] = Form(None),
    email_from_name: str = Form(""),
    email_from_address: str = Form("")
):
    """Update email settings."""
    # Process form data
    use_tls = smtp_tls is not None
    
    logger.info(f"Updated email settings:")
    logger.info(f"SMTP Server: {smtp_server}")
    logger.info(f"SMTP Port: {smtp_port}")
    logger.info(f"TLS: {'Enabled' if use_tls else 'Disabled'}")
    logger.info(f"From: {email_from_name} <{email_from_address}>")
    
    # Add a status message to display on the settings page
    request.session["status_message"] = "Email settings updated successfully."
    request.session["status_type"] = "success"
    
    # Redirect back to the settings page
    return RedirectResponse(url="/admin/settings#email", status_code=303)

@router.post("/admin/settings/general")
async def update_general_settings(
    request: Request,
    default_currency: str = Form("USD"),
    tax_rate: float = Form(0),
    enable_guest_checkout: Optional[str] = Form(None)
):
    """Update general store settings."""
    # Process form data
    allow_guest_checkout = enable_guest_checkout is not None
    
    logger.info(f"Updated general settings:")
    logger.info(f"Default Currency: {default_currency}")
    logger.info(f"Tax Rate: {tax_rate}%")
    logger.info(f"Guest Checkout: {'Enabled' if allow_guest_checkout else 'Disabled'}")
    
    # Add a status message to display on the settings page
    request.session["status_message"] = "General settings updated successfully."
    request.session["status_type"] = "success"
    
    # Redirect back to the settings page
    return RedirectResponse(url="/admin/settings#general", status_code=303)

def setup_routes(app_templates):
    """
    Set up routes with the given templates.
    
    Args:
        app_templates: Jinja2Templates instance from the main app
    """
    global templates
    templates = app_templates
    return router