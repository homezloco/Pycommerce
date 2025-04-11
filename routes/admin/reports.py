"""
Reports management routes for the admin dashboard.

This module provides routes for generating and viewing sales, products, customers,
and tax reports.
"""
import logging
import sys
from typing import Optional

# Add parent directory to path to allow imports
sys.path.append("..")

try:
    from fastapi import APIRouter, Request, Depends
    from fastapi.templating import Jinja2Templates
    from fastapi.responses import HTMLResponse, RedirectResponse
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
    async def reports(request: Request, tenant: Optional[str] = None):
        """Reports dashboard."""
        status_message = request.query_params.get('status_message')
        status_type = request.query_params.get('status_type', 'info')
        logger = logging.getLogger(__name__)

        # Get tenant from query parameters or session
        selected_tenant_slug = tenant or request.session.get("selected_tenant")

        # If no tenant is selected, redirect to dashboard with message
        if not selected_tenant_slug:
            return RedirectResponse(
                url="/admin/dashboard?status_message=Please+select+a+store+first&status_type=warning", 
                status_code=303
            )

        # Store the selected tenant in session for future requests
        request.session["selected_tenant"] = selected_tenant_slug

        # Get tenants for sidebar
        tenants = []
        if tenant_manager:
            try:
                tenants = tenant_manager.get_all()
            except Exception as e:
                logging.error(f"Error getting tenants in reports route: {e}")

        # Handle "all" tenant slug case
        if selected_tenant_slug.lower() == "all":
            logger.info("Using 'All Stores' selection in reports page")
            from routes.admin.tenant_utils import create_virtual_all_tenant, get_objects_for_all_tenants
            selected_tenant = type('AllStoresTenant', (), create_virtual_all_tenant())
            
            # Use the generalized utility function to get reports for all tenants
            try:
                # First try to get all tenants
                all_tenants = tenant_manager.list() or []
                
                # Define a report manager or function if one exists
                # For demonstration, we'll use a placeholder
                # In a real implementation, you would use an actual report manager
                class ReportManager:
                    @staticmethod
                    def get_for_tenant(tenant_id, **kwargs):
                        # Placeholder for report data fetching logic
                        # This should be replaced with actual implementation
                        return [{"id": f"report_{tenant_id}_{i}", "name": f"Report {i} for tenant {tenant_id}"} for i in range(3)]
                
                report_manager = ReportManager()
                
                # Get reports for all tenants using the generalized utility function
                report_data = get_objects_for_all_tenants(
                    tenant_manager=tenant_manager,
                    object_manager=report_manager,
                    get_method_name="get_for_tenant",
                    id_param_name="tenant_id",
                    logger=logger,
                    fallback_method_name=None
                )
                
                logger.info(f"Found {len(report_data)} report entries across all stores")
                
                # If no reports found, initialize to empty list
                if not report_data:
                    report_data = []
            except Exception as e:
                logger.error(f"Error fetching all reports: {str(e)}")
                report_data = []
        else:
            # Get tenant object
            selected_tenant = tenant_manager.get_by_slug(selected_tenant_slug) if tenant_manager else None
            if not selected_tenant:
                return RedirectResponse(
                    url="/admin/dashboard?status_message=Store+not+found&status_type=error", 
                    status_code=303
                )

            # Get report data for the specific tenant
            report_data = []  # Replace with actual report data fetching

        # Format tenants for template
        tenants_data = []
        for tenant in tenants:
            tenants_data.append({
                "id": str(tenant.id),
                "name": tenant.name,
                "slug": tenant.slug,
                "domain": getattr(tenant, 'domain', ''),
                "active": getattr(tenant, 'active', True)
            })

        return templates.TemplateResponse(
            "admin/reports.html",
            {
                "request": request,
                "active_page": "reports",
                "status_message": status_message,
                "status_type": status_type,
                "tenants": tenants_data,
                "selected_tenant": selected_tenant_slug,
                "tenant": selected_tenant,
                "cart_item_count": request.session.get("cart_item_count", 0),
                "report_data": report_data
            }
        )

    return router