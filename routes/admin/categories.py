"""
Categories management routes for the PyCommerce admin panel.

This module provides routes for managing product categories in the admin panel.
"""
import logging
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Request, Form, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from pycommerce.models.tenant import TenantManager
# Configure logging
logger = logging.getLogger(__name__)

# Router and templates initialized in setup_routes
router = None
templates = None

# Shared manager instances - initialized in setup_routes to avoid early initialization
tenant_manager = None
category_manager = None

# Flag to track initialization
_managers_initialized = False

def setup_routes(templates_instance: Jinja2Templates):
    """
    Set up routes for category management.

    Args:
        templates_instance: Jinja2 templates instance

    Returns:
        APIRouter: FastAPI router
    """
    global templates, router, tenant_manager, category_manager, _managers_initialized
    templates = templates_instance
    router = APIRouter()

    # Initialize managers only once, and only when this function is called (not at import time)
    if not _managers_initialized:
        try:
            logger.info("Initializing managers for categories routes")
            # Initialize tenant manager
            tenant_manager = TenantManager()
            # Add compatibility method
            if not hasattr(tenant_manager, 'get_tenant_by_slug'):
                tenant_manager.get_tenant_by_slug = tenant_manager.get_by_slug

            # Initialize category manager
            try:
                from pycommerce.models.category import CategoryManager
                category_manager = CategoryManager()
                logger.info("Successfully initialized CategoryManager for admin categories routes")
            except ImportError as e:
                logger.error(f"Failed to import CategoryManager: {e}")
                category_manager = None
            except Exception as e:
                logger.error(f"Error initializing CategoryManager: {e}")
                category_manager = None

            _managers_initialized = True
            logger.info("Manager initialization complete")
        except Exception as e:
            logger.error(f"Failed to initialize managers: {e}")
            # Set default values so the app doesn't crash
            if not tenant_manager:
                tenant_manager = TenantManager()
            if not category_manager:
                category_manager = None

    @router.get("/admin/categories", response_class=HTMLResponse)
    async def categories_page(
        request: Request,
        tenant: str = Query(None, description="Tenant slug"),
        parent_id: Optional[str] = Query(None, description="Parent category ID to filter by")
    ):
        """
        Render the categories management page.

        Args:
            request: The request object
            tenant: The tenant slug
            parent_id: Optional parent category ID to filter by
        """
        # Initialize variables
        all_tenants = []
        tenant_categories = []
        categories = []
        parent_category = None
        parent_breadcrumbs = []
        error_message = None

        # Check if tenant is specified in the URL or use the one from session
        selected_tenant_slug = tenant
        if not selected_tenant_slug:
            selected_tenant_slug = request.session.get("selected_tenant", "tech")

        # Get current tenant
        logger.info(f"Attempting to access categories for tenant: {selected_tenant_slug}")
        current_tenant = tenant_manager.get_tenant_by_slug(selected_tenant_slug)
        if not current_tenant:
            # Instead of redirecting, log the issue and try to get the first tenant
            logger.warning(f"Tenant with slug '{selected_tenant_slug}' not found, trying to find another tenant")

            # Try different method names for compatibility
            try:
                if hasattr(tenant_manager, 'get_all_tenants'):
                    tenants = tenant_manager.get_all_tenants()
                elif hasattr(tenant_manager, 'get_all'):
                    tenants = tenant_manager.get_all()
                elif hasattr(tenant_manager, 'list'):
                    tenants = tenant_manager.list()
                else:
                    tenants = []

                if tenants and len(tenants) > 0:
                    current_tenant = tenants[0]
                    logger.info(f"Using first available tenant: {current_tenant.name} ({current_tenant.slug})")
                else:
                    logger.error("No tenants found in the system")
                    return RedirectResponse(url="/admin/tenants")
            except Exception as e:
                logger.error(f"Error finding alternative tenant: {e}")
                return RedirectResponse(url="/admin/tenants")

        # Get all tenants for store selector
        try:
            if hasattr(tenant_manager, 'get_all_tenants'):
                all_tenants = tenant_manager.get_all_tenants()
            elif hasattr(tenant_manager, 'get_all'):
                all_tenants = tenant_manager.get_all()
            elif hasattr(tenant_manager, 'list'):
                all_tenants = tenant_manager.list()
            else:
                logger.warning("TenantManager doesn't have get_all_tenants, get_all, or list methods")
                all_tenants = []
        except Exception as e:
            logger.error(f"Error getting all tenants: {e}")
            all_tenants = []

        # Initialize context with what we have so far
        context = {
            "request": request,
            "active_page": "categories",
            "tenant": current_tenant,
            "tenants": all_tenants,
            "selected_tenant": selected_tenant_slug,
            "categories": [],
            "parent_category": None,
            "parent_breadcrumbs": [],
            "error": None,
            "success": None
        }

        # Check if CategoryManager is available
        if not category_manager:
            context["error"] = "Category management is not available. The CategoryManager module could not be loaded."
            return templates.TemplateResponse("admin/categories.html", context)

        # Get categories and process them
        try:
            if selected_tenant_slug.lower() == "all":
                # Fetch categories from all tenants
                from routes.admin.tenant_utils import get_categories_for_all_tenants
                logger.info("Fetching categories from all tenants")
                try:
                    categories = get_categories_for_all_tenants(
                        tenant_manager=tenant_manager,
                        category_manager=category_manager, 
                        logger=logger,
                        include_inactive=True
                    )
                    
                    if not categories:
                        error_message = "No categories found across all stores."
                except Exception as e:
                    logger.error(f"Error fetching categories from all tenants: {str(e)}")
                    categories = []
                    error_message = f"Error fetching categories: {str(e)}"
            else:
                # Get categories for a specific tenant
                logger.info(f"Getting categories for tenant: {current_tenant.name}")
                tenant_categories = category_manager.get_all_categories(current_tenant.id)

                # Handle None case
                if tenant_categories is None:
                    tenant_categories = []
                    logger.error(f"Failed to get categories for tenant: {current_tenant.id}")
                    context["error"] = "Failed to retrieve categories. Please try again later."

                # Filter categories based on parent_id
                if parent_id:
                    # Get the parent category
                    parent_category = category_manager.get_category(parent_id)
                    if parent_category:
                        # Check if this parent belongs to the current tenant
                        if parent_category.tenant_id != current_tenant.id:
                            context["error"] = "Selected category does not belong to this tenant."
                            return templates.TemplateResponse("admin/categories.html", context)

                        # Build breadcrumb path
                        breadcrumbs = []
                        current_parent = parent_category
                        while current_parent:
                            breadcrumbs.insert(0, current_parent)
                            if current_parent.parent_id:
                                current_parent = category_manager.get_category(current_parent.parent_id)
                            else:
                                current_parent = None

                        context["parent_category"] = parent_category
                        context["parent_breadcrumbs"] = breadcrumbs

                        # Get categories with this parent
                        categories = [cat for cat in tenant_categories 
                                    if cat.parent_id == parent_id]
                    else:
                        # Invalid parent ID, show root categories
                        context["error"] = "Selected parent category not found."
                        categories = [cat for cat in tenant_categories 
                                    if not cat.parent_id]
                else:
                    # Show root categories (those without parents)
                    categories = [cat for cat in tenant_categories 
                                 if not cat.parent_id]

                # Calculate product and subcategory counts for each category
                for category in categories:
                    # Get direct products in this category
                    products_in_category = category_manager.get_products_in_category(category.id, include_subcategories=False)
                    category.product_count = len(products_in_category) if products_in_category else 0

                    # Count subcategories - reuse tenant_categories to avoid extra database queries
                    subcategories = [cat for cat in tenant_categories 
                                   if cat.parent_id == category.id]
                    category.subcategory_count = len(subcategories) if subcategories else 0

            # Update context with processed categories
            context["categories"] = categories
            context["error"] = error_message

        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            context["error"] = f"Error fetching categories: {str(e)}"

        # Return the template response
        return templates.TemplateResponse("admin/categories.html", context)

    @router.post("/admin/categories/create", response_class=HTMLResponse)
    async def create_category(
        request: Request,
        tenant: str = Form(...),
        name: str = Form(...),
        slug: str = Form(...),
        description: str = Form(""),
        parent_id: Optional[str] = Form(None),
        active: bool = Form(True)
    ):
        """
        Create a new category.

        Args:
            request: The request object
            tenant: The tenant slug
            name: The category name
            slug: The category slug
            description: The category description
            parent_id: The parent category ID (if any)
            active: Whether the category is active
        """
        # Get current tenant
        current_tenant = tenant_manager.get_tenant_by_slug(tenant)
        if not current_tenant:
            return RedirectResponse(url="/admin/tenants")

        # Initialize redirect URL
        redirect_url = f"/admin/categories?tenant={tenant}"
        if parent_id:
            redirect_url += f"&parent_id={parent_id}"

        # Check if CategoryManager is available
        if not category_manager:
            return RedirectResponse(url=f"{redirect_url}&error=Category management is not available")

        try:
            # Create the category
            category = category_manager.create_category(
                tenant_id=current_tenant.id,
                name=name,
                slug=slug,
                description=description,
                parent_id=parent_id,
                active=active
            )

            # Redirect to categories page with success message
            return RedirectResponse(
                url=f"{redirect_url}&success=Category {name} created successfully", 
                status_code=303
            )

        except Exception as e:
            logger.error(f"Error creating category: {e}")
            return RedirectResponse(
                url=f"{redirect_url}&error={str(e)}",
                status_code=303
            )

    @router.post("/admin/categories/{category_id}/update", response_class=HTMLResponse)
    async def update_category(
        category_id: str,
        request: Request,
        tenant: str = Form(...),
        name: str = Form(...),
        slug: str = Form(...),
        description: str = Form(""),
        parent_id: Optional[str] = Form(None),
        active: bool = Form(True)
    ):
        """
        Update an existing category.

        Args:
            category_id: The category ID to update
            request: The request object
            tenant: The tenant slug
            name: The updated category name
            slug: The updated category slug
            description: The updated category description
            parent_id: The updated parent category ID (if any)
            active: Whether the category is active
        """
        # Get current tenant
        current_tenant = tenant_manager.get_tenant_by_slug(tenant)
        if not current_tenant:
            return RedirectResponse(url="/admin/tenants")

        # Initialize redirect URL (to the parent view if applicable)
        category = category_manager.get_category(category_id) if category_manager else None
        displayed_parent_id = parent_id if parent_id else (category.parent_id if category else None)

        redirect_url = f"/admin/categories?tenant={tenant}"
        if displayed_parent_id:
            redirect_url += f"&parent_id={displayed_parent_id}"

        # Check if CategoryManager is available
        if not category_manager:
            return RedirectResponse(
                url=f"{redirect_url}&error=Category management is not available",
                status_code=303
            )

        try:
            # Update the category
            updated_category = category_manager.update_category(
                category_id=category_id,
                name=name,
                slug=slug,
                description=description,
                parent_id=parent_id,
                active=active
            )

            if not updated_category:
                return RedirectResponse(
                    url=f"{redirect_url}&error=Category not found",
                    status_code=303
                )

            # Redirect to categories page with success message
            return RedirectResponse(
                url=f"{redirect_url}&success=Category {name} updated successfully", 
                status_code=303
            )

        except Exception as e:
            logger.error(f"Error updating category: {e}")
            return RedirectResponse(
                url=f"{redirect_url}&error={str(e)}",
                status_code=303
            )

    @router.post("/admin/categories/{category_id}/delete", response_class=HTMLResponse)
    async def delete_category(
        category_id: str,
        request: Request,
        tenant: str = Form(...)
    ):
        """
        Delete a category.

        Args:
            category_id: The category ID to delete
            request: The request object
            tenant: The tenant slug
        """
        # Get current tenant
        current_tenant = tenant_manager.get_tenant_by_slug(tenant)
        if not current_tenant:
            return RedirectResponse(url="/admin/tenants")

        # Get the category to find its parent for redirect
        category = category_manager.get_category(category_id) if category_manager else None
        parent_id = category.parent_id if category else None

        # Initialize redirect URL
        redirect_url = f"/admin/categories?tenant={tenant}"
        if parent_id:
            redirect_url += f"&parent_id={parent_id}"

        # Check if CategoryManager is available
        if not category_manager:
            return RedirectResponse(
                url=f"{redirect_url}&error=Category management is not available",
                status_code=303
            )

        try:
            # Remember the name for the success message
            category_name = category.name if category else "Unknown"

            # Delete the category
            success = category_manager.delete_category(category_id)

            if not success:
                return RedirectResponse(
                    url=f"{redirect_url}&error=Failed to delete category. It may have subcategories or not exist.",
                    status_code=303
                )

            # Redirect to categories page with success message
            return RedirectResponse(
                url=f"{redirect_url}&success=Category {category_name} deleted successfully", 
                status_code=303
            )

        except Exception as e:
            logger.error(f"Error deleting category: {e}")
            return RedirectResponse(
                url=f"{redirect_url}&error={str(e)}",
                status_code=303
            )

    return router