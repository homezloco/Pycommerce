"""
Standard shipping plugin for PyCommerce SDK.

This module implements a shipping plugin with dynamic rate calculations
based on weight, dimensions, and shipping zones.
"""

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
import time
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Depends, Query, Form, Body

from pycommerce.plugins.shipping.base import ShippingPlugin
from pycommerce.plugins.shipping.calculator import ShippingRateCalculator, PostalCodeCalculator, ShippingZone
from pycommerce.models.shipment import ShipmentManager
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
        self._shipping_calculator = None
        self._store_country = "US"  # Default store country
    
    def initialize(self) -> None:
        """Initialize the plugin."""
        logger.info("Initializing Standard shipping plugin")
        
        # Initialize the shipping calculator with default settings
        self._shipping_calculator = ShippingRateCalculator(
            free_shipping_threshold=50.0  # Default free shipping threshold
        )
    
    def get_router(self) -> APIRouter:
        """Create and return a FastAPI router for shipping-specific endpoints."""
        router = APIRouter()
        
        @router.get("/rates", tags=["shipping"])
        def get_shipping_rates(
            request: Request, 
            country: str, 
            postal_code: str = "",
            include_details: bool = False
        ):
            """
            Get shipping rates for a destination.
            
            Args:
                request: The request object
                country: The destination country code
                postal_code: The destination postal code (optional)
                include_details: Whether to include detailed information (optional)
            """
            try:
                # Create a sample cart with default item for anonymous rate calculation
                sample_items = []
                
                rates = self.calculate_rates(
                    items=sample_items,
                    destination={"country": country, "postal_code": postal_code},
                    request=request
                )
                
                # Remove technical details if not requested
                if not include_details:
                    for rate in rates:
                        rate.pop("billable_weight", None)
                        rate.pop("zone", None)
                
                return {"rates": rates}
            except ShippingError as e:
                logger.error(f"Shipping error: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Error calculating shipping rates: {str(e)}")
                raise HTTPException(status_code=500, detail="Error calculating shipping rates")
        
        @router.post("/calculate", tags=["shipping"])
        async def calculate_shipping_rates(
            request: Request,
            destination: Dict[str, str] = Body(..., description="Shipping destination"),
            items: List[Dict[str, Any]] = Body([], description="Cart items with weights and dimensions")
        ):
            """
            Calculate shipping rates for specific items.
            
            Args:
                request: The request object
                destination: The shipping destination with country and postal_code
                items: Cart items with weights and dimensions
            """
            try:
                rates = self.calculate_rates(
                    items=items,
                    destination=destination,
                    request=request
                )
                return {"rates": rates}
            except ShippingError as e:
                logger.error(f"Shipping error: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Error calculating shipping rates: {str(e)}")
                raise HTTPException(status_code=500, detail="Error calculating shipping rates")
        
        @router.get("/shipments/{shipment_id}", tags=["shipping"])
        def get_shipment(shipment_id: str):
            """
            Get shipment status.
            
            Args:
                shipment_id: The ID of the shipment to retrieve
            """
            try:
                return self.get_shipment_status(shipment_id)
            except ShippingError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                logger.error(f"Error retrieving shipment: {str(e)}")
                raise HTTPException(status_code=500, detail="Error retrieving shipment")
                
        @router.get("/zones", tags=["shipping"])
        def get_shipping_zones():
            """Get available shipping zones."""
            zones = [zone.value for zone in ShippingZone]
            return {"zones": zones}
            
        @router.get("/config", tags=["shipping"])
        def get_current_config(request: Request):
            """
            Get current shipping configuration.
            
            Args:
                request: The request object
            """
            try:
                tenant_id = self.get_tenant_from_host(request)
                config = self.get_shipping_config(tenant_id)
                
                # Remove sensitive information
                if "store_postal_code" in config:
                    config["store_postal_code"] = "***"
                    
                return {"config": config}
            except Exception as e:
                logger.error(f"Error retrieving shipping configuration: {str(e)}")
                raise HTTPException(status_code=500, detail="Error retrieving shipping configuration")
        
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
            # Basic configuration (backwards compatibility)
            "flat_rate_domestic": 5.99,
            "flat_rate_international": 19.99,
            "free_shipping_threshold": 50.00,
            
            # Advanced configuration
            "store_country": "US",
            "dimensional_weight_factor": 200,  # 1 cubic meter = 200kg
            "express_multiplier": 1.75,        # Express costs 75% more
            "premium_multiplier": 2.5,         # Premium costs 150% more
            
            # Weight-based rates for each zone
            "weight_rates": {
                ShippingZone.DOMESTIC.value: {
                    "base_rate": 5.99,
                    "per_kg": 0.5,
                    "min_weight_kg": 0.1,
                },
                ShippingZone.CONTINENTAL.value: {
                    "base_rate": 12.99,
                    "per_kg": 2.0,
                    "min_weight_kg": 0.1,
                },
                ShippingZone.INTERNATIONAL_CLOSE.value: {
                    "base_rate": 19.99,
                    "per_kg": 4.0,
                    "min_weight_kg": 0.1,
                },
                ShippingZone.INTERNATIONAL_FAR.value: {
                    "base_rate": 29.99,
                    "per_kg": 6.0,
                    "min_weight_kg": 0.1,
                }
            }
        }
        
        try:
            if tenant_id:
                # Get configuration from database
                config_manager = PluginConfigManager()
                stored_config = config_manager.get_config("standard-shipping", tenant_id) or {}
                
                # Update basic config with stored values (backwards compatibility)
                if stored_config:
                    for key in ["flat_rate_domestic", "flat_rate_international", "free_shipping_threshold"]:
                        if key in stored_config:
                            config[key] = stored_config.get(key, config[key])
                    
                    # Update advanced config
                    if "store_country" in stored_config:
                        config["store_country"] = stored_config["store_country"]
                    
                    if "dimensional_weight_factor" in stored_config:
                        config["dimensional_weight_factor"] = stored_config["dimensional_weight_factor"]
                    
                    if "express_multiplier" in stored_config:
                        config["express_multiplier"] = stored_config["express_multiplier"]
                    
                    if "premium_multiplier" in stored_config:
                        config["premium_multiplier"] = stored_config["premium_multiplier"]
                    
                    # Update weight-based rates
                    if "weight_rates" in stored_config:
                        for zone, rates in stored_config["weight_rates"].items():
                            if zone in config["weight_rates"]:
                                for rate_key, rate_value in rates.items():
                                    config["weight_rates"][zone][rate_key] = rate_value
        
        except Exception as e:
            logger.error(f"Error getting shipping configuration: {str(e)}")
        
        # Update store country
        self._store_country = config["store_country"]
        
        return config
    
    def calculate_rates(self, items: List[Dict[str, Any]], destination: Dict[str, Any], request=None) -> List[Dict[str, Any]]:
        """
        Calculate shipping rates for an order.
        
        Args:
            items: List of items in the order with weight and dimensions
            destination: Shipping destination with country and postal code
            request: The request object (optional)
            
        Returns:
            List of available shipping options
            
        Raises:
            ShippingError: If rate calculation fails
        """
        try:
            # Ensure destination has required fields
            if not destination:
                raise ShippingError("Destination is required for shipping calculation")
                
            country = destination.get("country", "").upper()
            postal_code = destination.get("postal_code", "")
            
            if not country:
                raise ShippingError("Destination country is required for shipping calculation")
            
            # Get tenant-specific configuration
            tenant_id = self.get_tenant_from_host(request)
            config = self.get_shipping_config(tenant_id)
            
            # Calculate total order value for free shipping
            order_total = sum(item.get("price", 0) * item.get("quantity", 1) for item in items)
            
            # Set up shipping calculator with tenant-specific config
            weight_rates = {}
            for zone_key, zone_rates in config["weight_rates"].items():
                # Convert string keys back to enum
                zone = ShippingZone(zone_key)
                weight_rates[zone] = zone_rates
            
            calculator = ShippingRateCalculator(
                weight_rates=weight_rates,
                dimensional_weight_factor=config.get("dimensional_weight_factor", 200),
                express_multiplier=config.get("express_multiplier", 1.75),
                premium_multiplier=config.get("premium_multiplier", 2.5),
                free_shipping_threshold=config.get("free_shipping_threshold", 0)
            )
            
            # Calculate distance-based rates if we have postal codes
            distance = 0
            if postal_code:
                origin_postal = "00000"  # Default placeholder
                try:
                    # Get store's postal code from tenant config if available
                    # This would be a more sophisticated approach in a real implementation
                    origin_postal = config.get("store_postal_code", origin_postal)
                    
                    # Calculate approximate distance
                    distance = PostalCodeCalculator.calculate_distance(
                        self._store_country, origin_postal, 
                        country, postal_code
                    )
                except Exception as e:
                    logger.warning(f"Could not calculate postal distance: {str(e)}")
            
            # Calculate shipping rates using the calculator
            rates = calculator.calculate_rates(
                items=items,
                origin_country=self._store_country,
                destination_country=country,
                order_total=order_total
            )
            
            # Add distance information if available
            if distance > 0:
                for rate in rates:
                    rate["distance_km"] = distance
            
            # Add postal codes for reference
            for rate in rates:
                rate["destination_postal"] = postal_code
            
            # For legacy compatibility (temporary)
            if len(rates) > 0:
                for rate in rates:
                    if rate["id"] == "standard" and country == "US":
                        rate["name"] = "Standard Shipping"
                    elif rate["id"] == "express" and country == "US":
                        rate["name"] = "Express Shipping"
                    elif rate["id"] == "premium" and country == "US":
                        rate["name"] = "Premium Shipping"
                    elif rate["id"] == "standard":
                        rate["name"] = "Standard International"
                    elif rate["id"] == "express":
                        rate["name"] = "Express International"
                    elif rate["id"] == "premium":
                        rate["name"] = "Premium International"
            
            return rates
        
        except ShippingError as e:
            # Re-raise shipping errors
            raise
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
            elif shipping_option_id == "premium":
                carrier = "Premium Carrier"
                shipping_method = "Premium Shipping"
            
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
