"""
Base module for the PyCommerce SDK.

This module contains the main PyCommerce class which serves as the central
entry point for using the SDK's functionality.
"""

from typing import Dict, List, Optional, Type, Union, Callable, Any
import logging
import uuid
from uuid import UUID
import importlib

# Set up logging first - other imports will use this
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pycommerce")

# Import dependencies with try/except to handle potential missing packages
try:
    from fastapi import FastAPI, Depends, Header, HTTPException, APIRouter
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    FASTAPI_AVAILABLE = True
except ImportError:
    logger.warning("FastAPI not available. API functionality will be disabled.")
    FASTAPI_AVAILABLE = False
    # Create dummy classes to avoid errors
    class FastAPI:
        def __init__(self, **kwargs):
            pass
        def include_router(self, *args, **kwargs):
            pass
        def add_middleware(self, *args, **kwargs):
            pass
        def get(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
            
    class BaseHTTPMiddleware:
        def __init__(self, app):
            self.app = app
    
    class Request:
        def __init__(self):
            self.headers = {}
            self.state = None
    
    class Depends:
        def __init__(self, dependency):
            self.dependency = dependency
    
    class HTTPException(Exception):
        def __init__(self, status_code, detail):
            self.status_code = status_code
            self.detail = detail
            super().__init__(f"{status_code}: {detail}")
    
    class APIRouter:
        def __init__(self):
            pass
        def get(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
        def post(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
        def put(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
        def delete(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator

from pycommerce.core.plugin import PluginManager
from pycommerce.models.product import ProductManager
from pycommerce.models.cart import CartManager
from pycommerce.models.order import OrderManager
from pycommerce.models.user import UserManager
from pycommerce.models.tenant import TenantManager, Tenant
from pycommerce.api.routes import products, cart, checkout, users

class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to extract tenant information from requests."""
    
    def __init__(self, app, tenant_resolver: Callable):
        super().__init__(app)
        self.tenant_resolver = tenant_resolver
    
    async def dispatch(self, request: Request, call_next):
        # Attempt to identify tenant from the request
        try:
            tenant_id = self.tenant_resolver(request)
            request.state.tenant_id = tenant_id
        except Exception as e:
            logger.error(f"Error resolving tenant: {str(e)}")
        
        # Proceed with request
        response = await call_next(request)
        return response


class PyCommerce:
    """
    Main class for the PyCommerce SDK.
    
    This class serves as the central entry point for using the SDK and
    provides access to all core functionality.
    """
    
    def __init__(self, debug: bool = False, multi_tenant: bool = False):
        """
        Initialize a new PyCommerce instance.
        
        Args:
            debug: Whether to enable debug mode
            multi_tenant: Whether to enable multi-tenancy support
        """
        self.debug = debug
        self.multi_tenant = multi_tenant
        
        if debug:
            logger.setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled")
        
        if multi_tenant:
            logger.info("Multi-tenancy mode enabled")
        
        # Initialize managers
        self.plugins = PluginManager()
        self.products = ProductManager()
        self.carts = CartManager()
        self.orders = OrderManager()
        self.users = UserManager()
        self.tenants = TenantManager() if multi_tenant else None
        
        # Initialize tenant data stores
        if multi_tenant:
            self._tenant_products = {}
            self._tenant_carts = {}
            self._tenant_orders = {}
            self._tenant_users = {}
        
        # Initialize FastAPI app
        self.app = None
    
    def get_product_manager(self, tenant_id=None):
        """Get the product manager for a tenant or the default one."""
        if not self.multi_tenant or tenant_id is None:
            return self.products
        
        if tenant_id not in self._tenant_products:
            self._tenant_products[tenant_id] = ProductManager()
        
        return self._tenant_products[tenant_id]
    
    def get_cart_manager(self, tenant_id=None):
        """Get the cart manager for a tenant or the default one."""
        if not self.multi_tenant or tenant_id is None:
            return self.carts
        
        if tenant_id not in self._tenant_carts:
            self._tenant_carts[tenant_id] = CartManager()
        
        return self._tenant_carts[tenant_id]
    
    def get_order_manager(self, tenant_id=None):
        """Get the order manager for a tenant or the default one."""
        if not self.multi_tenant or tenant_id is None:
            return self.orders
        
        if tenant_id not in self._tenant_orders:
            self._tenant_orders[tenant_id] = OrderManager()
        
        return self._tenant_orders[tenant_id]
    
    def get_user_manager(self, tenant_id=None):
        """Get the user manager for a tenant or the default one."""
        if not self.multi_tenant or tenant_id is None:
            return self.users
        
        if tenant_id not in self._tenant_users:
            self._tenant_users[tenant_id] = UserManager()
        
        return self._tenant_users[tenant_id]
    
    def resolve_tenant_from_request(self, request: Request):
        """
        Resolve the tenant ID from an HTTP request.
        
        By default, this looks for a tenant slug in the hostname or a tenant header.
        This method can be overridden to implement custom tenant resolution logic.
        
        Args:
            request: The HTTP request
            
        Returns:
            The tenant ID, or None if no tenant could be resolved
        """
        if not self.multi_tenant:
            return None
        
        # Look for a tenant header
        tenant_header = request.headers.get("X-Tenant-ID")
        if tenant_header:
            try:
                return self.tenants.get(tenant_header).id
            except ValueError:
                pass
        
        # Look for a tenant slug in the hostname
        hostname = request.headers.get("host", "").split(":")[0]
        if hostname:
            try:
                return self.tenants.get_by_domain(hostname).id
            except ValueError:
                # If not found by domain, try to extract a slug from a subdomain
                subdomain = hostname.split(".")[0]
                try:
                    return self.tenants.get_by_slug(subdomain).id
                except ValueError:
                    pass
        
        return None
    
    def create_app(self, title: str = "PyCommerce API", 
                  description: str = "API for PyCommerce SDK",
                  version: str = "0.1.0") -> FastAPI:
        """
        Create and configure a FastAPI application with all routes.
        
        Args:
            title: The title of the API
            description: The description of the API
            version: The version of the API
            
        Returns:
            The configured FastAPI application
        """
        self.app = FastAPI(title=title, description=description, version=version)
        
        # Add tenant middleware if in multi-tenant mode
        if self.multi_tenant:
            self.app.add_middleware(
                TenantMiddleware,
                tenant_resolver=self.resolve_tenant_from_request
            )
            
            # Create a dependency to get the current tenant ID
            async def get_tenant_id(request: Request):
                tenant_id = getattr(request.state, "tenant_id", None)
                if tenant_id is None:
                    raise HTTPException(status_code=400, detail="Tenant not found")
                return tenant_id
        
        # Include API routes
        self.app.include_router(products.router, prefix="/api/products", tags=["products"])
        self.app.include_router(cart.router, prefix="/api/cart", tags=["cart"])
        self.app.include_router(checkout.router, prefix="/api/checkout", tags=["checkout"])
        self.app.include_router(users.router, prefix="/api/users", tags=["users"])
        
        # Set dependencies for routes
        if self.multi_tenant:
            # In multi-tenant mode, use tenant-specific managers
            async def get_product_manager(tenant_id = Depends(get_tenant_id)):
                return self.get_product_manager(tenant_id)
                
            async def get_cart_manager(tenant_id = Depends(get_tenant_id)):
                return self.get_cart_manager(tenant_id)
                
            async def get_order_manager(tenant_id = Depends(get_tenant_id)):
                return self.get_order_manager(tenant_id)
                
            async def get_user_manager(tenant_id = Depends(get_tenant_id)):
                return self.get_user_manager(tenant_id)
                
            # Check if the routes modules have the necessary functions
            if hasattr(products, 'set_product_manager_func'):
                products.set_product_manager_func(get_product_manager)
            elif hasattr(products, 'set_product_manager'):
                products.set_product_manager(get_product_manager)
                
            if hasattr(cart, 'set_cart_manager_func'):
                cart.set_cart_manager_func(get_cart_manager)
            elif hasattr(cart, 'set_cart_manager'):
                cart.set_cart_manager(get_cart_manager)
                
            if hasattr(checkout, 'set_order_manager_func'):
                checkout.set_order_manager_func(get_order_manager)
            elif hasattr(checkout, 'set_order_manager'):
                checkout.set_order_manager(get_order_manager)
                
            if hasattr(users, 'set_user_manager_func'):
                users.set_user_manager_func(get_user_manager)
            elif hasattr(users, 'set_user_manager'):
                users.set_user_manager(get_user_manager)
        else:
            # In single-tenant mode, use the default managers
            if hasattr(products, 'set_product_manager'):
                products.set_product_manager(self.products)
            if hasattr(cart, 'set_cart_manager'):
                cart.set_cart_manager(self.carts)
            if hasattr(checkout, 'set_order_manager'):
                checkout.set_order_manager(self.orders)
            if hasattr(users, 'set_user_manager'):
                users.set_user_manager(self.users)
        
        # Register plugin routes
        self.plugins.register_routes(self.app)
        
        # Add root endpoint with SDK info
        @self.app.get("/", tags=["info"])
        async def get_info():
            return {
                "name": "PyCommerce SDK",
                "version": version,
                "multi_tenant": self.multi_tenant,
                "plugins": self.plugins.list_plugins(),
            }
        
        # Add tenant management endpoints in multi-tenant mode
        if self.multi_tenant:
            from fastapi import APIRouter
            tenant_router = APIRouter()
            
            @tenant_router.get("/", tags=["tenants"])
            async def list_tenants():
                return self.tenants.list()
            
            @tenant_router.post("/", tags=["tenants"])
            async def create_tenant(tenant_data: dict):
                return self.tenants.create(**tenant_data)
            
            @tenant_router.get("/{tenant_id}", tags=["tenants"])
            async def get_tenant(tenant_id: str):
                try:
                    tenant_uuid = UUID(tenant_id)
                    return self.tenants.get(tenant_uuid)
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid tenant ID format: {tenant_id}"
                    )
                except Exception as e:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Tenant not found: {tenant_id}"
                    )
            
            @tenant_router.put("/{tenant_id}", tags=["tenants"])
            async def update_tenant(tenant_id: str, tenant_data: dict):
                try:
                    tenant_uuid = UUID(tenant_id)
                    return self.tenants.update(tenant_uuid, tenant_data)
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid tenant ID format: {tenant_id}"
                    )
                except Exception as e:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Error updating tenant: {str(e)}"
                    )
            
            @tenant_router.delete("/{tenant_id}", tags=["tenants"])
            async def delete_tenant(tenant_id: str):
                try:
                    tenant_uuid = UUID(tenant_id)
                    result = self.tenants.delete(tenant_uuid)
                    return {"success": result, "message": "Tenant deleted successfully"}
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid tenant ID format: {tenant_id}"
                    )
                except Exception as e:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Error deleting tenant: {str(e)}"
                    )
            
            self.app.include_router(tenant_router, prefix="/api/tenants", tags=["tenants"])
        
        logger.info(f"Created FastAPI application with title: {title}")
        return self.app
