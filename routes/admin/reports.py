"""
Reports management routes for the admin dashboard.

This module provides routes for generating and viewing sales, products, customers,
and tax reports.
"""
import logging
import sys

# Add parent directory to path to allow imports
sys.path.append("..")

try:
    from fastapi import APIRouter, Request, Depends
    from fastapi.templating import Jinja2Templates
    from fastapi.responses import HTMLResponse
    from pycommerce.models.tenant import TenantManager
except ImportError as e:
    logging.error(f"Error importing required modules in reports.py: {e}")

# Initialize managers
tenant_manager = None
try:
    tenant_manager = TenantManager()
except Exception as e:
    logging.error(f"Error initializing managers in reports.py: {e}")

def setup_routes(templates: Jinja2Templates):
    """
    Set up reports management routes.

    Args:
        templates: Jinja2Templates for rendering

    Returns:
        APIRouter: FastAPI router with reports routes
    """
    router = APIRouter()

    @router.get("/admin/reports", response_class=HTMLResponse)
    async def reports(request: Request):
        """Reports dashboard."""
        status_message = request.query_params.get('status_message')
        status_type = request.query_params.get('status_type', 'info')

        # Get tenants
        tenants = []
        if tenant_manager:
            try:
                tenants = tenant_manager.get_all()
            except Exception as e:
                logging.error(f"Error getting tenants in reports route: {e}")

        # Get selected tenant from session or use the first tenant
        selected_tenant_slug = request.session.get("selected_tenant")
        selected_tenant = None

        if selected_tenant_slug and tenant_manager:
            try:
                selected_tenant = tenant_manager.get_by_slug(selected_tenant_slug)
            except Exception as e:
                logging.error(f"Error getting selected tenant: {e}")

        # If no tenant is selected or the selected tenant doesn't exist,
        # use the first available tenant
        if not selected_tenant and tenants:
            selected_tenant = tenants[0]
            request.session["selected_tenant"] = selected_tenant.slug

        # Format tenants for template
        tenants_data = []
        for tenant in tenants:
            tenants_data.append({
                "id": str(tenant.id),
                "name": tenant.name,
                "slug": tenant.slug,
                "domain": tenant.domain,
                "active": tenant.active
            })

        # Get report data
        if selected_tenant_slug and selected_tenant_slug.lower() == "all":
            logger = logging.getLogger(__name__)
            logger.info("Fetching reports for all stores")
            try:
                # First try to get all tenants
                all_tenants = tenant_manager.list() or []

                # Then fetch report data for each tenant and combine them
                all_report_data = []
                for tenant in all_tenants:
                    try:
                        # Replace with actual report data fetching logic
                        tenant_report_data = []  # Replace with actual report data fetching
                        all_report_data.extend(tenant_report_data)
                        logger.info(f"Found {len(tenant_report_data)} report entries for tenant {tenant.name}")
                    except Exception as e:
                        logger.error(f"Error fetching reports for tenant {tenant.name}: {str(e)}")

                report_data = all_report_data
                logger.info(f"Found {len(report_data)} report entries across all stores")
            except Exception as e:
                logger.error(f"Error fetching all reports: {str(e)}")
                report_data = []
        else:
            # Get report data for the selected tenant
            report_data = []  # Replace with actual report data fetching


        return templates.TemplateResponse(
            "admin/reports.html",
            {
                "request": request,
                "active_page": "reports",
                "status_message": status_message,
                "status_type": status_type,
                "tenants": tenants_data,
                "selected_tenant": selected_tenant.slug if selected_tenant else None,
                "cart_item_count": request.session.get("cart_item_count", 0),
                "report_data": report_data
            }
        )

    return router