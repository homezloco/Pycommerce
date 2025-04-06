"""
Shipping rate calculator for PyCommerce SDK.

This module provides calculations for shipping rates based on various factors
like weight, dimensions, distance, and shipping zones.
"""

import logging
import math
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger("pycommerce.plugins.shipping.calculator")


class ShippingZone(str, Enum):
    """Shipping zones for rate calculation."""
    DOMESTIC = "domestic"
    CONTINENTAL = "continental"
    INTERNATIONAL_CLOSE = "international_close"
    INTERNATIONAL_FAR = "international_far"


class ShippingRateCalculator:
    """Calculates shipping rates based on various factors."""
    
    # Default shipping zones mapping
    DEFAULT_ZONES = {
        # Domestic (US to US)
        "US": {
            "US": ShippingZone.DOMESTIC,
            "CA": ShippingZone.CONTINENTAL,
            "MX": ShippingZone.CONTINENTAL,
            "DEFAULT": ShippingZone.INTERNATIONAL_FAR
        },
        # Canadian zones
        "CA": {
            "CA": ShippingZone.DOMESTIC,
            "US": ShippingZone.CONTINENTAL,
            "MX": ShippingZone.CONTINENTAL,
            "DEFAULT": ShippingZone.INTERNATIONAL_FAR
        },
        # European zones - simplified
        "GB": {
            "GB": ShippingZone.DOMESTIC,
            "FR": ShippingZone.CONTINENTAL,
            "DE": ShippingZone.CONTINENTAL,
            "IT": ShippingZone.CONTINENTAL,
            "ES": ShippingZone.CONTINENTAL,
            "DEFAULT": ShippingZone.INTERNATIONAL_CLOSE
        },
        # Default for any country not specifically mapped
        "DEFAULT": {
            "DEFAULT": ShippingZone.INTERNATIONAL_FAR
        }
    }
    
    # Default weight-based rates
    DEFAULT_WEIGHT_RATES = {
        ShippingZone.DOMESTIC: {
            "base_rate": 5.99,
            "per_kg": 0.5,
            "min_weight_kg": 0.1,
        },
        ShippingZone.CONTINENTAL: {
            "base_rate": 12.99,
            "per_kg": 2.0,
            "min_weight_kg": 0.1,
        },
        ShippingZone.INTERNATIONAL_CLOSE: {
            "base_rate": 19.99,
            "per_kg": 4.0,
            "min_weight_kg": 0.1,
        },
        ShippingZone.INTERNATIONAL_FAR: {
            "base_rate": 29.99,
            "per_kg": 6.0,
            "min_weight_kg": 0.1,
        }
    }
    
    # Default dimensional weight factor (kg per cubic meter)
    DEFAULT_DIM_WEIGHT_FACTOR = 200  # 1 cubic meter = 200kg
    
    # Default express multipliers
    DEFAULT_EXPRESS_MULTIPLIER = 1.75  # Express costs 75% more than standard
    
    # Default premium multipliers
    DEFAULT_PREMIUM_MULTIPLIER = 2.5  # Premium costs 150% more than standard
    
    def __init__(
        self,
        zones_mapping: Optional[Dict[str, Dict[str, ShippingZone]]] = None,
        weight_rates: Optional[Dict[ShippingZone, Dict[str, float]]] = None,
        dimensional_weight_factor: Optional[float] = None,
        express_multiplier: Optional[float] = None,
        premium_multiplier: Optional[float] = None,
        free_shipping_threshold: Optional[float] = None
    ):
        """
        Initialize the shipping rate calculator.
        
        Args:
            zones_mapping: Mapping of origin and destination countries to shipping zones
            weight_rates: Rates for each shipping zone based on weight
            dimensional_weight_factor: Factor for calculating dimensional weight
            express_multiplier: Multiplier for express shipping rates
            premium_multiplier: Multiplier for premium shipping rates
            free_shipping_threshold: Minimum order total for free shipping
        """
        self.zones_mapping = zones_mapping or self.DEFAULT_ZONES
        self.weight_rates = weight_rates or self.DEFAULT_WEIGHT_RATES
        self.dimensional_weight_factor = dimensional_weight_factor or self.DEFAULT_DIM_WEIGHT_FACTOR
        self.express_multiplier = express_multiplier or self.DEFAULT_EXPRESS_MULTIPLIER
        self.premium_multiplier = premium_multiplier or self.DEFAULT_PREMIUM_MULTIPLIER
        self.free_shipping_threshold = free_shipping_threshold or 0.0
    
    def determine_shipping_zone(self, origin_country: str, destination_country: str) -> ShippingZone:
        """
        Determine the shipping zone for a given origin and destination.
        
        Args:
            origin_country: Country code of origin
            destination_country: Country code of destination
            
        Returns:
            The shipping zone
        """
        # Get country mapping or use DEFAULT
        country_mapping = self.zones_mapping.get(origin_country, self.zones_mapping.get("DEFAULT"))
        
        # Get zone for destination or use DEFAULT
        return country_mapping.get(destination_country, country_mapping.get("DEFAULT", ShippingZone.INTERNATIONAL_FAR))
    
    def calculate_dimensional_weight(self, dimensions: Dict[str, float]) -> float:
        """
        Calculate dimensional weight in kg based on package dimensions.
        
        Args:
            dimensions: Dictionary with width, height, length in cm
            
        Returns:
            Dimensional weight in kg
        """
        width = dimensions.get("width", 0)
        height = dimensions.get("height", 0)
        length = dimensions.get("length", 0)
        
        # Calculate volume in cubic meters
        volume_m3 = (width / 100) * (height / 100) * (length / 100)
        
        # Calculate dimensional weight
        return volume_m3 * self.dimensional_weight_factor
    
    def calculate_total_weight(self, items: List[Dict[str, Any]]) -> Tuple[float, float]:
        """
        Calculate both actual and dimensional weight for all items.
        
        Args:
            items: List of items with weights and dimensions
            
        Returns:
            Tuple of (actual weight, dimensional weight) in kg
        """
        actual_weight = 0.0
        dimensional_weight = 0.0
        
        for item in items:
            # Get quantity
            quantity = item.get("quantity", 1)
            
            # Add actual weight
            weight_kg = item.get("weight", 0)
            actual_weight += weight_kg * quantity
            
            # Add dimensional weight if dimensions are available
            dimensions = item.get("dimensions")
            if dimensions:
                item_dim_weight = self.calculate_dimensional_weight(dimensions)
                dimensional_weight += item_dim_weight * quantity
        
        return actual_weight, dimensional_weight
    
    def calculate_shipping_price(
        self,
        zone: ShippingZone,
        weight_kg: float,
        shipping_method: str = "standard"
    ) -> float:
        """
        Calculate shipping price based on zone and weight.
        
        Args:
            zone: The shipping zone
            weight_kg: The weight in kg
            shipping_method: The shipping method (standard, express, or premium)
            
        Returns:
            The shipping price
        """
        # Get rate information for the zone
        zone_rates = self.weight_rates.get(zone, self.weight_rates[ShippingZone.INTERNATIONAL_FAR])
        
        # Calculate base price
        base_rate = zone_rates["base_rate"]
        per_kg = zone_rates["per_kg"]
        min_weight = zone_rates["min_weight_kg"]
        
        # Ensure minimum weight
        weight_kg = max(weight_kg, min_weight)
        
        # Calculate price
        price = base_rate + (weight_kg * per_kg)
        
        # Apply method multiplier if needed
        if shipping_method == "express":
            price *= self.express_multiplier
        elif shipping_method == "premium":
            price *= self.premium_multiplier
        
        return round(price, 2)
    
    def calculate_rates(
        self,
        items: List[Dict[str, Any]],
        origin_country: str,
        destination_country: str,
        order_total: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Calculate shipping rates for a list of items.
        
        Args:
            items: List of items with weight and dimensions
            origin_country: Country code of origin
            destination_country: Country code of destination
            order_total: Total order amount for free shipping calculation
            
        Returns:
            List of shipping options with rates
        """
        # Determine shipping zone
        zone = self.determine_shipping_zone(origin_country, destination_country)
        
        # Calculate weights
        actual_weight, dimensional_weight = self.calculate_total_weight(items)
        
        # Use the higher of actual or dimensional weight
        billable_weight = max(actual_weight, dimensional_weight)
        
        # Calculate standard, express, and premium rates
        standard_rate = self.calculate_shipping_price(zone, billable_weight, shipping_method="standard")
        express_rate = self.calculate_shipping_price(zone, billable_weight, shipping_method="express")
        premium_rate = self.calculate_shipping_price(zone, billable_weight, shipping_method="premium")
        
        # Check for free shipping
        free_shipping = self.free_shipping_threshold > 0 and order_total >= self.free_shipping_threshold
        
        # Create shipping options
        rates = [
            {
                "id": "standard",
                "name": "Standard Shipping",
                "description": self._get_delivery_description(zone, shipping_method="standard"),
                "price": 0.0 if free_shipping else standard_rate,
                "estimated_days": self._get_delivery_days(zone, shipping_method="standard"),
                "free_shipping": free_shipping,
                "billable_weight": round(billable_weight, 2),
                "zone": zone.value
            },
            {
                "id": "express",
                "name": "Express Shipping",
                "description": self._get_delivery_description(zone, shipping_method="express"),
                "price": 0.0 if free_shipping else express_rate,
                "estimated_days": self._get_delivery_days(zone, shipping_method="express"),
                "free_shipping": free_shipping,
                "billable_weight": round(billable_weight, 2),
                "zone": zone.value
            },
            {
                "id": "premium",
                "name": "Premium Shipping",
                "description": self._get_delivery_description(zone, shipping_method="premium"),
                "price": 0.0 if free_shipping else premium_rate,
                "estimated_days": self._get_delivery_days(zone, shipping_method="premium"),
                "free_shipping": free_shipping,
                "billable_weight": round(billable_weight, 2),
                "zone": zone.value
            }
        ]
        
        return rates
    
    def _get_delivery_days(self, zone: ShippingZone, shipping_method: str = "standard") -> int:
        """
        Get estimated delivery days based on zone and shipping method.
        
        Args:
            zone: The shipping zone
            shipping_method: The shipping method (standard, express, or premium)
            
        Returns:
            Estimated delivery days
        """
        if shipping_method == "premium":
            # Premium shipping is fastest
            if zone == ShippingZone.DOMESTIC:
                return 1
            elif zone == ShippingZone.CONTINENTAL:
                return 2
            elif zone == ShippingZone.INTERNATIONAL_CLOSE:
                return 3
            else:  # INTERNATIONAL_FAR
                return 4
        elif shipping_method == "express":
            # Express shipping is faster than standard
            if zone == ShippingZone.DOMESTIC:
                return 2
            elif zone == ShippingZone.CONTINENTAL:
                return 3
            elif zone == ShippingZone.INTERNATIONAL_CLOSE:
                return 4
            else:  # INTERNATIONAL_FAR
                return 5
        else:
            # Standard shipping
            if zone == ShippingZone.DOMESTIC:
                return 5
            elif zone == ShippingZone.CONTINENTAL:
                return 7
            elif zone == ShippingZone.INTERNATIONAL_CLOSE:
                return 10
            else:  # INTERNATIONAL_FAR
                return 14
    
    def _get_delivery_description(self, zone: ShippingZone, shipping_method: str = "standard") -> str:
        """
        Get a human-readable description of delivery time.
        
        Args:
            zone: The shipping zone
            shipping_method: The shipping method (standard, express, or premium)
            
        Returns:
            Description string
        """
        days = self._get_delivery_days(zone, shipping_method)
        
        if days == 1:
            return "Next day delivery"
        elif days <= 2:
            return f"Delivery in {days} business days"
        else:
            return f"Delivery in {days-1}-{days} business days"


class PostalCodeCalculator:
    """Calculates distances and zones based on postal codes."""
    
    # Map of country codes to their distance calculation methods
    DISTANCE_CALCULATORS = {
        "US": "us_zip_distance",
        "CA": "ca_postal_distance",
        "GB": "uk_postal_distance",
        # Add more country-specific methods as needed
    }
    
    # US ZIP code first digit regions
    US_ZIP_REGIONS = {
        "0": "Northeast",
        "1": "Northeast",
        "2": "Southeast",
        "3": "Southeast",
        "4": "Midwest",
        "5": "Midwest",
        "6": "South-Central",
        "7": "South-Central",
        "8": "West",
        "9": "West"
    }
    
    # UK postal code region map (first 1-2 letters)
    UK_POSTAL_REGIONS = {
        "A": "Scotland",
        "B": "West Midlands",
        "C": "Wales",
        "D": "Wales",
        "E": "East",
        "F": "Scotland",
        "G": "Scotland",
        "H": "Scotland",
        "I": "Wales",
        "J": "Wales",
        "K": "Scotland",
        "L": "Northwest",
        "M": "Northwest",
        "N": "London",
        "O": "Wales",
        "P": "Wales",
        "Q": "Wales",
        "R": "Wales",
        "S": "Yorkshire",
        "T": "Southwest",
        "W": "London",
        # Add more regions as needed
    }
    
    # Canadian postal code region map (first letter)
    CA_POSTAL_REGIONS = {
        "A": "Newfoundland",
        "B": "Nova Scotia",
        "C": "Prince Edward Island",
        "E": "New Brunswick",
        "G": "Quebec East",
        "H": "Quebec West",
        "J": "Quebec Montreal",
        "K": "Ontario East",
        "L": "Ontario Central",
        "M": "Ontario Toronto",
        "N": "Ontario Southwest",
        "P": "Ontario Northwest",
        "R": "Manitoba",
        "S": "Saskatchewan",
        "T": "Alberta",
        "V": "British Columbia",
        "X": "Northwest Territories and Nunavut",
        "Y": "Yukon"
    }
    
    @classmethod
    def calculate_distance(cls, origin_country: str, origin_postal: str, dest_country: str, dest_postal: str) -> float:
        """
        Calculate approximate distance between two postal codes.
        
        Args:
            origin_country: Country code of origin
            origin_postal: Postal code of origin
            dest_country: Country code of destination
            dest_postal: Postal code of destination
            
        Returns:
            Approximate distance in km (or 0 if can't be calculated)
        """
        # If countries are different, we don't try to calculate postal code distance
        if origin_country != dest_country:
            return 0
        
        # Get the appropriate distance calculator method
        calculator_method = cls.DISTANCE_CALCULATORS.get(origin_country)
        
        if calculator_method and hasattr(cls, calculator_method):
            return getattr(cls, calculator_method)(origin_postal, dest_postal)
        
        return 0
    
    @classmethod
    def us_zip_distance(cls, origin_zip: str, dest_zip: str) -> float:
        """
        Calculate approximate distance between US ZIP codes.
        
        Args:
            origin_zip: Origin ZIP code
            dest_zip: Destination ZIP code
            
        Returns:
            Approximate distance in km
        """
        try:
            # Extract the regions based on first digit
            origin_region = cls.US_ZIP_REGIONS.get(origin_zip[0], "")
            dest_region = cls.US_ZIP_REGIONS.get(dest_zip[0], "")
            
            # If same region, consider it close
            if origin_region == dest_region:
                return 100
            
            # Calculate a very rough distance based on ZIP code
            # This is not accurate but gives a general idea
            origin_prefix = int(origin_zip[:3]) if origin_zip[:3].isdigit() else 0
            dest_prefix = int(dest_zip[:3]) if dest_zip[:3].isdigit() else 0
            
            # Normalize to a scale (very approximate)
            normalized_dist = abs(origin_prefix - dest_prefix) * 8
            
            # Ensure minimum distance
            return max(normalized_dist, 50)
            
        except (ValueError, IndexError):
            # If parsing fails, return a default
            return 500
    
    @classmethod
    def ca_postal_distance(cls, origin_postal: str, dest_postal: str) -> float:
        """
        Calculate approximate distance between Canadian postal codes.
        
        Args:
            origin_postal: Origin postal code
            dest_postal: Destination postal code
            
        Returns:
            Approximate distance in km
        """
        try:
            # Extract the regions based on first letter
            origin_region = cls.CA_POSTAL_REGIONS.get(origin_postal[0].upper(), "")
            dest_region = cls.CA_POSTAL_REGIONS.get(dest_postal[0].upper(), "")
            
            # If same region, consider it close
            if origin_region == dest_region:
                return 100
            
            # Very rough approximation
            return 500
            
        except (IndexError):
            # If parsing fails, return a default
            return 500
    
    @classmethod
    def uk_postal_distance(cls, origin_postal: str, dest_postal: str) -> float:
        """
        Calculate approximate distance between UK postal codes.
        
        Args:
            origin_postal: Origin postal code
            dest_postal: Destination postal code
            
        Returns:
            Approximate distance in km
        """
        try:
            # Extract the regions based on first letter(s)
            origin_region = cls.UK_POSTAL_REGIONS.get(origin_postal[0].upper(), "")
            dest_region = cls.UK_POSTAL_REGIONS.get(dest_postal[0].upper(), "")
            
            # If same region, consider it close
            if origin_region == dest_region:
                return 50
            
            # Very rough approximation
            return 300
            
        except (IndexError):
            # If parsing fails, return a default
            return 300