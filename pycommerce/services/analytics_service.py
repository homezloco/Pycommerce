"""
Analytics service for PyCommerce.

This module provides analytics functionality for orders, products, and customers.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

from sqlalchemy import func, desc, and_, or_, between, extract

from pycommerce.core.db import get_session
from pycommerce.models.order import Order, OrderStatus
from pycommerce.models.order_item import OrderItem
from pycommerce.models.product import Product

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for calculating analytics data."""
    
    def get_order_analytics(
        self, 
        tenant_id: str, 
        start_date: datetime, 
        end_date: datetime,
        previous_period: bool = True
    ) -> Dict[str, Any]:
        """
        Get order analytics for a specific period.
        
        Args:
            tenant_id: The tenant ID
            start_date: Start date for the period
            end_date: End date for the period
            previous_period: Whether to include comparison with previous period
            
        Returns:
            Dictionary with analytics data
        """
        try:
            # Calculate period length in days
            period_length = (end_date - start_date).days + 1
            
            # Get current period metrics
            current_metrics = self._get_period_metrics(tenant_id, start_date, end_date)
            
            # Calculate order count, revenue, and average order value
            order_count = current_metrics.get("order_count", 0)
            revenue = current_metrics.get("revenue", 0.0)
            avg_order_value = revenue / order_count if order_count > 0 else 0
            
            # Get top products by revenue
            top_products = self._get_top_products(tenant_id, start_date, end_date)
            
            # Get orders by day
            orders_by_day = self._get_orders_by_day(tenant_id, start_date, end_date)
            
            # Calculate metrics for comparison with previous period if requested
            comparison = {}
            if previous_period:
                # Define previous period date range
                prev_start_date = start_date - timedelta(days=period_length)
                prev_end_date = end_date - timedelta(days=period_length)
                
                # Get previous period metrics
                prev_metrics = self._get_period_metrics(tenant_id, prev_start_date, prev_end_date)
                
                # Calculate comparison percentages
                prev_order_count = prev_metrics.get("order_count", 0)
                prev_revenue = prev_metrics.get("revenue", 0.0)
                prev_avg_order_value = prev_revenue / prev_order_count if prev_order_count > 0 else 0
                
                # Calculate percentage changes
                comparison = {
                    "orders": self._calculate_percentage_change(prev_order_count, order_count),
                    "revenue": self._calculate_percentage_change(prev_revenue, revenue),
                    "avg_order_value": self._calculate_percentage_change(prev_avg_order_value, avg_order_value),
                    # For now, set conversion rate to 0 as we don't track site visits
                    "conversion_rate": 0
                }
            
            # Calculate estimated conversion rate (mocked for now)
            # In a real app, this would use actual visit data from analytics
            conversion_rate = 3.25  # Placeholder value
            
            # Construct the response
            return {
                "summary": {
                    "orders": order_count,
                    "revenue": round(revenue, 2),
                    "avg_order_value": round(avg_order_value, 2),
                    "conversion_rate": conversion_rate
                },
                "comparison": comparison,
                "orders_by_day": orders_by_day,
                "top_products": top_products,
                # These values are placeholders and would need proper tracking in a real app
                "traffic_sources": {
                    "direct": 35,
                    "organic": 25,
                    "referral": 15,
                    "social": 20,
                    "email": 5,
                },
                "device_types": {
                    "desktop": 45,
                    "mobile": 40,
                    "tablet": 15,
                },
                "customer_locations": {
                    "United States": 65,
                    "Canada": 15,
                    "United Kingdom": 10,
                    "Australia": 5,
                    "Other": 5,
                }
            }
        except Exception as e:
            logger.error(f"Error getting order analytics: {str(e)}")
            return {
                "summary": {
                    "orders": 0,
                    "revenue": 0.0,
                    "avg_order_value": 0.0,
                    "conversion_rate": 0.0
                },
                "comparison": {},
                "orders_by_day": [],
                "top_products": []
            }
    
    def _get_period_metrics(
        self, 
        tenant_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get basic metrics for a specific period.
        
        Args:
            tenant_id: The tenant ID
            start_date: Start date for the period
            end_date: End date for the period
            
        Returns:
            Dictionary with order count and revenue
        """
        try:
            with get_session() as session:
                # Count orders and sum revenue
                query = session.query(
                    func.count(Order.id).label("order_count"),
                    func.sum(Order.total).label("revenue")
                ).filter(
                    Order.tenant_id == tenant_id,
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                )
                
                result = query.first()
                
                return {
                    "order_count": result.order_count if result.order_count else 0,
                    "revenue": result.revenue if result.revenue else 0.0
                }
        except Exception as e:
            logger.error(f"Error getting period metrics: {str(e)}")
            return {"order_count": 0, "revenue": 0.0}
    
    def _get_top_products(
        self, 
        tenant_id: str, 
        start_date: datetime, 
        end_date: datetime,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get top products by revenue for a specific period.
        
        Args:
            tenant_id: The tenant ID
            start_date: Start date for the period
            end_date: End date for the period
            limit: Maximum number of products to return
            
        Returns:
            List of top products with their orders and revenue
        """
        try:
            with get_session() as session:
                # Query to get top products by revenue
                query = session.query(
                    OrderItem.product_id,
                    OrderItem.product_name,
                    func.sum(OrderItem.quantity).label("order_count"),
                    func.sum(OrderItem.price * OrderItem.quantity).label("revenue")
                ).join(
                    Order, OrderItem.order_id == Order.id
                ).filter(
                    Order.tenant_id == tenant_id,
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                ).group_by(
                    OrderItem.product_id,
                    OrderItem.product_name
                ).order_by(
                    desc("revenue")
                ).limit(limit)
                
                results = query.all()
                
                return [
                    {
                        "name": result.product_name,
                        "orders": int(result.order_count),
                        "revenue": round(float(result.revenue), 2)
                    }
                    for result in results
                ]
        except Exception as e:
            logger.error(f"Error getting top products: {str(e)}")
            return []
    
    def _get_orders_by_day(
        self, 
        tenant_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get orders grouped by day for a specific period.
        
        Args:
            tenant_id: The tenant ID
            start_date: Start date for the period
            end_date: End date for the period
            
        Returns:
            List of daily order counts and revenue
        """
        try:
            with get_session() as session:
                # Query to get orders by day
                query = session.query(
                    func.date(Order.created_at).label("date"),
                    func.count(Order.id).label("orders"),
                    func.sum(Order.total).label("revenue")
                ).filter(
                    Order.tenant_id == tenant_id,
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                ).group_by(
                    func.date(Order.created_at)
                ).order_by(
                    "date"
                )
                
                results = query.all()
                
                return [
                    {
                        "date": result.date.isoformat(),
                        "orders": int(result.orders),
                        "revenue": round(float(result.revenue), 2)
                    }
                    for result in results
                ]
        except Exception as e:
            logger.error(f"Error getting orders by day: {str(e)}")
            return []
    
    def _calculate_percentage_change(self, old_value: float, new_value: float) -> float:
        """
        Calculate percentage change between two values.
        
        Args:
            old_value: Previous value
            new_value: Current value
            
        Returns:
            Percentage change (rounded to 1 decimal place)
        """
        if old_value == 0:
            return 100.0 if new_value > 0 else 0.0
        
        change = ((new_value - old_value) / old_value) * 100
        return round(change, 1)