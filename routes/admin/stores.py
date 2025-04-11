"""
Admin routes for store management.

This module provides routes for managing stores (tenants) in the admin interface.
"""
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from pycommerce.models.tenant import Tenant, TenantManager

logger = logging.getLogger(__name__)

def setup_routes(templates: Jinja2Templates) -> APIRouter:
    """
    Set up routes for store management.
    
    Args:
        templates: Jinja2Templates for template rendering
        
    Returns:
        APIRouter: Router with store management routes
    """
    router = APIRouter(prefix="/admin")
    tenant_manager = TenantManager()
    
    @router.get("/stores", response_class=HTMLResponse)
    async def list_stores(
        request: Request
    ):
        """
        List all stores (tenants) in the admin interface.
        
        Args:
            request: FastAPI request object
        """
        try:
            # Ensure we get all tenants
            if hasattr(tenant_manager, 'get_all'):
                tenants = tenant_manager.get_all()
            elif hasattr(tenant_manager, 'list'):
                tenants = tenant_manager.list()
            else:
                logger.error("TenantManager has no method to list all tenants")
                tenants = []
            
            logger.info(f"Retrieved {len(tenants) if tenants else 0} tenants for stores page")
            
            # Don't use tenant selection on the stores management page
            logger.info(f"Retrieved {len(tenants) if tenants else 0} tenants for stores page")
            return templates.TemplateResponse(
                "admin/stores.html",
                {
                    "request": request,
                    "tenants": tenants,
                    "active_page": "stores"
                }
            )
        except Exception as e:
            logger.error(f"Error listing stores: {str(e)}")
            return templates.TemplateResponse(
                "admin/stores.html",
                {
                    "request": request,
                    "tenants": [],
                    "active_page": "stores",
                    "status_message": f"Error fetching stores: {str(e)}",
                    "status_type": "danger"
                }
            )
    
    @router.get("/stores/new", response_class=HTMLResponse)
    async def new_store_form(
        request: Request
    ):
        """
        Display form for creating a new store (tenant).
        
        Args:
            request: FastAPI request object
        """
        return templates.TemplateResponse(
            "admin/stores/form.html",
            {
                "request": request,
                "tenant": None,
                "action": "/admin/stores/new",
                "title": "Create New Store",
                "active_page": "stores"
            }
        )
    
    @router.post("/stores/new", response_class=HTMLResponse)
    async def create_store(
        request: Request,
        name: str = Form(...),
        slug: str = Form(...),
        domain: Optional[str] = Form(None),
        active: bool = Form(False)
    ):
        """
        Create a new store (tenant).
        
        Args:
            request: FastAPI request object
            name: Store name
            slug: Store slug (URL-friendly identifier)
            domain: Optional custom domain
            active: Whether the store is active
        """
        try:
            # Check if tenant with this slug already exists
            existing = tenant_manager.get_by_slug(slug)
            if existing:
                return templates.TemplateResponse(
                    "admin/stores/form.html",
                    {
                        "request": request,
                        "tenant": {
                            "name": name,
                            "slug": slug,
                            "domain": domain,
                            "active": active
                        },
                        "action": "/admin/stores/new",
                        "title": "Create New Store",
                        "active_page": "stores",
                        "error": f"A store with slug '{slug}' already exists"
                    },
                    status_code=400
                )
            
            # Create new tenant
            settings = {
                'primary_color': '#3498db',
                'secondary_color': '#6c757d',
                'background_color': '#ffffff',
                'text_color': '#212529',
                'font_family': 'Arial, sans-serif',
                'logo_position': 'left'
            }
            
            tenant = tenant_manager.create(
                name=name,
                slug=slug,
                domain=domain,
                active=active,
                settings=settings
            )
            
            logger.info(f"Created new store: {name} (slug: {slug})")
            
            # Redirect to store list
            return RedirectResponse(
                "/admin/stores",
                status_code=status.HTTP_303_SEE_OTHER
            )
            
        except ValidationError as e:
            return templates.TemplateResponse(
                "admin/stores/form.html",
                {
                    "request": request,
                    "tenant": {
                        "name": name,
                        "slug": slug,
                        "domain": domain,
                        "active": active
                    },
                    "action": "/admin/stores/new",
                    "title": "Create New Store",
                    "active_page": "stores",
                    "error": str(e)
                },
                status_code=400
            )
        except Exception as e:
            logger.error(f"Error creating store: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create store: {str(e)}"
            )
    
    @router.get("/stores/{tenant_id}/edit", response_class=HTMLResponse)
    async def edit_store_form(
        request: Request,
        tenant_id: str
    ):
        """
        Display form for editing an existing store (tenant).
        
        Args:
            request: FastAPI request object
            tenant_id: Tenant ID
        """
        tenant = tenant_manager.get(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=404,
                detail=f"Store with ID {tenant_id} not found"
            )
        
        return templates.TemplateResponse(
            "admin/stores/form.html",
            {
                "request": request,
                "tenant": tenant,
                "action": f"/admin/stores/{tenant_id}/edit",
                "title": f"Edit Store: {tenant.name}",
                "active_page": "stores"
            }
        )
    
    @router.post("/stores/{tenant_id}/edit", response_class=HTMLResponse)
    async def update_store(
        request: Request,
        tenant_id: str,
        name: str = Form(...),
        slug: str = Form(...),
        domain: Optional[str] = Form(None),
        active: bool = Form(False)
    ):
        """
        Update an existing store (tenant).
        
        Args:
            request: FastAPI request object
            tenant_id: Tenant ID
            name: Store name
            slug: Store slug (URL-friendly identifier)
            domain: Optional custom domain
            active: Whether the store is active
        """
        try:
            # Check if tenant exists
            tenant = tenant_manager.get(tenant_id)
            if not tenant:
                raise HTTPException(
                    status_code=404,
                    detail=f"Store with ID {tenant_id} not found"
                )
            
            # Check if slug is already used by another tenant
            if slug != tenant.slug:
                existing = tenant_manager.get_by_slug(slug)
                if existing and existing.id != tenant_id:
                    return templates.TemplateResponse(
                        "admin/stores/form.html",
                        {
                            "request": request,
                            "tenant": {
                                "id": tenant_id,
                                "name": name,
                                "slug": slug,
                                "domain": domain,
                                "active": active
                            },
                            "action": f"/admin/stores/{tenant_id}/edit",
                            "title": f"Edit Store: {name}",
                            "active_page": "stores",
                            "error": f"A store with slug '{slug}' already exists"
                        },
                        status_code=400
                    )
            
            # Update tenant
            tenant_manager.update(
                tenant_id=tenant_id,
                name=name,
                slug=slug,
                domain=domain,
                active=active
            )
            
            logger.info(f"Updated store: {name} (slug: {slug})")
            
            # Redirect to store list
            return RedirectResponse(
                "/admin/stores",
                status_code=status.HTTP_303_SEE_OTHER
            )
            
        except ValidationError as e:
            return templates.TemplateResponse(
                "admin/stores/form.html",
                {
                    "request": request,
                    "tenant": {
                        "id": tenant_id,
                        "name": name,
                        "slug": slug,
                        "domain": domain,
                        "active": active
                    },
                    "action": f"/admin/stores/{tenant_id}/edit",
                    "title": f"Edit Store: {name}",
                    "active_page": "stores",
                    "error": str(e)
                },
                status_code=400
            )
        except Exception as e:
            logger.error(f"Error updating store: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update store: {str(e)}"
            )
    
    @router.get("/stores/{tenant_id}/theme", response_class=HTMLResponse)
    async def theme_settings_form(
        request: Request,
        tenant_id: str
    ):
        """
        Display form for editing store theme settings.
        
        Args:
            request: FastAPI request object
            tenant_id: Tenant ID
        """
        tenant = tenant_manager.get(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=404,
                detail=f"Store with ID {tenant_id} not found"
            )
        
        return templates.TemplateResponse(
            "admin/stores/theme.html",
            {
                "request": request,
                "tenant": tenant,
                "action": f"/admin/stores/{tenant_id}/theme",
                "title": f"Theme Settings: {tenant.name}",
                "active_page": "stores"
            }
        )
    
    @router.post("/stores/{tenant_id}/theme", response_class=HTMLResponse)
    async def update_theme_settings(
        request: Request,
        tenant_id: str,
        primary_color: str = Form("#3498db"),
        secondary_color: str = Form("#6c757d"),
        background_color: str = Form("#ffffff"),
        text_color: str = Form("#212529"),
        font_family: str = Form("Arial, sans-serif"),
        logo_position: str = Form("left"),
        custom_css: Optional[str] = Form(None)
    ):
        """
        Update store theme settings.
        
        Args:
            request: FastAPI request object
            tenant_id: Tenant ID
            primary_color: Primary color for buttons and accents
            secondary_color: Secondary color for secondary elements
            background_color: Background color for the site
            text_color: Text color
            font_family: Font family for text
            logo_position: Position of the logo (left, center, right)
            custom_css: Custom CSS to be applied to the storefront
        """
        try:
            # Check if tenant exists
            tenant = tenant_manager.get(tenant_id)
            if not tenant:
                raise HTTPException(
                    status_code=404,
                    detail=f"Store with ID {tenant_id} not found"
                )
            
            # Update theme settings
            settings = tenant.settings or {}
            settings.update({
                'primary_color': primary_color,
                'secondary_color': secondary_color,
                'background_color': background_color,
                'text_color': text_color,
                'font_family': font_family,
                'logo_position': logo_position
            })
            
            if custom_css:
                settings['custom_css'] = custom_css
            
            tenant_manager.update_settings(tenant_id, settings)
            
            logger.info(f"Updated theme settings for store: {tenant.name}")
            
            # Redirect to store list
            return RedirectResponse(
                "/admin/stores",
                status_code=status.HTTP_303_SEE_OTHER
            )
            
        except Exception as e:
            logger.error(f"Error updating theme settings: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update theme settings: {str(e)}"
            )
    
    return router