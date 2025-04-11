"""
Market analysis routes for the admin dashboard.

This module provides routes for displaying market trend analysis,
demand forecasting, and business intelligence information.
"""
import logging
import json
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from pycommerce.models.tenant import TenantManager
from pycommerce.models.product import ProductManager
from pycommerce.models.order import OrderManager
from pycommerce.services.market_analysis import MarketAnalysisService
from routes.admin.tenant_utils import get_current_tenant

logger = logging.getLogger(__name__)

def setup_routes(templates):
    """
    Set up routes for market analysis.
    
    Args:
        templates: Jinja2 templates instance
        
    Returns:
        APIRouter: FastAPI router
    """
    router = APIRouter(prefix="/admin/market-analysis", tags=["admin-market-analysis"])
    tenant_manager = TenantManager()
    market_analysis_service = MarketAnalysisService()
    
    @router.get("", response_class=HTMLResponse)
    async def market_analysis_dashboard(request: Request):
        """Market Analysis Dashboard."""
        # Use the tenant utils function to get current tenant
        tenant_obj, tenant_id, tenant_slug = get_current_tenant(request, tenant_manager)
        
        # Get all tenants for the store selector
        tenants = []
        try:
            tenants_list = tenant_manager.list() or []
            tenants = [
                {
                    "id": str(t.id),
                    "name": t.name,
                    "slug": t.slug,
                    "domain": t.domain if hasattr(t, 'domain') else None,
                    "active": t.active if hasattr(t, 'active') else True
                }
                for t in tenants_list if t and hasattr(t, 'id')
            ]
        except Exception as e:
            logger.error(f"Error fetching tenants: {str(e)}")
        
        # Log the tenant ID being used
        logger.info(f"Using tenant_id: {tenant_id} for market analysis dashboard (slug: {tenant_slug})")
        
        # Get the default time period data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Handle all stores selection
        if tenant_slug.lower() == "all":
            logger.info("Using 'All Stores' selection for market analysis dashboard")
            
            # Get all tenants
            all_tenants = tenant_manager.list() or []
            
            # Initialize combined data structures
            combined_sales_trends = {"data": {
                "daily_sales": [],
                "weekly_sales": [],
                "monthly_sales": [],
                "top_selling_products": [],
                "sales_by_category": {}
            }}
            
            combined_insights = {"data": {
                "trending_products": [],
                "seasonal_trends": [],
                "competitive_analysis": {},
                "price_sensitivity": {},
                "customer_segments": {}
            }}
            
            combined_category_performance = {"data": {
                "categories": [],
                "performance_metrics": {},
                "growth_rates": {},
                "conversion_rates": {}
            }}
            
            # Collect data from all tenants
            for tenant in all_tenants:
                try:
                    # Get sales trends for this tenant
                    tenant_sales = market_analysis_service.get_sales_trends(
                        tenant_id=str(tenant.id),
                        start_date=start_date.strftime("%Y-%m-%d"),
                        end_date=end_date.strftime("%Y-%m-%d")
                    )
                    
                    if "data" in tenant_sales:
                        # Combine top selling products
                        if "top_selling_products" in tenant_sales["data"]:
                            combined_sales_trends["data"]["top_selling_products"].extend(
                                tenant_sales["data"]["top_selling_products"]
                            )
                        
                        # Combine sales by category
                        if "sales_by_category" in tenant_sales["data"]:
                            for category, value in tenant_sales["data"]["sales_by_category"].items():
                                if category in combined_sales_trends["data"]["sales_by_category"]:
                                    combined_sales_trends["data"]["sales_by_category"][category] += value
                                else:
                                    combined_sales_trends["data"]["sales_by_category"][category] = value
                    
                    # Get market insights for this tenant
                    tenant_insights = market_analysis_service.get_market_insights(
                        tenant_id=str(tenant.id)
                    )
                    
                    if "data" in tenant_insights:
                        # Combine trending products
                        if "trending_products" in tenant_insights["data"]:
                            combined_insights["data"]["trending_products"].extend(
                                tenant_insights["data"]["trending_products"]
                            )
                    
                    # Get category performance for this tenant
                    tenant_category = market_analysis_service.get_category_performance(
                        tenant_id=str(tenant.id),
                        period="month"
                    )
                    
                    if "data" in tenant_category:
                        # Combine categories
                        if "categories" in tenant_category["data"]:
                            for category in tenant_category["data"]["categories"]:
                                if category not in combined_category_performance["data"]["categories"]:
                                    combined_category_performance["data"]["categories"].append(category)
                        
                        # Combine performance metrics
                        if "performance_metrics" in tenant_category["data"]:
                            for category, metrics in tenant_category["data"]["performance_metrics"].items():
                                if category in combined_category_performance["data"]["performance_metrics"]:
                                    # Average the metrics
                                    for metric, value in metrics.items():
                                        combined_category_performance["data"]["performance_metrics"][category][metric] += value
                                else:
                                    combined_category_performance["data"]["performance_metrics"][category] = metrics.copy()
                    
                    logger.info(f"Added market data for tenant {tenant.name}")
                except Exception as e:
                    logger.error(f"Error getting market data for tenant {tenant.id}: {str(e)}")
            
            # Sort combined top selling products by sales
            combined_sales_trends["data"]["top_selling_products"] = sorted(
                combined_sales_trends["data"]["top_selling_products"],
                key=lambda x: x.get("sales", 0),
                reverse=True
            )[:10]  # Limit to top 10
            
            # Sort combined trending products by trend score
            combined_insights["data"]["trending_products"] = sorted(
                combined_insights["data"]["trending_products"],
                key=lambda x: x.get("trend_score", 0),
                reverse=True
            )[:10]  # Limit to top 10
            
            # Use the combined data
            sales_trends = combined_sales_trends
            insights = combined_insights
            category_performance = combined_category_performance
            
            logger.info(f"Combined market analysis data for all stores")
        else:
            # Get sales trend data for a single tenant
            sales_trends = market_analysis_service.get_sales_trends(
                tenant_id=tenant_id,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )
            
            # Get market insights
            insights = market_analysis_service.get_market_insights(tenant_id=tenant_id)
            
            # Get category performance for the month
            category_performance = market_analysis_service.get_category_performance(
                tenant_id=tenant_id,
                period="month"
            )
        
        # Determine selected tenant for the UI
        selected_tenant = None
        if tenant_slug == "all":
            # Create a special entry for the "All Stores" option
            selected_tenant = {
                "id": "",
                "name": "All Stores",
                "slug": "all",
                "domain": None,
                "active": True
            }
            logger.info("Using 'All Stores' view for market analysis dashboard")
        else:
            for tenant in tenants:
                if tenant.get("id") == tenant_id:
                    selected_tenant = tenant
                    break
        
        # Template context
        context = {
            "request": request,
            "active_page": "market_analysis",
            "page_title": "Market Analysis",
            "selected_tenant": selected_tenant,
            "tenants": tenants,
            "cart_item_count": request.session.get("cart_item_count", 0),
            "sales_trends": sales_trends.get("data", {}),
            "market_insights": insights.get("data", {}),
            "category_performance": category_performance.get("data", {}),
            # Serialize the data for JavaScript
            "sales_trends_json": json.dumps(sales_trends.get("data", {})),
            "market_insights_json": json.dumps(insights.get("data", {})),
            "category_performance_json": json.dumps(category_performance.get("data", {})),
        }
        
        return templates.TemplateResponse("admin/market_analysis.html", context)
    
    @router.get("/sales-trends", response_class=HTMLResponse)
    async def sales_trends(
        request: Request,
        start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
        end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
        category: Optional[str] = Query(None, description="Filter by category")
    ):
        """Sales trends view."""
        # Use the tenant utils function to get current tenant
        tenant_obj, tenant_id, tenant_slug = get_current_tenant(request, tenant_manager)
        
        # Log the tenant ID being used
        logger.info(f"Using tenant_id: {tenant_id} for sales trends (slug: {tenant_slug})")
        
        # If no dates provided, default to last 30 days
        if not start_date or not end_date:
            end_datetime = datetime.now()
            start_datetime = end_datetime - timedelta(days=30)
            start_date = start_datetime.strftime("%Y-%m-%d") 
            end_date = end_datetime.strftime("%Y-%m-%d")
        
        # Get sales trend data
        sales_trends = market_analysis_service.get_sales_trends(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            category=category
        )
        
        # Get all tenants for the store selector
        tenants = []
        try:
            tenants_list = tenant_manager.list() or []
            tenants = [
                {
                    "id": str(t.id),
                    "name": t.name,
                    "slug": t.slug,
                    "domain": t.domain if hasattr(t, 'domain') else None,
                    "active": t.active if hasattr(t, 'active') else True
                }
                for t in tenants_list if t and hasattr(t, 'id')
            ]
        except Exception as e:
            logger.error(f"Error fetching tenants: {str(e)}")
        
        # Determine selected tenant for the UI
        selected_tenant = None
        if tenant_slug == "all":
            # Create a special entry for the "All Stores" option
            selected_tenant = {
                "id": "",
                "name": "All Stores",
                "slug": "all",
                "domain": None,
                "active": True
            }
            logger.info("Using 'All Stores' view for sales trends")
        else:
            for tenant in tenants:
                if tenant.get("id") == tenant_id:
                    selected_tenant = tenant
                    break
        
        # Get product manager for categories
        product_manager = ProductManager()
        categories = []
        
        if tenant_id:
            try:
                # Get unique categories from products
                products = product_manager.list(tenant_id=tenant_id)
                unique_categories = set()
                for product in products:
                    if hasattr(product, 'categories'):
                        for cat in product.categories:
                            unique_categories.add(cat)
                categories = sorted(list(unique_categories))
            except Exception as e:
                logger.error(f"Error getting categories: {str(e)}")
        
        # Template context
        context = {
            "request": request,
            "active_page": "market_analysis",
            "active_tab": "sales_trends",
            "page_title": "Sales Trends",
            "selected_tenant": selected_tenant,
            "tenants": tenants,
            "categories": categories,
            "selected_category": category,
            "start_date": start_date,
            "end_date": end_date,
            "cart_item_count": request.session.get("cart_item_count", 0),
            "sales_trends": sales_trends.get("data", {}),
            # Serialize the data for JavaScript
            "sales_trends_json": json.dumps(sales_trends.get("data", {}))
        }
        
        return templates.TemplateResponse("admin/sales_trends.html", context)
    
    @router.get("/demand-forecast/{product_id}", response_class=HTMLResponse)
    async def demand_forecast(
        request: Request,
        product_id: str,
        forecast_days: int = Query(30, description="Number of days to forecast")
    ):
        """Demand forecast view for a specific product."""
        # Use the tenant utils function to get current tenant
        tenant_obj, tenant_id, tenant_slug = get_current_tenant(request, tenant_manager)
        
        # Log the tenant ID being used
        logger.info(f"Using tenant_id: {tenant_id} for demand forecast (slug: {tenant_slug})")
        
        # Get forecast data
        forecast = market_analysis_service.forecast_demand(
            product_id=product_id,
            forecast_days=forecast_days,
            tenant_id=tenant_id
        )
        
        # Get product details
        product_manager = ProductManager()
        product = product_manager.get(product_id)
        
        if not product:
            # Redirect to products page if product not found
            return RedirectResponse(url="/admin/products")
        
        # Template context
        context = {
            "request": request,
            "active_page": "market_analysis",
            "active_tab": "demand_forecast",
            "page_title": f"Demand Forecast - {product.name}",
            "product": product,
            "forecast_days": forecast_days,
            "cart_item_count": request.session.get("cart_item_count", 0),
            "forecast": forecast.get("data", {}),
            # Serialize the data for JavaScript
            "forecast_json": json.dumps(forecast.get("data", {}))
        }
        
        return templates.TemplateResponse("admin/demand_forecast.html", context)
    
    @router.get("/insights", response_class=HTMLResponse)
    async def market_insights(request: Request):
        """Market insights view."""
        # Use the tenant utils function to get current tenant
        tenant_obj, tenant_id, tenant_slug = get_current_tenant(request, tenant_manager)
        
        # Log the tenant ID being used
        logger.info(f"Using tenant_id: {tenant_id} for market insights (slug: {tenant_slug})")
        
        # Get market insights
        insights = market_analysis_service.get_market_insights(tenant_id=tenant_id)
        
        # Get all tenants for the store selector
        tenants = []
        try:
            tenants_list = tenant_manager.list() or []
            tenants = [
                {
                    "id": str(t.id),
                    "name": t.name,
                    "slug": t.slug,
                    "domain": t.domain if hasattr(t, 'domain') else None,
                    "active": t.active if hasattr(t, 'active') else True
                }
                for t in tenants_list if t and hasattr(t, 'id')
            ]
        except Exception as e:
            logger.error(f"Error fetching tenants: {str(e)}")
        
        # Determine selected tenant for the UI
        selected_tenant = None
        if tenant_slug == "all":
            # Create a special entry for the "All Stores" option
            selected_tenant = {
                "id": "",
                "name": "All Stores",
                "slug": "all",
                "domain": None,
                "active": True
            }
            logger.info("Using 'All Stores' view for market insights")
        else:
            for tenant in tenants:
                if tenant.get("id") == tenant_id:
                    selected_tenant = tenant
                    break
        
        # Template context
        context = {
            "request": request,
            "active_page": "market_analysis",
            "active_tab": "insights",
            "page_title": "Market Insights",
            "selected_tenant": selected_tenant,
            "tenants": tenants,
            "cart_item_count": request.session.get("cart_item_count", 0),
            "insights": insights.get("data", {}),
            # Serialize the data for JavaScript
            "insights_json": json.dumps(insights.get("data", {}))
        }
        
        return templates.TemplateResponse("admin/market_insights.html", context)
    
    @router.get("/category-performance", response_class=HTMLResponse)
    async def category_performance(
        request: Request,
        period: str = Query("month", description="Time period (week, month, quarter, year)")
    ):
        """Category performance view."""
        # Use the tenant utils function to get current tenant
        tenant_obj, tenant_id, tenant_slug = get_current_tenant(request, tenant_manager)
        
        # Log the tenant ID being used
        logger.info(f"Using tenant_id: {tenant_id} for category performance (slug: {tenant_slug})")
        
        # Get category performance data
        category_perf = market_analysis_service.get_category_performance(
            tenant_id=tenant_id,
            period=period
        )
        
        # Get all tenants for the store selector
        tenants = []
        try:
            tenants_list = tenant_manager.list() or []
            tenants = [
                {
                    "id": str(t.id),
                    "name": t.name,
                    "slug": t.slug,
                    "domain": t.domain if hasattr(t, 'domain') else None,
                    "active": t.active if hasattr(t, 'active') else True
                }
                for t in tenants_list if t and hasattr(t, 'id')
            ]
        except Exception as e:
            logger.error(f"Error fetching tenants: {str(e)}")
        
        # Determine selected tenant for the UI
        selected_tenant = None
        if tenant_slug == "all":
            # Create a special entry for the "All Stores" option
            selected_tenant = {
                "id": "",
                "name": "All Stores",
                "slug": "all",
                "domain": None,
                "active": True
            }
            logger.info("Using 'All Stores' view for category performance")
        else:
            for tenant in tenants:
                if tenant.get("id") == tenant_id:
                    selected_tenant = tenant
                    break
        
        # Template context
        context = {
            "request": request,
            "active_page": "market_analysis",
            "active_tab": "category_performance",
            "page_title": "Category Performance",
            "selected_tenant": selected_tenant,
            "tenants": tenants,
            "selected_period": period,
            "periods": ["week", "month", "quarter", "year"],
            "cart_item_count": request.session.get("cart_item_count", 0),
            "category_performance": category_perf.get("data", {}),
            # Serialize the data for JavaScript
            "category_performance_json": json.dumps(category_perf.get("data", {}))
        }
        
        return templates.TemplateResponse("admin/category_performance.html", context)
    
    # API endpoints for AJAX calls
    @router.get("/api/sales-trends")
    async def api_sales_trends(
        request: Request,
        start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
        end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
        category: Optional[str] = Query(None, description="Filter by category")
    ):
        """API endpoint for sales trends data."""
        # Use the tenant utils function to get current tenant
        tenant_obj, tenant_id, tenant_slug = get_current_tenant(request, tenant_manager)
        
        # Log the tenant ID being used
        logger.info(f"[API] Using tenant_id: {tenant_id} for sales trends API (slug: {tenant_slug})")
        
        # Get sales trend data
        sales_trends = market_analysis_service.get_sales_trends(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            category=category
        )
        
        return sales_trends
    
    @router.get("/api/demand-forecast/{product_id}")
    async def api_demand_forecast(
        request: Request,
        product_id: str,
        forecast_days: int = Query(30, description="Number of days to forecast")
    ):
        """API endpoint for demand forecast data."""
        # Use the tenant utils function to get current tenant
        tenant_obj, tenant_id, tenant_slug = get_current_tenant(request, tenant_manager)
        
        # Log the tenant ID being used
        logger.info(f"[API] Using tenant_id: {tenant_id} for demand forecast API (slug: {tenant_slug})")
        
        # Get forecast data
        forecast = market_analysis_service.forecast_demand(
            product_id=product_id,
            forecast_days=forecast_days,
            tenant_id=tenant_id
        )
        
        return forecast
    
    @router.get("/api/insights")
    async def api_market_insights(request: Request):
        """API endpoint for market insights data."""
        # Use the tenant utils function to get current tenant
        tenant_obj, tenant_id, tenant_slug = get_current_tenant(request, tenant_manager)
        
        # Log the tenant ID being used
        logger.info(f"[API] Using tenant_id: {tenant_id} for insights API (slug: {tenant_slug})")
        
        # Get market insights
        insights = market_analysis_service.get_market_insights(tenant_id=tenant_id)
        
        return insights
    
    @router.get("/api/category-performance")
    async def api_category_performance(
        request: Request,
        period: str = Query("month", description="Time period (week, month, quarter, year)")
    ):
        """API endpoint for category performance data."""
        # Use the tenant utils function to get current tenant
        tenant_obj, tenant_id, tenant_slug = get_current_tenant(request, tenant_manager)
        
        # Log the tenant ID being used
        logger.info(f"[API] Using tenant_id: {tenant_id} for category performance API (slug: {tenant_slug})")
        
        # Get category performance data
        category_perf = market_analysis_service.get_category_performance(
            tenant_id=tenant_id,
            period=period
        )
        
        return category_perf
    
    return router