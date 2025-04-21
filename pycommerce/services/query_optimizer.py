"""
Query optimization service for PyCommerce.

This module provides optimized query patterns for common database operations,
using techniques like eager loading, join optimization, and result caching.
"""
import logging
import functools
import time
from typing import Dict, List, Any, Optional, Tuple, Callable, TypeVar, Union
from datetime import datetime, timedelta

from sqlalchemy import func, text
from sqlalchemy.orm import joinedload, contains_eager

from pycommerce.core.db import get_session
from pycommerce.models.order import Order, OrderItem, OrderStatus
from pycommerce.models.order_note import OrderNote
from pycommerce.models.product import Product

# Configure logger
logger = logging.getLogger(__name__)

# Type variables for generic functions
T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

# Simple in-memory cache with timeout
_cache: Dict[str, Tuple[Any, datetime]] = {}
_DEFAULT_CACHE_TIMEOUT = 300  # 5 minutes in seconds


def timed_cache(timeout: int = _DEFAULT_CACHE_TIMEOUT):
    """
    Function decorator that caches return values for a specified period.
    
    Args:
        timeout: Cache timeout in seconds
        
    Returns:
        Decorated function with caching capability
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key from function name and arguments
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Check if result is in cache and not expired
            now = datetime.now()
            if cache_key in _cache:
                result, expiry = _cache[cache_key]
                if expiry > now:
                    return result
            
            # Execute function and cache result
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log slow queries for optimization
            if execution_time > 0.5:  # Log queries taking more than 500ms
                logger.warning(f"Slow query detected: {func.__name__} took {execution_time:.2f}s")
            
            # Cache the result with expiry time
            _cache[cache_key] = (result, now + timedelta(seconds=timeout))
            return result
        return wrapper
    return decorator


def clear_cache():
    """Clear the entire query cache."""
    global _cache
    _cache = {}


def clear_cache_for_prefix(prefix: str):
    """
    Clear cache entries that start with a specific prefix.
    
    This is useful for invalidating all cached items related to a specific entity
    when that entity is modified.
    
    Args:
        prefix: The cache key prefix to match
    """
    global _cache
    keys_to_remove = [k for k in _cache.keys() if k.startswith(prefix)]
    for key in keys_to_remove:
        _cache.pop(key, None)


@timed_cache(timeout=60)  # Cache for 1 minute
def get_order_with_items_and_notes(order_id: str) -> Dict[str, Any]:
    """
    Get an order with its items and notes in a single optimized query.
    
    This function performs eager loading to reduce the number of database queries
    required to fetch an order and its related data.
    
    Args:
        order_id: The ID of the order to retrieve
        
    Returns:
        Dictionary containing the order and its related data, or an empty dict if not found
    """
    try:
        with get_session() as session:
            # Query the order with eager loading of items
            query = (
                session.query(Order)
                .options(joinedload(Order.items))
                .filter(Order.id == order_id)
            )
            
            order = query.first()
            
            if not order:
                return {}
            
            # Get notes in the same session
            notes = session.query(OrderNote).filter(
                OrderNote.order_id == order_id
            ).order_by(OrderNote.created_at.desc()).all()
            
            # Get all product IDs from items
            product_ids = [str(item.product_id) for item in order.items]
            
            # Fetch all relevant products in a single query
            products = {}
            if product_ids:
                product_query = session.query(Product).filter(
                    Product.id.in_(product_ids)
                )
                products = {str(p.id): p for p in product_query.all()}
            
            # Prepare the result with denormalized data
            result = {
                "order": {
                    "id": str(order.id),
                    "customer_name": order.customer_name,
                    "customer_email": order.customer_email,
                    "total": order.total,
                    "status": order.status.value if hasattr(order.status, 'value') else order.status,
                    "created_at": order.created_at,
                    "updated_at": order.updated_at,
                    "tenant_id": str(order.tenant_id),
                    # Include other fields as needed
                },
                "items": [],
                "notes": [],
                "items_count": len(order.items)
            }
            
            # Process items with product data
            for item in order.items:
                product = products.get(str(item.product_id))
                product_name = product.name if product else "Unknown Product"
                product_sku = product.sku if product else "N/A"
                
                result["items"].append({
                    "id": str(item.id),
                    "product_id": str(item.product_id),
                    "name": product_name,
                    "product_name": product_name,
                    "sku": product_sku,
                    "quantity": item.quantity,
                    "price": item.price,
                    "total": item.price * item.quantity,
                    "product": {
                        "id": str(item.product_id),
                        "name": product_name,
                        "sku": product_sku
                    }
                })
            
            # Process notes
            for note in notes:
                result["notes"].append({
                    "id": str(note.id),
                    "content": note.content or "",
                    "created_at": note.created_at,
                    "is_customer_note": bool(note.is_customer_note)
                })
            
            return result
            
    except Exception as e:
        logger.error(f"Error in get_order_with_items_and_notes: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {}


@timed_cache(timeout=60)
def get_orders_summary_for_tenant(tenant_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Get summarized order data for a tenant with efficient queries.
    
    This function optimizes the query for retrieving orders by:
    1. Using subqueries to count items efficiently
    2. Filtering in the database instead of in Python
    3. Only retrieving the necessary fields
    
    Args:
        tenant_id: The tenant ID to get orders for
        filters: Optional filters for status, date range, etc.
        
    Returns:
        List of order summary dictionaries
    """
    try:
        with get_session() as session:
            # Start with a base query
            query = session.query(
                Order.id,
                Order.customer_name,
                Order.customer_email,
                Order.total,
                Order.status,
                Order.created_at,
                func.count(OrderItem.id).label('items_count')
            ).outerjoin(
                OrderItem, Order.id == OrderItem.order_id
            ).filter(
                Order.tenant_id == tenant_id
            ).group_by(
                Order.id
            )
            
            # Apply filters if provided
            if filters:
                if 'status' in filters and filters['status']:
                    query = query.filter(Order.status == filters['status'])
                
                if 'date_from' in filters and filters['date_from']:
                    date_from = datetime.strptime(filters['date_from'], "%Y-%m-%d")
                    query = query.filter(Order.created_at >= date_from)
                
                if 'date_to' in filters and filters['date_to']:
                    date_to = datetime.strptime(filters['date_to'], "%Y-%m-%d")
                    # Add a day to include the entire end date
                    date_to = date_to + timedelta(days=1)
                    query = query.filter(Order.created_at < date_to)
                
                if 'customer_email' in filters and filters['customer_email']:
                    query = query.filter(Order.customer_email.ilike(f"%{filters['customer_email']}%"))
            
            # Order by created_at descending for most recent orders first
            query = query.order_by(Order.created_at.desc())
            
            # Execute the query
            results = query.all()
            
            # Process results
            orders_data = []
            for row in results:
                status_value = row.status.value if hasattr(row.status, 'value') else row.status
                
                orders_data.append({
                    "id": str(row.id),
                    "customer_name": row.customer_name or "",
                    "customer_email": row.customer_email or "",
                    "total": row.total,
                    "status": status_value,
                    "items_count": row.items_count,
                    "created_at": row.created_at
                })
            
            return orders_data
            
    except Exception as e:
        logger.error(f"Error in get_orders_summary_for_tenant: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []


@timed_cache(timeout=30)  # Shorter timeout for frequently changing data
def get_order_items_with_products(order_id: str) -> List[Dict[str, Any]]:
    """
    Get order items with product details in a single efficient query.
    
    Args:
        order_id: The order ID to get items for
        
    Returns:
        List of order items with product details
    """
    try:
        with get_session() as session:
            # Join OrderItem with Product to get product details in a single query
            items_query = (
                session.query(OrderItem, Product)
                .outerjoin(Product, OrderItem.product_id == Product.id)
                .filter(OrderItem.order_id == order_id)
            )
            
            results = items_query.all()
            
            items_data = []
            for item, product in results:
                product_name = product.name if product else "Unknown Product"
                product_sku = product.sku if product else "N/A"
                
                items_data.append({
                    "id": str(item.id),
                    "product_id": str(item.product_id),
                    "name": product_name,
                    "product_name": product_name,
                    "sku": product_sku,
                    "quantity": item.quantity,
                    "price": item.price,
                    "total": item.price * item.quantity,
                    "product": {
                        "id": str(item.product_id),
                        "name": product_name,
                        "sku": product_sku
                    } if product else None
                })
            
            return items_data
            
    except Exception as e:
        logger.error(f"Error in get_order_items_with_products: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []


def invalidate_order_cache(order_id: str):
    """
    Invalidate all cached data related to a specific order.
    
    Call this function whenever an order is updated.
    
    Args:
        order_id: The order ID that was modified
    """
    clear_cache_for_prefix(f"get_order_with_items_and_notes:{order_id}")
    clear_cache_for_prefix(f"get_order_items_with_products:{order_id}")


def invalidate_tenant_orders_cache(tenant_id: str):
    """
    Invalidate all cached order data for a tenant.
    
    Call this function whenever orders for a tenant are created or updated.
    
    Args:
        tenant_id: The tenant ID whose orders were modified
    """
    clear_cache_for_prefix(f"get_orders_summary_for_tenant:{tenant_id}")