"""
Category management module for PyCommerce.

This module provides the CategoryManager class for managing product categories.
Following the same pattern as other managers in the system for consistency.
"""
import logging
import uuid
from typing import List, Optional, Dict, Any, Union, TypeVar, cast
import sys
import importlib

# Configure logging
logger = logging.getLogger(__name__)

# Define a generic type for category objects
T = TypeVar('T')

# Import models - we do this at module level like other managers
try:
    from models import db, Category, ProductCategory, Product, Tenant
except ImportError:
    logger.error("Failed to import models in CategoryManager module")
    db = None
    Category = None
    ProductCategory = None
    Product = None
    Tenant = None

# Import Flask app to use app_context
flask_app = None
try:
    # Dynamically find the Flask app from common module locations
    for module_name in ["web_app", "main", "app", "flask_app", "main_flask"]:
        try:
            if module_name in sys.modules:
                module = sys.modules[module_name]
            else:
                module = importlib.import_module(module_name)
                
            if hasattr(module, "app"):
                flask_app = getattr(module, "app")
                if hasattr(flask_app, 'app_context'):
                    logger.info(f"Found Flask app in module {module_name}")
                    break
        except (ImportError, AttributeError):
            continue
        except Exception as e:
            logger.warning(f"Error importing module {module_name}: {e}")
except Exception as e:
    logger.warning(f"Error finding Flask app: {e}")


class CategoryManager:
    """Manager class for category operations."""

    def __init__(self):
        """Initialize the CategoryManager."""
        logger.info("CategoryManager initialized")

    def get_all_categories(self, tenant_id: str, include_inactive: bool = False) -> List[Any]:
        """
        Get all categories for a tenant.
        
        Args:
            tenant_id: The tenant ID
            include_inactive: Whether to include inactive categories
            
        Returns:
            List of Category objects
        """
        # Use Flask's app_context if available
        if flask_app is not None and hasattr(flask_app, 'app_context'):
            with flask_app.app_context():
                return self._get_all_categories(tenant_id, include_inactive)
        else:
            # Fallback if we can't find a Flask app
            return self._get_all_categories(tenant_id, include_inactive)
            
    def _get_all_categories(self, tenant_id: str, include_inactive: bool = False) -> List[Any]:
        """Internal implementation of get_all_categories."""
        try:
            # Use eager loading when available
            try:
                from sqlalchemy.orm import joinedload
                query = Category.query.options(joinedload(Category.products))
            except (ImportError, AttributeError):
                query = Category.query
                
            # Filter by tenant
            query = query.filter_by(tenant_id=tenant_id)
            
            # Filter by active status if needed
            if not include_inactive:
                query = query.filter_by(active=True)
                
            # Get all categories
            categories = query.all()
            
            return categories
        except Exception as e:
            logger.error(f"Error in get_all_categories: {e}")
            return []

    def get_category(self, category_id: str) -> Optional[T]:
        """
        Get a category by ID.
        
        Args:
            category_id: The category ID
            
        Returns:
            Category object or None if not found
        """
        # Use Flask's app_context if available
        if flask_app is not None and hasattr(flask_app, 'app_context'):
            with flask_app.app_context():
                return self._get_category(category_id)
        else:
            # Fallback if we can't find a Flask app
            return self._get_category(category_id)
            
    def _get_category(self, category_id: str) -> Optional[T]:
        """Internal implementation of get_category."""
        try:
            # Use eager loading when available
            try:
                from sqlalchemy.orm import joinedload
                category = Category.query.options(joinedload(Category.products)).get(category_id)
            except (ImportError, AttributeError):
                category = Category.query.get(category_id)
                
            return category
        except Exception as e:
            logger.error(f"Error in get_category: {e}")
            return None

    def get_category_by_slug(self, tenant_id: str, slug: str) -> Optional[T]:
        """
        Get a category by slug for a tenant.
        
        Args:
            tenant_id: The tenant ID
            slug: The category slug
            
        Returns:
            Category object or None if not found
        """
        # Use Flask's app_context if available
        if flask_app is not None and hasattr(flask_app, 'app_context'):
            with flask_app.app_context():
                return self._get_category_by_slug(tenant_id, slug)
        else:
            # Fallback if we can't find a Flask app
            return self._get_category_by_slug(tenant_id, slug)
            
    def _get_category_by_slug(self, tenant_id: str, slug: str) -> Optional[T]:
        """Internal implementation of get_category_by_slug."""
        try:
            return Category.query.filter_by(tenant_id=tenant_id, slug=slug).first()
        except Exception as e:
            logger.error(f"Error in get_category_by_slug: {e}")
            return None

    def create_category(self, tenant_id: str, name: str, slug: str, 
                        description: Optional[str] = None, 
                        parent_id: Optional[str] = None,
                        active: bool = True) -> Optional[T]:
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
        
        # Use Flask's app_context if available
        if flask_app is not None and hasattr(flask_app, 'app_context'):
            with flask_app.app_context():
                return self._create_category(tenant_id, name, slug, description, parent_id, active)
        else:
            # Fallback if we can't find a Flask app
            return self._create_category(tenant_id, name, slug, description, parent_id, active)
    
    def _create_category(self, tenant_id: str, name: str, slug: str, 
                        description: Optional[str] = None, 
                        parent_id: Optional[str] = None,
                        active: bool = True) -> Optional[T]:
        """Internal implementation of create_category."""
        try:
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
        except Exception as e:
            logger.error(f"Error in create_category: {e}")
            if db is not None and hasattr(db, 'session'):
                db.session.rollback()
            return None

    def update_category(self, category_id: str, **kwargs) -> Optional[T]:
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
        
        try:
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
        except Exception as e:
            logger.error(f"Error in update_category: {e}")
            if db is not None and hasattr(db, 'session'):
                db.session.rollback()
            return None

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
        
        try:
            # Check if category has subcategories
            subcategories = Category.query.filter_by(parent_id=category_id).first()
            if subcategories:
                logger.warning(f"Cannot delete category {category_id} because it has subcategories")
                return False
            
            # Check for product associations
            associations = ProductCategory.query.filter_by(category_id=category_id).all()
            for assoc in associations:
                db.session.delete(assoc)
            
            # Delete the category
            db.session.delete(category)
            db.session.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error in delete_category: {e}")
            if db is not None and hasattr(db, 'session'):
                db.session.rollback()
            return False

    def get_category_tree(self, tenant_id: str, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """
        Get a hierarchical category tree for a tenant.
        
        Args:
            tenant_id: The tenant ID
            include_inactive: Whether to include inactive categories
            
        Returns:
            List of category dictionaries with nested 'children' lists
        """
        categories = self.get_all_categories(tenant_id, include_inactive)
        
        # Create lookup dictionaries
        category_dict = {cat.id: {
            'id': cat.id,
            'name': cat.name,
            'slug': cat.slug,
            'description': cat.description,
            'parent_id': cat.parent_id,
            'active': cat.active,
            'children': []
        } for cat in categories}
        
        # Build hierarchy
        roots = []
        for cat_id, cat_data in category_dict.items():
            if cat_data['parent_id'] is None:
                # This is a root category
                roots.append(cat_data)
            elif cat_data['parent_id'] in category_dict:
                # This is a child category
                category_dict[cat_data['parent_id']]['children'].append(cat_data)
        
        return roots

    def get_product_categories(self, product_id: str) -> List[Any]:
        """
        Get all categories that a product belongs to.
        
        Args:
            product_id: The product ID
            
        Returns:
            List of Category objects
        """
        # Use Flask's app_context if available
        if flask_app is not None and hasattr(flask_app, 'app_context'):
            with flask_app.app_context():
                return self._get_product_categories(product_id)
        else:
            # Fallback if we can't find a Flask app
            return self._get_product_categories(product_id)
    
    def _get_product_categories(self, product_id: str) -> List[Any]:
        """Internal implementation of get_product_categories."""
        try:
            # Get product-category associations
            associations = ProductCategory.query.filter_by(product_id=product_id).all()
            
            # Get category objects
            category_ids = [assoc.category_id for assoc in associations]
            categories = []
            
            for cat_id in category_ids:
                category = self.get_category(cat_id)
                if category:
                    categories.append(category)
            
            return categories
        except Exception as e:
            logger.error(f"Error in get_product_categories: {e}")
            return []

    def get_products_in_category(self, category_id: str, include_subcategories: bool = True) -> List[Any]:
        """
        Get all products in a category.
        
        Args:
            category_id: The category ID
            include_subcategories: Whether to include products from subcategories
            
        Returns:
            List of Product objects
        """
        # Use Flask's app_context if available
        if flask_app is not None and hasattr(flask_app, 'app_context'):
            with flask_app.app_context():
                return self._get_products_in_category(category_id, include_subcategories)
        else:
            # Fallback if we can't find a Flask app
            return self._get_products_in_category(category_id, include_subcategories)
            
    def _get_products_in_category(self, category_id: str, include_subcategories: bool = True) -> List[Any]:
        """Internal implementation of get_products_in_category."""
        try:
            # Use eager loading when available
            try:
                from sqlalchemy.orm import joinedload
                query = Product.query.options(joinedload(Product.category_objects))
            except (ImportError, AttributeError):
                query = Product.query
            
            # Get direct product-category associations
            associations = ProductCategory.query.filter_by(category_id=category_id).all()
            product_ids = [assoc.product_id for assoc in associations]
            
            # Get subcategory products if requested
            if include_subcategories:
                subcategories = Category.query.filter_by(parent_id=category_id).all()
                for subcat in subcategories:
                    # Recursive call - note this will use the public method which has app_context
                    sub_products = self.get_products_in_category(subcat.id, include_subcategories=True)
                    product_ids.extend([p.id for p in sub_products if p.id not in product_ids])
            
            # Get product objects
            if product_ids:
                products = query.filter(Product.id.in_(product_ids)).all()
            else:
                products = []
            
            return products
        except Exception as e:
            logger.error(f"Error in get_products_in_category: {e}")
            return []

    def assign_product_to_category(self, product_id: str, category_id: str) -> bool:
        """
        Assign a product to a category.
        
        Args:
            product_id: The product ID
            category_id: The category ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if product and category exist
            product = Product.query.get(product_id)
            category = Category.query.get(category_id)
            
            if not product or not category:
                logger.warning(f"Product {product_id} or category {category_id} not found")
                return False
            
            # Check if association already exists
            existing = ProductCategory.query.filter_by(
                product_id=product_id,
                category_id=category_id
            ).first()
            
            if existing:
                logger.info(f"Product {product_id} is already in category {category_id}")
                return True
            
            # Create new association
            association = ProductCategory(
                product_id=product_id,
                category_id=category_id
            )
            
            db.session.add(association)
            db.session.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error in assign_product_to_category: {e}")
            if db is not None and hasattr(db, 'session'):
                db.session.rollback()
            return False

    def remove_product_from_category(self, product_id: str, category_id: str) -> bool:
        """
        Remove a product from a category.
        
        Args:
            product_id: The product ID
            category_id: The category ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if association exists
            association = ProductCategory.query.filter_by(
                product_id=product_id,
                category_id=category_id
            ).first()
            
            if not association:
                logger.warning(f"Product {product_id} is not in category {category_id}")
                return False
            
            # Remove association
            db.session.delete(association)
            db.session.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error in remove_product_from_category: {e}")
            if db is not None and hasattr(db, 'session'):
                db.session.rollback()
            return False

    def sync_product_categories(self, product_id: str, category_ids: List[str]) -> bool:
        """
        Sync a product's categories to match the provided list.
        
        Args:
            product_id: The product ID
            category_ids: List of category IDs to assign to the product
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current associations
            current_associations = ProductCategory.query.filter_by(product_id=product_id).all()
            current_category_ids = [assoc.category_id for assoc in current_associations]
            
            # Categories to add
            to_add = [cat_id for cat_id in category_ids if cat_id not in current_category_ids]
            
            # Categories to remove
            to_remove = [cat_id for cat_id in current_category_ids if cat_id not in category_ids]
            
            # Perform removals
            for cat_id in to_remove:
                self.remove_product_from_category(product_id, cat_id)
            
            # Perform additions
            for cat_id in to_add:
                self.assign_product_to_category(product_id, cat_id)
            
            return True
        except Exception as e:
            logger.error(f"Error in sync_product_categories: {e}")
            if db is not None and hasattr(db, 'session'):
                db.session.rollback()
            return False

    def migrate_from_json_categories(self, tenant_id: str) -> Dict[str, int]:
        """
        Migrate products from using JSON categories to proper category relationships.
        
        Args:
            tenant_id: The tenant ID to migrate
            
        Returns:
            Dictionary with metrics about the migration
        """
        metrics = {
            "products_processed": 0,
            "categories_created": 0,
            "associations_created": 0,
            "errors": 0
        }
        
        try:
            # Get all products for this tenant
            products = Product.query.filter_by(tenant_id=tenant_id).all()
            
            for product in products:
                metrics["products_processed"] += 1
                
                # Skip products without categories
                if not hasattr(product, 'category_data') or not product.category_data:
                    continue
                
                try:
                    # Process each category string
                    category_names = product.category_data.split(',') if isinstance(product.category_data, str) else []
                    
                    for category_name in category_names:
                        category_name = category_name.strip()
                        if not category_name:
                            continue
                        
                        # Generate a slug from the category name
                        slug = category_name.lower().replace(' ', '-')
                        
                        # Check if category exists
                        category = self.get_category_by_slug(tenant_id, slug)
                        
                        # Create category if it doesn't exist
                        if not category:
                            category = self.create_category(
                                tenant_id=tenant_id,
                                name=category_name,
                                slug=slug,
                                description=f"Auto-created category for {category_name}"
                            )
                            metrics["categories_created"] += 1
                        
                        # Assign product to category
                        if category and self.assign_product_to_category(product.id, category.id):
                            metrics["associations_created"] += 1
                
                except Exception as prod_error:
                    logger.error(f"Error migrating product {product.id}: {prod_error}")
                    metrics["errors"] += 1
            
            return metrics
        except Exception as e:
            logger.error(f"Error in migrate_from_json_categories: {e}")
            metrics["errors"] += 1
            return metrics