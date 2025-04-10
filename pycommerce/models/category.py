"""
Category management module for PyCommerce.

This module provides the CategoryManager class for managing product categories.
"""
import logging
import uuid
from typing import List, Optional, Dict, Any, Union
from functools import wraps

# Configure logging
logger = logging.getLogger(__name__)

# Import models dynamically to avoid circular imports
# These will be properly imported in the ensure_app_context wrapper
db = None
Category = None
ProductCategory = None
Product = None
Tenant = None

def get_db_session():
    """
    Get a database session that works in both Flask and FastAPI environments.
    
    This function handles importing the necessary models and creating a session
    regardless of which web framework is being used.
    
    Returns:
        tuple: (db, Category, ProductCategory, Product, Tenant) - database and model classes
    """
    global db, Category, ProductCategory, Product, Tenant
    
    # Make sure models are imported
    if db is None or Category is None:
        try:
            from models import db, Category, ProductCategory, Product, Tenant
        except ImportError:
            logger.error("Failed to import models")
            return None, None, None, None, None
    
    # Check if db already has a session (Flask environment)
    if hasattr(db, 'session') and db.session is not None:
        return db, Category, ProductCategory, Product, Tenant
    
    # For FastAPI, create a standalone session
    try:
        from sqlalchemy.orm import sessionmaker, scoped_session
        from sqlalchemy import create_engine
        import os
        
        # Create engine and session
        if not hasattr(db, 'engine'):
            db.engine = create_engine(os.environ.get("DATABASE_URL"))
        
        if not hasattr(db, 'session') or db.session is None:
            session_factory = sessionmaker(bind=db.engine)
            db.session = scoped_session(session_factory)
            logger.info("Created standalone SQLAlchemy session for FastAPI")
        
        return db, Category, ProductCategory, Product, Tenant
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        return None, None, None, None, None


def ensure_db_session(func):
    """
    Decorator to ensure a database session is available.
    Works with both Flask and FastAPI environments.
    
    Args:
        func: The function to wrap
        
    Returns:
        Wrapped function that ensures database access
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Import global variables and get DB session
        db, Category, ProductCategory, Product, Tenant = get_db_session()
        
        if db is None:
            logger.error("Failed to get database session")
            return None
            
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in database operation: {e}")
            # Try to rollback if there was a transaction
            try:
                db.session.rollback()
            except:
                pass
            return None
    
    return wrapper

class CategoryManager:
    """Manager class for category operations."""

    def __init__(self):
        """Initialize the CategoryManager."""
        logger.info("CategoryManager initialized")

    def get_all_categories(self, tenant_id: str, include_inactive: bool = False) -> List:
        """
        Get all categories for a tenant.
        
        Args:
            tenant_id: The tenant ID
            include_inactive: Whether to include inactive categories
            
        Returns:
            List of Category objects
        """
        @ensure_db_session
        def _get_all_categories(tenant_id, include_inactive):
            query = Category.query.filter_by(tenant_id=tenant_id)
            
            if not include_inactive:
                query = query.filter_by(active=True)
                
            return query.all()
        
        return _get_all_categories(tenant_id, include_inactive)
    
    def get_category(self, category_id: str) -> Optional:
        """
        Get a category by ID.
        
        Args:
            category_id: The category ID
            
        Returns:
            Category object or None if not found
        """
        @ensure_db_session
        def _get_category(category_id):
            return Category.query.get(category_id)
        
        return _get_category(category_id)
    
    def get_category_by_slug(self, tenant_id: str, slug: str) -> Optional:
        """
        Get a category by slug for a tenant.
        
        Args:
            tenant_id: The tenant ID
            slug: The category slug
            
        Returns:
            Category object or None if not found
        """
        @ensure_db_session
        def _get_category_by_slug(tenant_id, slug):
            return Category.query.filter_by(tenant_id=tenant_id, slug=slug).first()
        
        return _get_category_by_slug(tenant_id, slug)
    
    def create_category(self, tenant_id: str, name: str, slug: str, 
                        description: Optional[str] = None, 
                        parent_id: Optional[str] = None,
                        active: bool = True):
        """
        Create a new category.
        
        Args:
            tenant_id: The tenant ID
            name: The category name
            slug: The category slug
            description: Optional category description
            parent_id: Optional parent category ID
            active: Whether the category is active
            
        Returns:
            The newly created Category object
        """
        # Check if a category with the same slug already exists
        existing = self.get_category_by_slug(tenant_id, slug)
        if existing:
            raise ValueError(f"Category with slug '{slug}' already exists for this tenant")
        
        @ensure_db_session
        def _create_category(tenant_id, name, slug, description, parent_id, active):
            # Create new category
            category = Category(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                name=name,
                slug=slug,
                description=description,
                parent_id=parent_id,
                active=active
            )
            
            # Add to database
            db.session.add(category)
            db.session.commit()
            
            return category
        
        return _create_category(tenant_id, name, slug, description, parent_id, active)
    
    def update_category(self, category_id: str, **kwargs):
        """
        Update a category.
        
        Args:
            category_id: The category ID
            **kwargs: Fields to update (name, slug, description, parent_id, active)
            
        Returns:
            The updated Category object or None if not found
        """
        category = self.get_category(category_id)
        if not category:
            logger.warning(f"Category with ID {category_id} not found")
            return None
        
        @ensure_db_session
        def _update_category(category, kwargs, category_id):
            # Update allowed fields
            allowed_fields = ["name", "slug", "description", "parent_id", "active"]
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(category, field, value)
            
            # If slug is being updated, check for duplicates
            if "slug" in kwargs:
                existing = Category.query.filter_by(
                    tenant_id=category.tenant_id, 
                    slug=kwargs["slug"]
                ).first()
                
                if existing and existing.id != category_id:
                    raise ValueError(f"Category with slug '{kwargs['slug']}' already exists for this tenant")
            
            db.session.commit()
            return category
        
        return _update_category(category, kwargs, category_id)
    
    def delete_category(self, category_id: str) -> bool:
        """
        Delete a category.
        
        Args:
            category_id: The category ID
            
        Returns:
            True if successful, False otherwise
        """
        category = self.get_category(category_id)
        if not category:
            logger.warning(f"Category with ID {category_id} not found")
            return False
        
        @ensure_db_session
        def _delete_category(category_id, category):
            # Check if category has subcategories
            subcategories = Category.query.filter_by(parent_id=category_id).count()
            if subcategories > 0:
                logger.warning(f"Cannot delete category {category_id} as it has {subcategories} subcategories")
                return False
            
            # Remove product associations
            ProductCategory.query.filter_by(category_id=category_id).delete()
            
            # Delete the category
            db.session.delete(category)
            db.session.commit()
            
            return True
            
        return _delete_category(category_id, category)
    
    def get_category_tree(self, tenant_id: str, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """
        Get a hierarchical category tree for a tenant.
        
        Args:
            tenant_id: The tenant ID
            include_inactive: Whether to include inactive categories
            
        Returns:
            List of category dictionaries with nested 'children' lists
        """
        # Get all categories for the tenant
        categories = self.get_all_categories(tenant_id, include_inactive)
        
        # Create a dict of id -> category
        category_dict = {cat.id: {
            "id": cat.id,
            "name": cat.name,
            "slug": cat.slug,
            "description": cat.description,
            "active": cat.active,
            "parent_id": cat.parent_id,
            "children": []
        } for cat in categories}
        
        # Build the tree structure
        root_categories = []
        for cat_id, cat_data in category_dict.items():
            if cat_data["parent_id"] is None:
                # This is a root category
                root_categories.append(cat_data)
            else:
                # This is a child category
                parent_id = cat_data["parent_id"]
                if parent_id in category_dict:  # Make sure parent exists
                    category_dict[parent_id]["children"].append(cat_data)
        
        return root_categories
    
    def get_products_in_category(self, category_id: str, include_subcategories: bool = True) -> List[Product]:
        """
        Get all products in a category.
        
        Args:
            category_id: The category ID
            include_subcategories: Whether to include products from subcategories
            
        Returns:
            List of Product objects
        """
        category = self.get_category(category_id)
        if not category:
            logger.warning(f"Category with ID {category_id} not found")
            return []
        
        # Get direct products in this category
        products = category.products
        
        # If including subcategories, add those products too
        if include_subcategories:
            subcategories = Category.query.filter_by(parent_id=category_id).all()
            for subcat in subcategories:
                # Recursive call to get products from this subcategory and its children
                sub_products = self.get_products_in_category(subcat.id, include_subcategories)
                products.extend(sub_products)
        
        return products
    
    def assign_product_to_category(self, product_id: str, category_id: str) -> bool:
        """
        Assign a product to a category.
        
        Args:
            product_id: The product ID
            category_id: The category ID
            
        Returns:
            True if successful, False otherwise
        """
        @ensure_db_session
        def _get_product_and_category(product_id, category_id):
            # Check if product and category exist
            product = Product.query.get(product_id)
            category = Category.query.get(category_id)
            return product, category
            
        product, category = _get_product_and_category(product_id, category_id)
        
        if not product or not category:
            logger.warning(f"Product {product_id} or category {category_id} not found")
            return False
        
        # Check if they belong to the same tenant
        if product.tenant_id != category.tenant_id:
            logger.warning(f"Product {product_id} and category {category_id} belong to different tenants")
            return False
        
        @ensure_db_session
        def _assign_product_to_category(product_id, category_id, product, category):
            # Check if the association already exists
            association = ProductCategory.query.filter_by(
                product_id=product_id, 
                category_id=category_id
            ).first()
            
            if association:
                logger.info(f"Product {product_id} is already assigned to category {category_id}")
                return True
            
            # Create the association
            association = ProductCategory(
                product_id=product_id,
                category_id=category_id
            )
            db.session.add(association)
            
            # Update the legacy categories JSON field for backward compatibility
            if category.name not in product.categories:
                current_categories = product.categories or []
                current_categories.append(category.name)
                product.categories = current_categories
            
            db.session.commit()
            return True
            
        return _assign_product_to_category(product_id, category_id, product, category)
    
    def remove_product_from_category(self, product_id: str, category_id: str) -> bool:
        """
        Remove a product from a category.
        
        Args:
            product_id: The product ID
            category_id: The category ID
            
        Returns:
            True if successful, False otherwise
        """
        @ensure_db_session
        def _check_and_remove_association(product_id, category_id):
            # Check if the association exists
            association = ProductCategory.query.filter_by(
                product_id=product_id, 
                category_id=category_id
            ).first()
            
            if not association:
                logger.warning(f"Product {product_id} is not assigned to category {category_id}")
                return False, None, None
            
            # Get product and category
            product = Product.query.get(product_id)
            category = Category.query.get(category_id)
            
            # Delete the association
            db.session.delete(association)
            
            # Update the legacy categories JSON field for backward compatibility
            if product and category and category.name in product.categories:
                current_categories = product.categories or []
                current_categories.remove(category.name)
                product.categories = current_categories
            
            db.session.commit()
            return True, product, category
        
        success, product, category = _check_and_remove_association(product_id, category_id)
        return success
    
    def sync_product_categories(self, product_id: str, category_ids: List[str]) -> bool:
        """
        Sync a product's categories to match the provided list.
        
        Args:
            product_id: The product ID
            category_ids: List of category IDs to assign to the product
            
        Returns:
            True if successful, False otherwise
        """
        @ensure_db_session
        def _get_product_and_associations(product_id):
            product = Product.query.get(product_id)
            if not product:
                return None, []
                
            # Get current category associations
            current_associations = ProductCategory.query.filter_by(product_id=product_id).all()
            current_category_ids = [assoc.category_id for assoc in current_associations]
            return product, current_category_ids
            
        product, current_category_ids = _get_product_and_associations(product_id)
        if not product:
            logger.warning(f"Product {product_id} not found")
            return False
        
        # Determine categories to add and remove
        categories_to_add = [cat_id for cat_id in category_ids if cat_id not in current_category_ids]
        categories_to_remove = [cat_id for cat_id in current_category_ids if cat_id not in category_ids]
        
        # Add new associations
        for cat_id in categories_to_add:
            self.assign_product_to_category(product_id, cat_id)
        
        # Remove old associations
        for cat_id in categories_to_remove:
            self.remove_product_from_category(product_id, cat_id)
        
        return True
    
    def migrate_from_json_categories(self, tenant_id: str) -> Dict[str, int]:
        """
        Migrate products from using JSON categories to proper category relationships.
        
        Args:
            tenant_id: The tenant ID to migrate
            
        Returns:
            Dictionary with metrics about the migration
        """
        stats = {
            "products_processed": 0,
            "categories_created": 0,
            "associations_created": 0,
            "errors": 0
        }
        
        @ensure_db_session
        def _get_products_for_tenant(tenant_id):
            # Get all products for this tenant
            return Product.query.filter_by(tenant_id=tenant_id).all()
        
        products = _get_products_for_tenant(tenant_id)
        
        for product in products:
            stats["products_processed"] += 1
            
            # Skip products with no categories
            if not product.categories:
                continue
            
            for category_name in product.categories:
                # Skip empty category names
                if not category_name:
                    continue
                
                # Create a slug from the name
                slug = category_name.lower().replace(' ', '-')
                
                # Check if category exists
                category = self.get_category_by_slug(tenant_id, slug)
                
                # Create category if it doesn't exist
                if not category:
                    try:
                        category = self.create_category(
                            tenant_id=tenant_id,
                            name=category_name,
                            slug=slug
                        )
                        stats["categories_created"] += 1
                    except Exception as e:
                        logger.error(f"Error creating category {category_name}: {e}")
                        stats["errors"] += 1
                        continue
                
                # Create association
                try:
                    success = self.assign_product_to_category(product.id, category.id)
                    if success:
                        stats["associations_created"] += 1
                except Exception as e:
                    logger.error(f"Error assigning product {product.id} to category {category.id}: {e}")
                    stats["errors"] += 1
        
        return stats