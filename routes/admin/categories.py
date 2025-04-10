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
# Import CategoryManager with error handling
try:
    from pycommerce.models.category import CategoryManager
except ImportError:
    CategoryManager = None

# Configure logging
logger = logging.getLogger(__name__)

# Router and templates initialized in setup_routes
router = None
templates = None

# Initialize managers
tenant_manager = TenantManager()
# Add compatibility method
if not hasattr(tenant_manager, 'get_tenant_by_slug'):
    tenant_manager.get_tenant_by_slug = tenant_manager.get_by_slug

# Initialize category manager
category_manager = None
if CategoryManager:
    try:
        category_manager = CategoryManager()
    except Exception as e:
        logger.error(f"Error initializing CategoryManager: {e}")

def setup_routes(templates_instance: Jinja2Templates):
    """
    Set up routes for category management.
    
    Args:
        templates_instance: Jinja2 templates instance
        
    Returns:
        APIRouter: FastAPI router
    """
    global templates, router
    templates = templates_instance
    router = APIRouter()
    
    @router.get("/admin/categories", response_class=HTMLResponse)
    async def categories_page(
        request: Request,
        tenant: str = Query("default", description="Tenant slug"),
        parent_id: Optional[str] = Query(None, description="Parent category ID to filter by")
    ):
        """
        Render the categories management page.
        
        Args:
            request: The request object
            tenant: The tenant slug
            parent_id: Optional parent category ID to filter by
        """
        # Get current tenant
        current_tenant = tenant_manager.get_tenant_by_slug(tenant)
        if not current_tenant:
            return RedirectResponse(url="/admin/tenants")
        
        # Initialize context
        context = {
            "request": request,
            "active_page": "categories",
            "tenant": current_tenant,
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
        
        try:
            # Get parent category if specified
            if parent_id:
                parent = category_manager.get_category(parent_id)
                if parent and str(parent.tenant_id) == str(current_tenant.id):
                    context["parent_category"] = parent
                    
                    # Build breadcrumbs for navigation
                    breadcrumbs = []
                    current = parent
                    while current:
                        breadcrumbs.insert(0, current)
                        if current.parent_id:
                            current = category_manager.get_category(current.parent_id)
                        else:
                            current = None
                    
                    context["parent_breadcrumbs"] = breadcrumbs
                    
                    # Get categories that are children of this parent
                    all_categories = category_manager.get_all_categories(str(current_tenant.id))
                    categories = [c for c in all_categories if c.parent_id == parent_id]
                else:
                    # Invalid parent, show root categories
                    parent_id = None
                    all_categories = category_manager.get_all_categories(str(current_tenant.id))
                    categories = [c for c in all_categories if c.parent_id is None]
            else:
                # Show root categories (no parent)
                all_categories = category_manager.get_all_categories(str(current_tenant.id))
                categories = [c for c in all_categories if c.parent_id is None]
            
            # Sort categories by name
            categories.sort(key=lambda x: x.name)
            
            # Add to context
            context["categories"] = categories
            
            # Count products in each category
            for category in categories:
                category.product_count = len(category_manager.get_products_in_category(
                    category.id, include_subcategories=True
                ))
                
                # Count subcategories
                all_categories = category_manager.get_all_categories(str(current_tenant.id))
                category.subcategory_count = len([
                    c for c in all_categories if c.parent_id == category.id
                ])
        
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            context["error"] = f"Error fetching categories: {str(e)}"
        
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