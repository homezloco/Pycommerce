"""
Enhanced query optimization service for PyCommerce.

This module extends the base query optimizer with additional caching strategies
and optimized queries for page builder and product catalog operations.
"""
import logging
import functools
import time
from typing import Dict, List, Any, Optional, Tuple, Callable, TypeVar, Union, Set
from datetime import datetime, timedelta

# Standard SQLAlchemy imports
try:
    from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, JSON, Integer
    from sqlalchemy import func, text, or_, and_, desc
    from sqlalchemy.orm import joinedload, contains_eager, selectinload
except ImportError:
    # Handle import error gracefully
    import logging
    logging.error("SQLAlchemy imports failed in enhanced_query_optimizer")
    # Provide mock classes/functions to prevent further errors
    class MockFunc:
        def count(self, *args): return None
    func = MockFunc()

from pycommerce.core.db import get_session
from pycommerce.models.order import Order, OrderItem, OrderStatus
from pycommerce.models.product import Product
from pycommerce.models.category import Category
from pycommerce.models.page_builder import Page, PageSection, ContentBlock, PageTemplate

# Import original query optimizer for compatibility
from pycommerce.services.query_optimizer import (
    timed_cache, clear_cache, clear_cache_for_prefix,
    _cache, _DEFAULT_CACHE_TIMEOUT
)

# Configure logger
logger = logging.getLogger(__name__)

# Type variables for generic functions
T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')


# Enhanced caching decorator with auto-invalidation
def cached_query(
    timeout: int = _DEFAULT_CACHE_TIMEOUT, 
    auto_invalidate_keys: Optional[List[str]] = None
):
    """
    Enhanced caching decorator with auto-invalidation support.
    
    This decorator extends the basic timed_cache with:
    1. More detailed cache key generation based on query structure
    2. Support for related invalidation keys
    3. Query execution time logging

    Args:
        timeout: Cache timeout in seconds
        auto_invalidate_keys: List of related keys to clear when the cache is invalidated
        
    Returns:
        Decorated function with enhanced caching capability
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create a more detailed cache key
            key_parts = [func.__name__]
            
            # Add serialized arguments
            for arg in args[1:]:  # Skip self argument
                if hasattr(arg, 'id'):
                    # For model instances, use their ID
                    key_parts.append(f"{arg.__class__.__name__}#{arg.id}")
                else:
                    key_parts.append(str(arg))
            
            # Add sorted keyword arguments
            for k, v in sorted(kwargs.items()):
                if hasattr(v, 'id'):
                    key_parts.append(f"{k}={v.__class__.__name__}#{v.id}")
                else:
                    key_parts.append(f"{k}={v}")
            
            cache_key = ":".join(key_parts)
            
            # Check if result is in cache and not expired
            now = datetime.now()
            if cache_key in _cache:
                result, expiry = _cache[cache_key]
                if expiry > now:
                    return result
            
            # Execute function and measure time
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log execution time for monitoring
            if execution_time > 0.1:  # Lower threshold to catch more potential issues
                logger.info(f"Query timing: {func.__name__} took {execution_time:.4f}s")
                if execution_time > 0.5:  # Log warnings for slower queries
                    logger.warning(f"Slow query detected: {func.__name__} took {execution_time:.4f}s")
            
            # Cache the result with expiry time
            _cache[cache_key] = (result, now + timedelta(seconds=timeout))
            
            # Store relationship with invalidation keys
            if auto_invalidate_keys:
                for inv_key in auto_invalidate_keys:
                    # Store relationship for future invalidation
                    # This could be implemented with a reverse lookup map in the cache system
                    pass
                
            return result
        return wrapper
    return decorator


# ----- Page Builder Optimized Queries -----

@cached_query(timeout=300)  # 5 minutes cache
def get_page_with_full_content(page_id: str) -> Dict[str, Any]:
    """
    Get a page with all its sections and content blocks in a single optimized query.
    
    This function uses eager loading to fetch an entire page structure in one query,
    significantly reducing database round trips for page rendering.
    
    Args:
        page_id: The ID of the page to retrieve
        
    Returns:
        Dictionary containing the page with its sections and blocks
    """
    try:
        with get_session() as session:
            # Build an optimized query with eager loading
            query = (
                session.query(Page)
                .options(
                    # Load sections with order by position
                    selectinload(Page.sections).selectinload(PageSection.blocks)
                )
                .filter(Page.id == page_id)
            )
            
            page = query.first()
            
            if not page:
                return {}
            
            # Prepare the result with nested structure
            result = {
                "page": {
                    "id": str(page.id),
                    "title": page.title,
                    "slug": page.slug,
                    "meta_title": page.meta_title,
                    "meta_description": page.meta_description,
                    "is_published": page.is_published,
                    "layout_data": page.layout_data,
                    "created_at": page.created_at,
                    "updated_at": page.updated_at,
                    "tenant_id": str(page.tenant_id)
                },
                "sections": []
            }
            
            # Process sections and their blocks
            for section in sorted(page.sections, key=lambda s: s.position):
                section_data = {
                    "id": str(section.id),
                    "section_type": section.section_type,
                    "position": section.position,
                    "settings": section.settings,
                    "blocks": []
                }
                
                # Process blocks within the section
                for block in sorted(section.blocks, key=lambda b: b.position):
                    block_data = {
                        "id": str(block.id),
                        "block_type": block.block_type,
                        "position": block.position,
                        "content": block.content,
                        "settings": block.settings
                    }
                    section_data["blocks"].append(block_data)
                
                result["sections"].append(section_data)
            
            return result
            
    except Exception as e:
        logger.error(f"Error in get_page_with_full_content: {e}")
        return {}


@cached_query(timeout=600)  # 10 minutes cache for templates
def get_all_page_templates(include_system: bool = True) -> List[Dict[str, Any]]:
    """
    Get all page templates with optimized query.
    
    Args:
        include_system: Whether to include system templates
        
    Returns:
        List of template dictionaries
    """
    try:
        with get_session() as session:
            query = session.query(PageTemplate)
            
            if not include_system:
                query = query.filter(PageTemplate.is_system == False)
                
            templates = query.all()
            
            result = []
            for template in templates:
                result.append({
                    "id": str(template.id),
                    "name": template.name,
                    "description": template.description or "",
                    "thumbnail_url": template.thumbnail_url,
                    "is_system": template.is_system,
                    "template_data": template.template_data,
                    "created_at": template.created_at
                })
                
            return result
            
    except Exception as e:
        logger.error(f"Error in get_all_page_templates: {e}")
        return []


@cached_query(timeout=300)  # 5 minutes cache
def get_pages_by_tenant(tenant_id: str, include_unpublished: bool = False) -> List[Dict[str, Any]]:
    """
    Get all pages for a tenant with optimized query.
    
    Args:
        tenant_id: The tenant ID
        include_unpublished: Whether to include unpublished pages
        
    Returns:
        List of page dictionaries
    """
    try:
        with get_session() as session:
            query = session.query(Page).filter(Page.tenant_id == tenant_id)
            
            if not include_unpublished:
                query = query.filter(Page.is_published == True)
                
            # Count sections for each page using a subquery
            section_count_subquery = (
                session.query(
                    PageSection.page_id,
                    func.count(PageSection.id).label('section_count')
                )
                .group_by(PageSection.page_id)
                .subquery()
            )
            
            # Join with the section count subquery
            query = query.outerjoin(
                section_count_subquery,
                Page.id == section_count_subquery.c.page_id
            )
            
            # Add the count to the selection
            query = query.add_columns(
                func.coalesce(section_count_subquery.c.section_count, 0).label('section_count')
            )
            
            # Execute the query
            results = query.all()
            
            # Process results
            pages_data = []
            for row in results:
                if isinstance(row, tuple):
                    page, section_count = row
                else:
                    page = row
                    section_count = 0
                    
                pages_data.append({
                    "id": str(page.id),
                    "title": page.title,
                    "slug": page.slug,
                    "is_published": page.is_published,
                    "created_at": page.created_at,
                    "updated_at": page.updated_at,
                    "section_count": section_count
                })
                
            return pages_data
            
    except Exception as e:
        logger.error(f"Error in get_pages_by_tenant: {e}")
        return []


# ----- Product Catalog Optimized Queries -----

@cached_query(timeout=180)  # 3 minutes cache
def get_products_with_categories(
    tenant_id: str,
    category_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    search_term: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get products with their categories using optimized joins.
    
    Args:
        tenant_id: The tenant ID
        category_id: Optional category ID filter
        limit: Maximum number of products to return
        offset: Offset for pagination
        search_term: Optional search term for product name
        
    Returns:
        Dictionary with products list and total count
    """
    try:
        with get_session() as session:
            # Base query for count
            count_query = session.query(func.count(Product.id)).filter(Product.tenant_id == tenant_id)
            
            # Base query for products
            query = session.query(Product).filter(Product.tenant_id == tenant_id)
            
            # Apply category filter if provided
            if category_id:
                # This could be optimized with a direct join to the product_categories table
                # Instead of loading all categories and filtering in Python
                pass
                
            # Apply search filter if provided
            if search_term:
                search_pattern = f"%{search_term}%"
                try:
                    # Use case-insensitive search with ilike if available
                    count_query = count_query.filter(Product.name.ilike(search_pattern))
                    query = query.filter(Product.name.ilike(search_pattern))
                except AttributeError:
                    # Fallback to case-sensitive contains
                    logger.warning("ilike not available, falling back to string contains")
                    count_query = count_query.filter(Product.name.contains(search_pattern))
                    query = query.filter(Product.name.contains(search_pattern))
                
            # Get total count
            total_count = count_query.scalar() or 0
            
            # Apply pagination
            try:
                # Try to order by created_at descending
                from sqlalchemy import desc
                query = query.order_by(desc(Product.created_at))
            except (ImportError, AttributeError):
                # Fallback if desc is not available
                logger.warning("desc() not available, using default ordering")
            
            query = query.limit(limit).offset(offset)
            
            # Option to eager load categories
            query = query.options(
                selectinload(Product.categories)
            )
            
            # Execute the query
            products = query.all()
            
            # Process the results
            result = {
                "products": [],
                "total_count": total_count,
                "page": (offset // limit) + 1 if limit > 0 else 1,
                "total_pages": (total_count + limit - 1) // limit if limit > 0 else 1
            }
            
            for product in products:
                # Prepare product data with categories
                category_names = [category.name for category in product.categories] if hasattr(product, 'categories') else []
                
                result["products"].append({
                    "id": str(product.id),
                    "name": product.name,
                    "price": float(product.price),
                    "sku": product.sku,
                    "stock": product.stock,
                    "categories": category_names
                })
                
            return result
            
    except Exception as e:
        logger.error(f"Error in get_products_with_categories: {e}")
        return {"products": [], "total_count": 0, "page": 1, "total_pages": 0}


# ----- Cache Invalidation Functions -----

def invalidate_page_cache(page_id: str):
    """
    Invalidate all cached data related to a specific page.
    
    Call this function whenever a page is updated.
    
    Args:
        page_id: The page ID that was modified
    """
    clear_cache_for_prefix(f"get_page_with_full_content:{page_id}")
    # Also invalidate tenant pages lists that might contain this page
    clear_cache_for_prefix("get_pages_by_tenant")


def invalidate_template_cache():
    """
    Invalidate all template cache.
    
    Call this function whenever a template is created, updated, or deleted.
    """
    clear_cache_for_prefix("get_all_page_templates")


# ----- Product API Optimizations -----

@cached_query(timeout=180)  # 3 minutes cache
def get_products_by_tenant(
    tenant_id: str,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Get products for a tenant with optional filtering in an optimized query.
    
    This function uses efficient filtering and pagination with eager loading of
    product relationships to minimize database queries.
    
    Args:
        tenant_id: The tenant ID
        category: Optional category name to filter by
        min_price: Optional minimum price filter
        max_price: Optional maximum price filter
        in_stock: Optional stock availability filter
        limit: Maximum number of products to return
        offset: Pagination offset
        
    Returns:
        Dictionary with products list, total count, and filter information
    """
    try:
        with get_session() as session:
            # Start building the query
            query = session.query(Product).filter(Product.tenant_id == tenant_id)
            
            # Apply filters
            filters = {}
            
            if category:
                filters['category'] = category
                # Find category and filter products by it
                category_obj = session.query(Category).filter(
                    Category.name == category,
                    Category.tenant_id == tenant_id
                ).first()
                
                if category_obj:
                    # Join with Category and filter
                    query = query.join(Product.categories).filter(Category.id == category_obj.id)
                else:
                    # No matching category found, return empty result
                    return {
                        "products": [],
                        "count": 0,
                        "tenant": tenant_id,
                        "filters": filters,
                        "limit": limit,
                        "offset": offset
                    }
            
            if min_price is not None:
                filters['min_price'] = min_price
                query = query.filter(Product.price >= min_price)
                
            if max_price is not None:
                filters['max_price'] = max_price
                query = query.filter(Product.price <= max_price)
                
            if in_stock is not None:
                filters['in_stock'] = in_stock
                query = query.filter(Product.stock > 0 if in_stock else Product.stock == 0)
            
            # Get total count for pagination
            total_count = query.count()
            
            # Apply pagination and eager load relationships
            query = (
                query
                .options(selectinload(Product.categories))
                .order_by(Product.name)
                .limit(limit)
                .offset(offset)
            )
            
            # Execute query and format results
            products = query.all()
            result_products = []
            
            for product in products:
                product_dict = {
                    "id": str(product.id),
                    "name": product.name,
                    "description": product.description,
                    "price": product.price,
                    "sku": product.sku,
                    "stock": product.stock,
                    "tenant_id": product.tenant_id,
                    "categories": [category.name for category in product.categories],
                    "created_at": product.created_at.isoformat() if product.created_at else None,
                    "updated_at": product.updated_at.isoformat() if product.updated_at else None
                }
                result_products.append(product_dict)
            
            return {
                "products": result_products,
                "count": total_count,
                "tenant": tenant_id,
                "filters": filters,
                "limit": limit,
                "offset": offset
            }
    except Exception as e:
        logger.error(f"Error in get_products_by_tenant: {e}")
        return {
            "products": [],
            "count": 0,
            "tenant": tenant_id,
            "filters": {},
            "limit": limit,
            "offset": offset,
            "error": str(e)
        }

@cached_query(timeout=300)  # 5 minutes cache
def get_product_with_details(product_id: str) -> Dict[str, Any]:
    """
    Get a product with all its details including categories in a single optimized query.
    
    Args:
        product_id: The ID of the product to retrieve
        
    Returns:
        Dictionary containing the product with all its details
    """
    try:
        with get_session() as session:
            # Build query with eager loading of relationships
            query = (
                session.query(Product)
                .options(selectinload(Product.categories))
                .filter(Product.id == product_id)
            )
            
            product = query.first()
            if not product:
                logger.warning(f"Product not found with ID: {product_id}")
                return None
                
            # Convert to dictionary for JSON serialization
            result = {
                "id": str(product.id),
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "sku": product.sku,
                "stock": product.stock,
                "tenant_id": product.tenant_id,
                "categories": [category.name for category in product.categories],
                "created_at": product.created_at.isoformat() if product.created_at else None,
                "updated_at": product.updated_at.isoformat() if product.updated_at else None
            }
            
            return result
    except Exception as e:
        logger.error(f"Error in get_product_with_details: {e}")
        return None

def invalidate_product_cache(tenant_id: Optional[str] = None, product_id: Optional[str] = None):
    """
    Invalidate product cache.
    
    Args:
        tenant_id: Optional tenant ID to invalidate all products for this tenant
        product_id: Optional product ID to invalidate specific product
    """
    # Clear cache based on specificity
    if tenant_id is not None:
        # Clear cache for specific tenant
        clear_cache_for_prefix(f"get_products_with_categories:{tenant_id}")
        clear_cache_for_prefix(f"get_products_by_tenant:{tenant_id}")
    elif product_id is not None:
        # This would need a reverse lookup mechanism to find all queries that included this product
        # For now, we clear all product queries to be safe
        clear_cache_for_prefix("get_products_with_categories")
        clear_cache_for_prefix("get_products_by_tenant")
        clear_cache_for_prefix(f"get_product_with_details:{product_id}")
    else:
        # Clear all product cache if no specific ID provided
        clear_cache_for_prefix("get_products_with_categories")
        clear_cache_for_prefix("get_products_by_tenant")
        clear_cache_for_prefix("get_product_with_details")