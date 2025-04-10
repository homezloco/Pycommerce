"""
Market analysis service for PyCommerce.

This module provides functionality for analyzing market trends,
forecasting demand, and providing business intelligence insights.
"""
import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple
import json
from collections import defaultdict

from pycommerce.models.product import ProductManager
from pycommerce.models.order import OrderManager
from pycommerce.models.tenant import TenantManager
from pycommerce.utils.date_utils import get_date_range, format_date

# AI config may not be available in all environments
try:
    from pycommerce.plugins.ai.config import AIConfigManager
    ai_config_available = True
except ImportError:
    ai_config_available = False
    logging.warning("AI configuration module not available")

logger = logging.getLogger(__name__)

class MarketAnalysisService:
    """
    Service for market trend analysis and demand forecasting.
    
    This service analyzes historical sales data, product popularity,
    and market trends to provide insights and forecasts.
    """
    
    def __init__(self):
        """Initialize the market analysis service."""
        self.product_manager = ProductManager()
        self.order_manager = OrderManager()
        self.tenant_manager = TenantManager()
        
        # Initialize AI config manager if available
        if ai_config_available:
            try:
                self.ai_config_manager = AIConfigManager()
            except Exception as e:
                logger.warning(f"Failed to initialize AI config manager: {str(e)}")
                self.ai_config_manager = None
        else:
            self.ai_config_manager = None
        
        logger.info("Market analysis service initialized")
    
    def get_sales_trends(
        self, 
        tenant_id: Optional[str] = None, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get sales trends for a specific time period.
        
        Args:
            tenant_id: Optional ID of the tenant to filter sales for
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            category: Optional product category to filter by
            
        Returns:
            Dictionary containing sales trend data
        """
        try:
            # Default to last 30 days if no dates provided
            if not start_date:
                end_datetime = datetime.datetime.now()
                start_datetime = end_datetime - datetime.timedelta(days=30)
                start_date = start_datetime.strftime("%Y-%m-%d")
                end_date = end_datetime.strftime("%Y-%m-%d")
            
            # Get orders for the specified time period
            orders = self.order_manager.get_orders(
                tenant_id=tenant_id,
                date_from=start_date,
                date_to=end_date
            )
            
            if not orders:
                logger.warning(f"No orders found for the specified period: {start_date} to {end_date}")
                return {
                    "status": "success",
                    "message": "No sales data available for the selected period",
                    "data": {
                        "trends": [],
                        "total_revenue": 0,
                        "total_orders": 0,
                        "avg_order_value": 0
                    }
                }
            
            # Process orders into sales data
            daily_sales = defaultdict(float)
            category_sales = defaultdict(float)
            product_sales = defaultdict(int)
            total_revenue = 0
            
            for order in orders:
                order_date = order.created_at.strftime("%Y-%m-%d")
                daily_sales[order_date] += order.total
                total_revenue += order.total
                
                # Process items in the order
                for item in order.items:
                    product_id = str(item.product_id)
                    product = self.product_manager.get(product_id)
                    
                    if product and hasattr(product, 'categories'):
                        # Skip if category filter is applied and product doesn't match
                        if category and category not in product.categories:
                            continue
                            
                        # Update category sales
                        for cat in product.categories:
                            category_sales[cat] += item.price * item.quantity
                    
                    # Update product sales counts
                    product_sales[product_id] += item.quantity
            
            # Format data for trends
            date_range = get_date_range(start_date, end_date)
            trends = []
            
            for date_str in date_range:
                trends.append({
                    "date": date_str,
                    "revenue": round(daily_sales.get(date_str, 0), 2)
                })
            
            # Get top categories by sales
            top_categories = sorted(
                [{"category": cat, "revenue": round(revenue, 2)} 
                 for cat, revenue in category_sales.items()],
                key=lambda x: x["revenue"],
                reverse=True
            )[:5]  # Top 5 categories
            
            # Get top products by quantity sold
            top_products_data = []
            for product_id, quantity in sorted(
                product_sales.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]:  # Top 10 products
                product = self.product_manager.get(product_id)
                if product:
                    top_products_data.append({
                        "id": product_id,
                        "name": product.name,
                        "quantity": quantity,
                        "revenue": round(quantity * product.price, 2)
                    })
            
            return {
                "status": "success",
                "data": {
                    "trends": trends,
                    "total_revenue": round(total_revenue, 2),
                    "total_orders": len(orders),
                    "avg_order_value": round(total_revenue / len(orders), 2) if orders else 0,
                    "top_categories": top_categories,
                    "top_products": top_products_data
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting sales trends: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to retrieve sales trends: {str(e)}"
            }
    
    def forecast_demand(
        self,
        product_id: str,
        forecast_days: int = 30,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Forecast demand for a specific product.
        
        Args:
            product_id: ID of the product to forecast demand for
            forecast_days: Number of days to forecast (default 30)
            tenant_id: Optional ID of the tenant that owns the product
            
        Returns:
            Dictionary containing forecast data
        """
        try:
            # Get the product details
            product = self.product_manager.get(product_id)
            if not product:
                logger.error(f"Product not found: {product_id}")
                return {
                    "status": "error",
                    "message": f"Product not found: {product_id}"
                }
            
            # Get historical sales data for the past 90 days
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=90)
            
            orders = self.order_manager.get_orders(
                tenant_id=tenant_id,
                date_from=start_date.strftime("%Y-%m-%d"),
                date_to=end_date.strftime("%Y-%m-%d")
            )
            
            # Process historical sales data
            daily_sales = defaultdict(int)
            for order in orders:
                for item in order.items:
                    if str(item.product_id) == product_id:
                        order_date = order.created_at.strftime("%Y-%m-%d")
                        daily_sales[order_date] += item.quantity
            
            # Calculate basic forecast using moving average
            # This is a simple approach; a real implementation would use more
            # sophisticated time series forecasting methods
            sales_values = list(daily_sales.values())
            
            if not sales_values:
                logger.warning(f"No historical sales data for product: {product_id}")
                return {
                    "status": "success",
                    "message": "No historical data available for accurate forecasting",
                    "data": {
                        "product_id": product_id,
                        "product_name": product.name,
                        "current_stock": product.stock,
                        "forecast_days": forecast_days,
                        "daily_forecast": 0,
                        "total_forecast": 0,
                        "stock_status": "Unknown" if product.stock is None else "Sufficient"
                    }
                }
            
            # Calculate average daily sales (simple moving average)
            avg_daily_sales = sum(sales_values) / len(sales_values) if sales_values else 0
            
            # Forecast total demand for the forecast period
            total_forecast = round(avg_daily_sales * forecast_days)
            
            # Determine stock status
            stock_status = "Sufficient"
            if product.stock is not None:
                if product.stock <= 0:
                    stock_status = "Out of Stock"
                elif product.stock < total_forecast:
                    stock_status = "Insufficient"
            
            # Generate forecast data
            forecast_data = {
                "product_id": product_id,
                "product_name": product.name,
                "current_stock": product.stock,
                "forecast_days": forecast_days,
                "daily_forecast": round(avg_daily_sales, 2),
                "total_forecast": total_forecast,
                "stock_status": stock_status,
                "restock_recommendation": max(0, total_forecast - (product.stock or 0))
            }
            
            return {
                "status": "success",
                "data": forecast_data
            }
        
        except Exception as e:
            logger.error(f"Error forecasting demand: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to forecast demand: {str(e)}"
            }
    
    def get_market_insights(
        self,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get market insights using available data and AI integration.
        
        Args:
            tenant_id: Optional ID of the tenant to get insights for
            
        Returns:
            Dictionary containing market insights
        """
        try:
            # Get active AI provider configuration
            ai_provider = None
            if self.ai_config_manager:
                try:
                    ai_config = self.ai_config_manager.get_active_provider(tenant_id)
                    if ai_config:
                        ai_provider = ai_config.get("provider_id")
                except Exception as e:
                    logger.error(f"Error getting AI provider: {str(e)}")
            else:
                logger.debug("AI configuration manager not available")
            
            # Get sales trends for the past 90 days
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=90)
            
            sales_trends = self.get_sales_trends(
                tenant_id=tenant_id,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )
            
            # If we don't have valid sales data, return a basic response
            if sales_trends.get("status") != "success" or not sales_trends.get("data", {}).get("trends"):
                return {
                    "status": "warning",
                    "message": "Insufficient data for market insights",
                    "data": {
                        "insights": [
                            "Not enough historical data available for analysis",
                            "Continue operating your store to generate more sales data"
                        ],
                        "trend_direction": "neutral",
                        "recommendations": []
                    }
                }
            
            # Get all products for the tenant
            products = self.product_manager.get_products(tenant_id=tenant_id)
            
            # Calculate basic insights
            insights = []
            recommendations = []
            
            # Analyze sales trend direction
            trend_data = sales_trends["data"]["trends"]
            first_half = sum(item["revenue"] for item in trend_data[:len(trend_data)//2])
            second_half = sum(item["revenue"] for item in trend_data[len(trend_data)//2:])
            
            trend_direction = "neutral"
            if second_half > first_half * 1.1:  # 10% increase
                trend_direction = "up"
                insights.append("Sales are trending upward over the past 90 days")
            elif second_half < first_half * 0.9:  # 10% decrease
                trend_direction = "down"
                insights.append("Sales are trending downward over the past 90 days")
            else:
                insights.append("Sales have remained relatively stable over the past 90 days")
            
            # Add insights based on top categories
            if "top_categories" in sales_trends["data"] and sales_trends["data"]["top_categories"]:
                top_category = sales_trends["data"]["top_categories"][0]["category"]
                insights.append(f"'{top_category}' is your best-performing category")
                recommendations.append(f"Consider expanding your '{top_category}' product line")
            
            # Add insights based on top products
            if "top_products" in sales_trends["data"] and sales_trends["data"]["top_products"]:
                top_product = sales_trends["data"]["top_products"][0]["name"]
                insights.append(f"'{top_product}' is your best-selling product")
                recommendations.append(f"Ensure '{top_product}' remains well-stocked")
            
            # Check inventory status
            low_stock_products = []
            for product in products:
                if product.stock is not None and product.stock <= 5:  # Arbitrary low stock threshold
                    low_stock_products.append(product.name)
            
            if low_stock_products:
                product_names = ", ".join(low_stock_products[:3])
                if len(low_stock_products) > 3:
                    product_names += f", and {len(low_stock_products) - 3} more"
                    
                insights.append(f"Low stock alerts for: {product_names}")
                recommendations.append("Restock your low inventory products soon")
            
            # Add seasonal insights
            current_month = datetime.datetime.now().month
            if 3 <= current_month <= 5:  # Spring
                insights.append("Spring shopping season is in progress")
                recommendations.append("Consider spring-themed promotions and seasonal products")
            elif 6 <= current_month <= 8:  # Summer
                insights.append("Summer shopping season is in progress")
                recommendations.append("Promote summer products and vacation-related items")
            elif 9 <= current_month <= 11:  # Fall
                insights.append("Fall shopping season is in progress")
                recommendations.append("Prepare for the upcoming holiday shopping season")
            else:  # Winter/Holiday
                insights.append("Holiday shopping season is in progress")
                recommendations.append("Focus on gift items and holiday promotions")
            
            return {
                "status": "success",
                "data": {
                    "insights": insights,
                    "trend_direction": trend_direction,
                    "recommendations": recommendations,
                    "ai_enhanced": ai_provider is not None
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting market insights: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to get market insights: {str(e)}"
            }
    
    def get_category_performance(
        self,
        tenant_id: Optional[str] = None,
        period: str = "month"  # "week", "month", "quarter", "year"
    ) -> Dict[str, Any]:
        """
        Get performance metrics for product categories.
        
        Args:
            tenant_id: Optional ID of the tenant to get insights for
            period: Time period for analysis (week, month, quarter, year)
            
        Returns:
            Dictionary containing category performance data
        """
        try:
            # Determine date range based on period
            end_date = datetime.datetime.now()
            
            if period == "week":
                start_date = end_date - datetime.timedelta(days=7)
            elif period == "month":
                start_date = end_date - datetime.timedelta(days=30)
            elif period == "quarter":
                start_date = end_date - datetime.timedelta(days=90)
            elif period == "year":
                start_date = end_date - datetime.timedelta(days=365)
            else:
                # Default to month
                start_date = end_date - datetime.timedelta(days=30)
            
            # Get orders for the period
            orders = self.order_manager.get_orders(
                tenant_id=tenant_id,
                date_from=start_date.strftime("%Y-%m-%d"),
                date_to=end_date.strftime("%Y-%m-%d")
            )
            
            if not orders:
                logger.warning(f"No orders found for the period: {period}")
                return {
                    "status": "success",
                    "message": "No sales data available for the selected period",
                    "data": {
                        "categories": [],
                        "period": period
                    }
                }
            
            # Process category data
            category_metrics = defaultdict(lambda: {
                "revenue": 0,
                "orders": 0,
                "units_sold": 0,
                "avg_price": 0
            })
            
            for order in orders:
                for item in order.items:
                    product_id = str(item.product_id)
                    product = self.product_manager.get(product_id)
                    
                    if product and hasattr(product, 'categories'):
                        for category in product.categories:
                            category_metrics[category]["revenue"] += item.price * item.quantity
                            category_metrics[category]["orders"] += 1
                            category_metrics[category]["units_sold"] += item.quantity
            
            # Calculate average price
            for category, metrics in category_metrics.items():
                if metrics["units_sold"] > 0:
                    metrics["avg_price"] = round(metrics["revenue"] / metrics["units_sold"], 2)
            
            # Format category data for response
            categories_data = []
            for category, metrics in category_metrics.items():
                categories_data.append({
                    "category": category,
                    "revenue": round(metrics["revenue"], 2),
                    "orders": metrics["orders"],
                    "units_sold": metrics["units_sold"],
                    "avg_price": metrics["avg_price"]
                })
            
            # Sort by revenue (highest first)
            categories_data.sort(key=lambda x: x["revenue"], reverse=True)
            
            return {
                "status": "success",
                "data": {
                    "categories": categories_data,
                    "period": period
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting category performance: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to get category performance: {str(e)}"
            }