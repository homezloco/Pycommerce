"""
Standard shipping plugin for PyCommerce SDK.

This module implements a basic shipping plugin with fixed rates
and simple shipment tracking.
"""

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
import time
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request

from pycommerce.plugins.shipping.base import ShippingPlugin
from pycommerce.core.exceptions import ShippingError
from pycommerce.models.plugin_config import PluginConfigManager
from pycommerce.models.tenant import TenantManager

logger = logging.getLogger("pycommerce.plugins.shipping.standard")


class StandardShippingPlugin(ShippingPlugin):
    """
    Standard shipping plugin with fixed rates.
    """
    
    @property
    def name(self) -> str:
        return "standard_shipping"
    
    @property
    def version(self) -> str:
        return "0.1.0"
    
    @property
    def description(self) -> str:
        return "Standard shipping with fixed rates and delivery estimates"
    
    def __init__(self):
        """Initialize the standard shipping plugin."""
        self._shipments: Dict[str, Dict[str, Any]] = {}
        self._last_shipment_id = 0
    
    def initialize(self) -> None:
        """Initialize the plugin."""
        logger.info("Initializing Standard shipping plugin")
    
    def get_router(self) -> APIRouter:
        """Create and return a FastAPI router for shipping-specific endpoints."""
        router = APIRouter()
        
        @router.get("/rates", tags=["shipping"])
        def get_shipping_rates(request: Request, country: str, postal_code: str):
            """Get shipping rates for a destination."""
            try:
                rates = self.calculate_rates(
                    items=[],  # Not used in basic implementation
                    destination={"country": country, "postal_code": postal_code},
                    request=request
                )
                return {"rates": rates}
            except Exception as e:
                logger.error(f"Error calculating shipping rates: {str(e)}")
                raise HTTPException(status_code=500, detail="Error calculating shipping rates")
        
        @router.get("/shipments/{shipment_id}", tags=["shipping"])
        def get_shipment(shipment_id: str):
            """Get shipment status."""
            try:
                return self.get_shipment_status(shipment_id)
            except ShippingError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                logger.error(f"Error retrieving shipment: {str(e)}")
                raise HTTPException(status_code=500, detail="Error retrieving shipment")
        
        return router
    
    def get_tenant_from_host(self, request=None):
        """
        Get the current tenant based on the host header.
        
        Args:
            request: The request object (optional)
            
        Returns:
            Tenant ID or None
        """
        tenant_id = None
        try:
            if request and hasattr(request, 'headers'):
                host = request.headers.get('host', '')
                if host:
                    # Extract domain from host (remove port)
                    domain = host.split(':')[0]
                    
                    # Find tenant by domain
                    tenant_manager = TenantManager()
                    tenant = tenant_manager.get_by_domain(domain)
                    
                    if tenant:
                        tenant_id = str(tenant.id)
            
            # If we couldn't get tenant by domain, use the default tenant
            if not tenant_id:
                # Get the first tenant as default
                tenant_manager = TenantManager()
                tenants = tenant_manager.list()
                if tenants:
                    tenant_id = str(tenants[0].id)
        
        except Exception as e:
            logger.error(f"Error getting tenant from host: {str(e)}")
        
        return tenant_id
    
    def get_shipping_config(self, tenant_id=None):
        """
        Get shipping configuration for a tenant.
        
        Args:
            tenant_id: The tenant ID (optional)
            
        Returns:
            Dictionary with shipping configuration
        """
        # Default configuration
        config = {
            "flat_rate_domestic": 5.99,
            "flat_rate_international": 19.99,
            "free_shipping_threshold": 50.00
        }
        
        try:
            if tenant_id:
                # Get configuration from database
                config_manager = PluginConfigManager()
                stored_config = config_manager.get_config("standard-shipping", tenant_id) or {}
                
                # Update config with stored values
                if stored_config:
                    config["flat_rate_domestic"] = stored_config.get("flat_rate_domestic", config["flat_rate_domestic"])
                    config["flat_rate_international"] = stored_config.get("flat_rate_international", config["flat_rate_international"])
                    config["free_shipping_threshold"] = stored_config.get("free_shipping_threshold", config["free_shipping_threshold"])
        
        except Exception as e:
            logger.error(f"Error getting shipping configuration: {str(e)}")
        
        return config
    
    def calculate_rates(self, items: List[Dict[str, Any]], destination: Dict[str, Any], request=None) -> List[Dict[str, Any]]:
        """
        Calculate shipping rates for an order.
        
        Args:
            items: List of items in the order (not used in basic implementation)
            destination: Shipping destination
            request: The request object (optional)
            
        Returns:
            List of available shipping options
            
        Raises:
            ShippingError: If rate calculation fails
        """
        try:
            country = destination.get("country", "").upper()
            
            # Get tenant-specific configuration
            tenant_id = self.get_tenant_from_host(request)
            config = self.get_shipping_config(tenant_id)
            
            # Check if order qualifies for free shipping
            order_total = sum(item.get("price", 0) * item.get("quantity", 1) for item in items)
            free_shipping = (
                config["free_shipping_threshold"] and 
                order_total >= config["free_shipping_threshold"]
            )
            
            # Define standard shipping options
            if country == "US":
                return [
                    {
                        "id": "standard",
                        "name": "Standard Shipping",
                        "description": "Delivery in 3-5 business days",
                        "price": 0 if free_shipping else config["flat_rate_domestic"],
                        "estimated_days": 5,
                        "free_shipping": free_shipping
                    },
                    {
                        "id": "express",
                        "name": "Express Shipping",
                        "description": "Delivery in 1-2 business days",
                        "price": 0 if free_shipping else config["flat_rate_domestic"] * 2,
                        "estimated_days": 2,
                        "free_shipping": free_shipping
                    }
                ]
            elif country in ["CA", "MX"]:
                return [
                    {
                        "id": "standard",
                        "name": "Standard International",
                        "description": "Delivery in 5-7 business days",
                        "price": 0 if free_shipping else config["flat_rate_international"] * 0.7,
                        "estimated_days": 7,
                        "free_shipping": free_shipping
                    },
                    {
                        "id": "express",
                        "name": "Express International",
                        "description": "Delivery in 2-3 business days",
                        "price": 0 if free_shipping else config["flat_rate_international"],
                        "estimated_days": 3,
                        "free_shipping": free_shipping
                    }
                ]
            else:
                return [
                    {
                        "id": "standard",
                        "name": "Standard International",
                        "description": "Delivery in 7-14 business days",
                        "price": 0 if free_shipping else config["flat_rate_international"],
                        "estimated_days": 14,
                        "free_shipping": free_shipping
                    },
                    {
                        "id": "express",
                        "name": "Express International",
                        "description": "Delivery in 3-5 business days",
                        "price": 0 if free_shipping else config["flat_rate_international"] * 2,
                        "estimated_days": 5,
                        "free_shipping": free_shipping
                    }
                ]
        
        except Exception as e:
            logger.error(f"Error calculating shipping rates: {str(e)}")
            raise ShippingError(f"Failed to calculate shipping rates: {str(e)}")
    
    def create_shipment(self, order_id: UUID, shipping_option_id: str, shipping_address: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a shipment for an order.
        
        Args:
            order_id: The ID of the order to create shipment for
            shipping_option_id: The ID of the selected shipping option
            shipping_address: The shipping address
            
        Returns:
            Dictionary containing shipment information
            
        Raises:
            ShippingError: If shipment creation fails
        """
        try:
            # Create a shipment ID
            self._last_shipment_id += 1
            shipment_id = f"SHP{int(time.time())}{self._last_shipment_id}"
            
            # Generate a tracking number
            tracking_number = f"TRK{int(time.time())}{self._last_shipment_id}"
            
            # Determine carrier based on shipping option
            carrier = "Standard Carrier"
            shipping_method = "Standard Shipping"
            
            if shipping_option_id == "express":
                carrier = "Express Carrier"
                shipping_method = "Express Shipping"
            
            # Store shipment information
            shipment = {
                "shipment_id": shipment_id,
                "order_id": str(order_id),
                "tracking_number": tracking_number,
                "tracking_url": f"https://example.com/track/{tracking_number}",
                "carrier": carrier,
                "shipping_method": shipping_method,
                "shipping_address": shipping_address,
                "status": "created",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            self._shipments[shipment_id] = shipment
            
            logger.info(f"Created shipment {shipment_id} for order {order_id}")
            
            return {
                "shipment_id": shipment_id,
                "tracking_number": tracking_number,
                "label_url": f"https://example.com/shipping-labels/{shipment_id}.pdf",
                "carrier": carrier,
                "shipping_method": shipping_method
            }
        
        except Exception as e:
            logger.error(f"Error creating shipment: {str(e)}")
            raise ShippingError(f"Failed to create shipment: {str(e)}")
    
    def get_shipment_status(self, shipment_id: str) -> Dict[str, Any]:
        """
        Get the status of a shipment.
        
        Args:
            shipment_id: The ID of the shipment to check
            
        Returns:
            Dictionary containing shipment status information
            
        Raises:
            ShippingError: If status retrieval fails
        """
        if shipment_id not in self._shipments:
            raise ShippingError(f"Shipment not found: {shipment_id}")
        
        shipment = self._shipments[shipment_id]
        
        return {
            "shipment_id": shipment["shipment_id"],
            "status": shipment["status"],
            "tracking_number": shipment["tracking_number"],
            "tracking_url": shipment["tracking_url"],
            "updated_at": shipment["updated_at"]
        }
    
    def update_shipment_status(self, shipment_id: str, status: str) -> Dict[str, Any]:
        """
        Update the status of a shipment.
        
        Args:
            shipment_id: The ID of the shipment to update
            status: The new status
            
        Returns:
            Dictionary containing updated shipment information
            
        Raises:
            ShippingError: If the shipment is not found
        """
        if shipment_id not in self._shipments:
            raise ShippingError(f"Shipment not found: {shipment_id}")
        
        shipment = self._shipments[shipment_id]
        shipment["status"] = status
        shipment["updated_at"] = datetime.now().isoformat()
        
        logger.info(f"Updated shipment {shipment_id} status to {status}")
        
        return self.get_shipment_status(shipment_id)
