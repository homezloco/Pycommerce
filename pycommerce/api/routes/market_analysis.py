"""
Market analysis API routes for PyCommerce.

This module provides API endpoints for market trend analysis,
demand forecasting, and business intelligence.
"""
import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Query, Path, Depends
from pydantic import BaseModel

from pycommerce.services.market_analysis import MarketAnalysisService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market-analysis", tags=["market-analysis"])

# Pydantic models for API responses
class SalesTrendItem(BaseModel):
    date: str
    revenue: float

    class Config:
        from_attributes = True

class CategorySales(BaseModel):
    category: str
    revenue: float

    class Config:
        from_attributes = True

class ProductSales(BaseModel):
    id: str
    name: str
    quantity: int
    revenue: float

    class Config:
        from_attributes = True

class SalesTrendsResponse(BaseModel):
    trends: List[SalesTrendItem]
    total_revenue: float
    total_orders: int
    avg_order_value: float
    top_categories: List[CategorySales] = []
    top_products: List[ProductSales] = []

    class Config:
        from_attributes = True

class ForecastData(BaseModel):
    product_id: str
    product_name: str
    current_stock: Optional[int]
    forecast_days: int
    daily_forecast: float
    total_forecast: int
    stock_status: str
    restock_recommendation: int

    class Config:
        from_attributes = True

class InsightsResponse(BaseModel):
    insights: List[str]
    trend_direction: str
    recommendations: List[str]
    ai_enhanced: bool

    class Config:
        from_attributes = True

class CategoryPerformance(BaseModel):
    category: str
    revenue: float
    orders: int
    units_sold: int
    avg_price: float

    class Config:
        from_attributes = True

class CategoryPerformanceResponse(BaseModel):
    categories: List[CategoryPerformance]
    period: str

    class Config:
        from_attributes = True

class ApiResponse(BaseModel):
    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# Create the MarketAnalysisService
market_analysis_service = MarketAnalysisService()

@router.get("/sales-trends", response_model=ApiResponse)
async def get_sales_trends(
    tenant_id: Optional[str] = Query(None, description="Tenant ID to filter sales"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Category to filter by")
):
    """
    Get sales trends for a specific time period.

    Args:
        tenant_id: Optional tenant ID to filter sales
        start_date: Start date in ISO format (YYYY-MM-DD)
        end_date: End date in ISO format (YYYY-MM-DD)
        category: Optional product category to filter by

    Returns:
        Sales trend data
    """
    logger.info(f"Getting sales trends for tenant: {tenant_id}, dates: {start_date} to {end_date}")

    result = market_analysis_service.get_sales_trends(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
        category=category
    )

    return result

@router.get("/demand-forecast/{product_id}", response_model=ApiResponse)
async def forecast_demand(
    product_id: str = Path(..., description="ID of the product to forecast demand for"),
    forecast_days: int = Query(30, description="Number of days to forecast"),
    tenant_id: Optional[str] = Query(None, description="Tenant ID that owns the product")
):
    """
    Forecast demand for a specific product.

    Args:
        product_id: ID of the product to forecast demand for
        forecast_days: Number of days to forecast (default 30)
        tenant_id: Optional tenant ID that owns the product

    Returns:
        Demand forecast data
    """
    logger.info(f"Forecasting demand for product: {product_id}, days: {forecast_days}")

    result = market_analysis_service.forecast_demand(
        product_id=product_id,
        forecast_days=forecast_days,
        tenant_id=tenant_id
    )

    return result

@router.get("/insights", response_model=ApiResponse)
async def get_market_insights(
    tenant_id: Optional[str] = Query(None, description="Tenant ID to get insights for")
):
    """
    Get market insights using available data and AI integration.

    Args:
        tenant_id: Optional tenant ID to get insights for

    Returns:
        Market insights data
    """
    logger.info(f"Getting market insights for tenant: {tenant_id}")

    result = market_analysis_service.get_market_insights(tenant_id=tenant_id)

    return result

@router.get("/category-performance", response_model=ApiResponse)
async def get_category_performance(
    tenant_id: Optional[str] = Query(None, description="Tenant ID to get insights for"),
    period: str = Query("month", description="Time period (week, month, quarter, year)")
):
    """
    Get performance metrics for product categories.

    Args:
        tenant_id: Optional tenant ID to get insights for
        period: Time period for analysis (week, month, quarter, year)

    Returns:
        Category performance data
    """
    logger.info(f"Getting category performance for tenant: {tenant_id}, period: {period}")

    result = market_analysis_service.get_category_performance(
        tenant_id=tenant_id,
        period=period
    )

    return result