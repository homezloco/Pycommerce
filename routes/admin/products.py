"""
Admin routes for product management.

This module contains all the routes for managing products in the admin interface.
"""
import logging
from typing import Optional, List, Dict, Any
import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

# Template setup will be passed from main app
templates = None

# Initialize logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin"])

# Import models and managers for products
try:
    from pycommerce.models.tenant import TenantManager
    from pycommerce.models.product import ProductManager
    from pycommerce.services.media_service import MediaService
    
    # Initialize managers and services
    tenant_manager = TenantManager()
    product_manager = ProductManager()
    # CategoryManager may not exist, so we'll handle it gracefully
    category_manager = None
    media_service = MediaService()
except ImportError as e:
    logger.error(f"Error importing product modules: {str(e)}")
    tenant_manager = None
    product_manager = None
    category_manager = None
    media_service = None

@router.get("/products", response_class=HTMLResponse)
async def admin_products(
    request: Request,
    tenant: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[str] = None,
    max_price: Optional[str] = None,
    status_message: Optional[str] = None,
    status_type: str = "info"
):
    """Admin page for managing products."""
    # Convert price strings to float if present and not empty
    min_price_float = None
    if min_price and min_price.strip():
        try:
            min_price_float = float(min_price)
        except ValueError:
            pass
            
    max_price_float = None
    if max_price and max_price.strip():
        try:
            max_price_float = float(max_price)
        except ValueError:
            pass
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
    
    # Get tenant object
    tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
    if not tenant_obj:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Store+not+found&status_type=error", 
            status_code=303
        )
    
    # Get products for tenant
    logger.info(f"Fetching products for tenant: {tenant_obj.name} (ID: {tenant_obj.id})")
    products = product_manager.get_by_tenant(str(tenant_obj.id))
    logger.info(f"Found {len(products)} products for tenant {tenant_obj.name}")
    
    # Log product details for debugging
    for idx, p in enumerate(products):
        logger.info(f"Product {idx+1}: ID={p.id}, Name={p.name}, Price={p.price}")
    
    # Apply filters if specified
    if category:
        products = [p for p in products if hasattr(p, 'categories') and category in p.categories]
    if min_price_float is not None:
        products = [p for p in products if hasattr(p, 'price') and float(p.price) >= min_price_float]
    if max_price_float is not None:
        products = [p for p in products if hasattr(p, 'price') and float(p.price) <= max_price_float]
    
    # Format products for HTML
    products_html_rows = ""
    products_list = []
    for product in products:
        product_id = str(product.id)
        name = product.name
        description = product.description if hasattr(product, "description") else ""
        price = product.price
        stock = product.stock if hasattr(product, "stock") else 0
        sku = product.sku if hasattr(product, "sku") else ""
        tenant_name = tenant_obj.name
        categories = product.categories if hasattr(product, "categories") else []
        
        # Create HTML table row for this product
        products_html_rows += f"""
        <tr>
            <td class="text-muted small">{product_id[:8]}...</td>
            <td>
                <strong>{name}</strong>
                <div class="small text-muted">SKU: {sku}</div>
            </td>
            <td>
                <span class="badge bg-dark rounded-pill">{tenant_name}</span>
            </td>
            <td><span class="fw-bold">${price}</span></td>
            <td>
                <span class="badge {stock > 10 and 'bg-success' or (stock > 0 and 'bg-warning' or 'bg-danger')} rounded-pill">
                    {stock} {stock == 1 and 'unit' or 'units'}
                </span>
            </td>
            <td class="text-end">
                <a href="/admin/products/edit/{product_id}" class="btn btn-sm btn-primary me-1">
                    <i class="fas fa-edit"></i> Edit
                </a>
                <a href="/admin/products/delete/{product_id}" class="btn btn-sm btn-danger" 
                   onclick="return confirm('Are you sure you want to delete this product?')">
                    <i class="fas fa-trash"></i> Delete
                </a>
            </td>
        </tr>
        """
        
        # Also store in list for potential future template use
        product_dict = {
            "id": product_id,
            "name": name,
            "description": description,
            "price": price,
            "stock": stock,
            "sku": sku,
            "categories": categories,
            "image_url": product.image_url if hasattr(product, "image_url") else None,
            "tenant_name": tenant_name
        }
        products_list.append(product_dict)
        logger.info(f"Added product to template: {product_dict['name']} with tenant_name={product_dict['tenant_name']}")
    
    # If no products found
    if not products_html_rows:
        products_html_rows = '<tr><td colspan="6" class="text-center">No products found for this tenant</td></tr>'
    
    logger.info(f"Total products for template: {len(products_list)}")
    
    # Get categories for filter
    categories = []
    if category_manager:
        try:
            categories = category_manager.get_by_tenant(str(tenant_obj.id))
        except Exception as e:
            logger.warning(f"Error getting categories: {str(e)}")
    
    # Format categories for dropdown
    categories_options = ""
    for cat in categories:
        cat_name = cat.name if hasattr(cat, "name") else str(cat)
        categories_options += f'<option value="{cat_name}" {"selected" if category == cat_name else ""}>{cat_name}</option>'
    
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
    
    # Format tenants for dropdown
    tenant_options = ""
    for t in tenants:
        if t["slug"] != selected_tenant_slug:  # Skip current store
            tenant_options += f'<option value="{t["slug"]}">{t["name"]}</option>'
    
    # Status message display
    status_alert = ""
    if status_message:
        status_alert = f"""
        <div class="alert alert-{status_type} alert-dismissible fade show" role="alert">
            {status_message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
        """
    
    # Generate direct HTML output
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PyCommerce - Product Management</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <link rel="stylesheet" href="/static/css/admin.css">
        <link rel="icon" href="/static/favicon.ico" type="image/x-icon">
    </head>
    <body>
        <!-- Top Navigation Bar -->
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark fixed-top">
            <div class="container-fluid">
                <a class="navbar-brand" href="/">
                    <i class="fas fa-shopping-cart me-2"></i>PyCommerce
                </a>
                
                <!-- Store selector in navbar -->
                <div class="store-selector">
                    <select class="form-select form-select-sm" id="storeSelector" onchange="window.location='/admin/products?tenant='+this.value">
                        <option value="{selected_tenant_slug}" selected>{tenant_obj.name}</option>
                        {tenant_options}
                    </select>
                </div>
                
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav me-auto">
                        <li class="nav-item">
                            <a class="nav-link" href="/admin/dashboard">
                                <i class="fas fa-tachometer-alt me-1"></i>Dashboard
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link active" href="/admin/products">
                                <i class="fas fa-box me-1"></i>Products
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/admin/orders">
                                <i class="fas fa-shopping-bag me-1"></i>Orders
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/admin/shipping">
                                <i class="fas fa-truck me-1"></i>Shipping
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/admin/reports">
                                <i class="fas fa-chart-bar me-1"></i>Reports
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/admin/settings">
                                <i class="fas fa-cog me-1"></i>Settings
                            </a>
                        </li>
                    </ul>
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link" href="/" target="_blank">
                                <i class="fas fa-external-link-alt me-1"></i>View Store
                            </a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>

        <!-- Main Content -->
        <div class="container-fluid py-4 mt-4">
            <div class="row mb-4">
                <div class="col">
                    <h1 class="display-6">Product Management</h1>
                    <nav aria-label="breadcrumb">
                        <ol class="breadcrumb">
                            <li class="breadcrumb-item"><a href="/admin/dashboard">Admin</a></li>
                            <li class="breadcrumb-item active" aria-current="page">Products</li>
                        </ol>
                    </nav>
                    
                    {status_alert}
                </div>
            </div>
            
            <!-- Filter Panel -->
            <div class="card mb-4">
                <div class="card-header">
                    <div class="d-flex justify-content-between align-items-center">
                        <h5><i class="fas fa-filter me-2"></i>Filter Products</h5>
                        <button class="btn btn-sm btn-outline-secondary" type="button" data-bs-toggle="collapse" data-bs-target="#filterCollapse">
                            <i class="fas fa-chevron-down"></i>
                        </button>
                    </div>
                </div>
                <div class="card-body collapse show" id="filterCollapse">
                    <form action="/admin/products" method="get" class="row g-3">
                        <input type="hidden" name="tenant" value="{selected_tenant_slug}">
                        
                        <div class="col-md-3">
                            <label for="category" class="form-label">Category</label>
                            <select name="category" id="category" class="form-select">
                                <option value="">All Categories</option>
                                {categories_options}
                            </select>
                        </div>
                        
                        <div class="col-md-3">
                            <label for="min_price" class="form-label">Min Price</label>
                            <div class="input-group">
                                <span class="input-group-text">$</span>
                                <input type="number" class="form-control" id="min_price" name="min_price" 
                                       value="{min_price if min_price else ''}" step="0.01" min="0">
                            </div>
                        </div>
                        
                        <div class="col-md-3">
                            <label for="max_price" class="form-label">Max Price</label>
                            <div class="input-group">
                                <span class="input-group-text">$</span>
                                <input type="number" class="form-control" id="max_price" name="max_price" 
                                       value="{max_price if max_price else ''}" step="0.01" min="0">
                            </div>
                        </div>
                        
                        <div class="col-md-3 d-flex align-items-end">
                            <button type="submit" class="btn btn-primary me-2">
                                <i class="fas fa-search me-1"></i>Filter
                            </button>
                            <a href="/admin/products?tenant={selected_tenant_slug}" class="btn btn-outline-secondary">
                                <i class="fas fa-times me-1"></i>Clear
                            </a>
                        </div>
                    </form>
                </div>
            </div>
            
            <!-- Products Table -->
            <div class="card">
                <div class="card-header">
                    <div class="d-flex justify-content-between align-items-center">
                        <h3><i class="fas fa-boxes me-2"></i>Products</h3>
                        <a href="/admin/products/add" class="btn btn-success">
                            <i class="fas fa-plus me-1"></i>Add New Product
                        </a>
                    </div>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-striped table-hover">
                            <thead>
                                <tr>
                                    <th width="5%">ID</th>
                                    <th width="30%">Name</th>
                                    <th width="20%">Store</th>
                                    <th width="10%">Price</th>
                                    <th width="10%">Stock</th>
                                    <th width="25%" class="text-end">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {products_html_rows}
                            </tbody>
                        </table>
                    </div>
                </div>
                <div class="card-footer text-muted">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>Showing {len(products_list)} products</div>
                        <div>
                            <a href="/admin/products/add" class="btn btn-sm btn-success">
                                <i class="fas fa-plus me-1"></i>Add Product
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <footer class="bg-light mt-5 py-3 text-center text-muted">
            <div class="container">
                <p class="mb-0">PyCommerce Admin Panel</p>
            </div>
        </footer>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    # Add debugging
    logger.info(f"Context products type: {type(products_list)}")
    logger.info(f"Context products length: {len(products_list)}")
    if products_list:
        logger.info(f"First product in context: {products_list[0]}")
    
    # Return the HTML directly instead of using a template
    return HTMLResponse(content=html)


@router.get("/products/add", response_class=HTMLResponse)
async def admin_add_product_form(
    request: Request,
    tenant: Optional[str] = None
):
    """Admin form for adding a new product."""
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
    
    # Get tenant object
    tenant_obj = tenant_manager.get_by_slug(selected_tenant_slug)
    if not tenant_obj:
        return RedirectResponse(
            url="/admin/dashboard?status_message=Store+not+found&status_type=error", 
            status_code=303
        )
    
    # Get categories for tenant
    categories = []
    if category_manager:
        try:
            categories = category_manager.get_by_tenant(str(tenant_obj.id))
        except Exception as e:
            logger.warning(f"Error getting categories: {str(e)}")
    
    # Get media files for tenant
    media_files = []
    try:
        media_files = media_service.list_media(tenant_id=str(tenant_obj.id), file_type="image")
    except Exception as e:
        logger.warning(f"Error getting media files: {str(e)}")
    
    # Format media for template
    media_list = []
    for media in media_files:
        media_list.append({
            "id": str(media.id),
            "name": media.name if hasattr(media, "name") else (media.file_name if hasattr(media, "file_name") else ""),
            "url": media.file_url if hasattr(media, "file_url") else (media.url if hasattr(media, "url") else ""),
            "thumbnail_url": media.thumbnail_url if hasattr(media, "thumbnail_url") else None
        })
    
    return templates.TemplateResponse(
        "admin/product_form.html",
        {
            "request": request,
            "active_page": "products",
            "tenant": tenant_obj,
            "tenant_id": str(tenant_obj.id),
            "categories": categories,
            "media_files": media_list,
            "form_action": "/admin/products/add",
            "form_title": "Add New Product",
            "cart_item_count": request.session.get("cart_item_count", 0)
        }
    )

@router.post("/products/add", response_class=RedirectResponse)
async def admin_add_product(
    request: Request,
    tenant_id: str = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    sku: str = Form(...),
    stock: int = Form(0),
    categories: List[str] = Form([]),
    image_url: Optional[str] = Form(None),
    metadata: Optional[Dict[str, Any]] = Form({})
):
    """Add a new product."""
    try:
        # Create product data
        product_data = {
            "tenant_id": tenant_id,
            "name": name,
            "description": description,
            "price": price,
            "sku": sku,
            "stock": stock,
            "categories": categories,
            "image_url": image_url,
            "metadata": metadata or {}
        }
        
        # Add image URL to metadata if provided
        if image_url:
            product_data["metadata"]["image_url"] = image_url
        
        # Create product
        product = product_manager.create(product_data)
        
        return RedirectResponse(
            url="/admin/products?status_message=Product+created+successfully&status_type=success", 
            status_code=303
        )
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        error_message = f"Error creating product: {str(e)}"
        return RedirectResponse(
            url=f"/admin/products?status_message={error_message}&status_type=danger", 
            status_code=303
        )

@router.get("/products/edit/{product_id}", response_class=HTMLResponse)
async def admin_edit_product(
    request: Request,
    product_id: str
):
    """Admin form for editing a product."""
    try:
        # Get product
        product = product_manager.get(product_id)
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")
        
        # Get tenant for the product
        tenant_id = str(product.tenant_id) if hasattr(product, "tenant_id") else None
        
        if not tenant_id:
            # Try to get tenant ID from metadata
            tenant_id = product.metadata.get("tenant_id") if hasattr(product, "metadata") else None
            
        if not tenant_id:
            raise ValueError(f"Cannot determine tenant for product {product_id}")
        
        # Get tenant object
        tenant_obj = tenant_manager.get(tenant_id)
        if not tenant_obj:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        # Get categories for tenant
        categories = []
        if category_manager:
            try:
                categories = category_manager.get_by_tenant(tenant_id)
            except Exception as e:
                logger.warning(f"Error getting categories: {str(e)}")
        
        # Get media files for tenant
        media_files = []
        try:
            media_files = media_service.list_media(tenant_id=tenant_id, file_type="image")
        except Exception as e:
            logger.warning(f"Error getting media files: {str(e)}")
        
        # Format media for template
        media_list = []
        for media in media_files:
            media_list.append({
                "id": str(media.id),
                "name": media.name if hasattr(media, "name") else (media.file_name if hasattr(media, "file_name") else ""),
                "url": media.file_url if hasattr(media, "file_url") else (media.url if hasattr(media, "url") else ""),
                "thumbnail_url": media.thumbnail_url if hasattr(media, "thumbnail_url") else None
            })
        
        # Get product image URL from metadata
        image_url = None
        if hasattr(product, "metadata") and product.metadata:
            image_url = product.metadata.get("image_url")
        
        # Prepare product data for template
        product_data = {
            "id": str(product.id),
            "name": product.name,
            "description": product.description if hasattr(product, "description") else "",
            "price": product.price,
            "sku": product.sku if hasattr(product, "sku") else "",
            "stock": product.stock if hasattr(product, "stock") else 0,
            "categories": product.categories if hasattr(product, "categories") else [],
            "image_url": image_url
        }
        
        return templates.TemplateResponse(
            "admin/product_form.html",
            {
                "request": request,
                "active_page": "products",
                "tenant": tenant_obj,
                "tenant_id": tenant_id,
                "product": product_data,
                "categories": categories,
                "media_files": media_list,
                "form_action": f"/admin/products/update/{product_id}",
                "form_title": "Edit Product",
                "cart_item_count": request.session.get("cart_item_count", 0)
            }
        )
    except Exception as e:
        logger.error(f"Error editing product: {str(e)}")
        error_message = f"Error editing product: {str(e)}"
        return RedirectResponse(
            url=f"/admin/products?status_message={error_message}&status_type=danger", 
            status_code=303
        )

@router.post("/products/update/{product_id}", response_class=RedirectResponse)
async def admin_update_product(
    request: Request,
    product_id: str,
    tenant_id: str = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    sku: str = Form(...),
    stock: int = Form(0),
    categories: List[str] = Form([]),
    image_url: Optional[str] = Form(None)
):
    """Update a product."""
    try:
        # Prepare product data
        product_data = {
            "name": name,
            "description": description,
            "price": price,
            "sku": sku,
            "stock": stock,
            "categories": categories
        }
        
        # Get current product to update metadata
        current_product = product_manager.get(product_id)
        
        # Create metadata if it doesn't exist
        metadata = getattr(current_product, "metadata", {}) or {}
        
        # Update image URL in metadata
        if image_url:
            metadata["image_url"] = image_url
            
        # Set updated metadata
        product_data["metadata"] = metadata
        
        # Update product
        product = product_manager.update(product_id, **product_data)
        
        return RedirectResponse(
            url="/admin/products?status_message=Product+updated+successfully&status_type=success", 
            status_code=303
        )
    except Exception as e:
        logger.error(f"Error updating product: {str(e)}")
        error_message = f"Error updating product: {str(e)}"
        return RedirectResponse(
            url=f"/admin/products?status_message={error_message}&status_type=danger", 
            status_code=303
        )

@router.get("/products/delete/{product_id}", response_class=RedirectResponse)
async def admin_delete_product(
    request: Request,
    product_id: str
):
    """Delete a product."""
    try:
        # Delete product
        product_manager.delete(product_id)
        
        return RedirectResponse(
            url="/admin/products?status_message=Product+deleted+successfully&status_type=success", 
            status_code=303
        )
    except Exception as e:
        logger.error(f"Error deleting product: {str(e)}")
        error_message = f"Error deleting product: {str(e)}"
        return RedirectResponse(
            url=f"/admin/products?status_message={error_message}&status_type=danger", 
            status_code=303
        )

def setup_routes(app_templates):
    """
    Set up routes with the given templates.
    
    Args:
        app_templates: Jinja2Templates instance from the main app
    """
    global templates
    templates = app_templates
    return router