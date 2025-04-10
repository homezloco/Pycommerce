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

# Mock data for CategoryManager in FastAPI environment
_mock_categories = {}
_mock_associations = {}
_in_flask_app = None

def is_flask_app():
    """
    Check if we're running in a Flask app or FastAPI environment.
    Caches the result.
    
    Returns:
        bool: True if Flask, False if FastAPI
    """
    global _in_flask_app
    
    if _in_flask_app is not None:
        return _in_flask_app
    
    try:
        import flask
        if hasattr(flask, 'current_app') and flask.current_app:
            _in_flask_app = True
            return True
    except (ImportError, RuntimeError):
        pass
    
    try:
        # Try to find the Flask app module
        for module_name in ["web_app", "main", "app"]:
            try:
                module = __import__(module_name)
                if hasattr(module, "app"):
                    flask_app = getattr(module, "app")
                    if hasattr(flask_app, 'app_context'):
                        _in_flask_app = True
                        return True
            except ImportError:
                continue
    except:
        pass
    
    _in_flask_app = False
    return False


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
    
    return db, Category, ProductCategory, Product, Tenant


def ensure_db_session(func):
    """
    Decorator that uses Flask app_context when available, or falls back to mock data
    when running in FastAPI.
    
    Args:
        func: The function to wrap
        
    Returns:
        Wrapped function that ensures proper data access in any environment
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Import global variables
        db, Category, ProductCategory, Product, Tenant = get_db_session()
        
        if db is None:
            logger.error("Failed to import database models")
            return None
        
        # If we're in a Flask app, use the real database
        if is_flask_app():
            try:
                import flask
                if flask.has_app_context():
                    return func(self, *args, **kwargs)
                
                # Try to find the Flask app
                for module_name in ["web_app", "main", "app"]:
                    try:
                        module = __import__(module_name)
                        if hasattr(module, "app"):
                            flask_app = getattr(module, "app")
                            if hasattr(flask_app, 'app_context'):
                                with flask_app.app_context():
                                    return func(self, *args, **kwargs)
                    except ImportError:
                        continue
            except Exception as e:
                logger.warning(f"Error in Flask app context: {e}")
                
        # If we're here, we're in FastAPI or couldn't get a Flask app context
        # Use mock implementation based on the function name
        func_name = func.__name__
        
        # Initialize mock data if we haven't done it yet
        if not _mock_categories and hasattr(self, '_initialize_mock_data'):
            self._initialize_mock_data()
        
        # Call the appropriate mock method
        if hasattr(self, f"_mock_{func_name}"):
            mock_method = getattr(self, f"_mock_{func_name}")
            return mock_method(*args, **kwargs)
        else:
            logger.error(f"No mock implementation for {func_name}")
            return None
    
    return wrapper

class CategoryManager:
    """Manager class for category operations."""

    def __init__(self):
        """Initialize the CategoryManager."""
        logger.info("CategoryManager initialized")
        self._initialize_mock_data()
        
    def _initialize_mock_data(self):
        """Initialize mock category data for FastAPI environment."""
        global _mock_categories, _mock_associations
        
        # Only initialize once
        if _mock_categories:
            return
            
        logger.info("Initializing mock category data for FastAPI environment")
        
        # Create some default categories for the Tech tenant
        tech_tenant_id = "ea6c4bc0-d5aa-4d4f-862c-5d47e7c3f410"  # Tech Gadgets tenant ID
        
        laptops_id = str(uuid.uuid4())
        electronics_id = str(uuid.uuid4())
        audio_id = str(uuid.uuid4())
        accessories_id = str(uuid.uuid4())
        phones_id = str(uuid.uuid4())
        smart_home_id = str(uuid.uuid4())
        
        # Create category objects (mimicking SQLAlchemy models)
        class MockCategory:
            def __init__(self, id, tenant_id, name, slug, description=None, parent_id=None, active=True):
                self.id = id
                self.tenant_id = tenant_id
                self.name = name
                self.slug = slug
                self.description = description
                self.parent_id = parent_id
                self.active = active
                self.products = []
                
        # Add categories
        _mock_categories[laptops_id] = MockCategory(
            id=laptops_id,
            tenant_id=tech_tenant_id,
            name="Laptops",
            slug="laptops",
            description="Portable computing devices",
        )
        
        _mock_categories[electronics_id] = MockCategory(
            id=electronics_id,
            tenant_id=tech_tenant_id,
            name="Electronics",
            slug="electronics",
            description="General electronic devices",
        )
        
        _mock_categories[audio_id] = MockCategory(
            id=audio_id,
            tenant_id=tech_tenant_id,
            name="Audio",
            slug="audio",
            description="Audio equipment and accessories",
        )
        
        _mock_categories[accessories_id] = MockCategory(
            id=accessories_id,
            tenant_id=tech_tenant_id,
            name="Accessories",
            slug="accessories",
            description="Device accessories and add-ons",
        )
        
        _mock_categories[phones_id] = MockCategory(
            id=phones_id,
            tenant_id=tech_tenant_id,
            name="Phones",
            slug="phones",
            description="Mobile phones and smartphones",
        )
        
        _mock_categories[smart_home_id] = MockCategory(
            id=smart_home_id,
            tenant_id=tech_tenant_id,
            name="Smart Home",
            slug="smart-home",
            description="Smart home devices and automation",
        )
        
        # Initialize product-category associations
        _mock_associations = {}
        
        logger.info(f"Initialized {len(_mock_categories)} mock categories")
    
    def _mock_get_all_categories(self, tenant_id, include_inactive=False):
        """Mock implementation of get_all_categories."""
        result = []
        for category in _mock_categories.values():
            if category.tenant_id == tenant_id:
                if include_inactive or category.active:
                    result.append(category)
        return result
    
    def _mock_get_category(self, category_id):
        """Mock implementation of get_category."""
        return _mock_categories.get(category_id)
    
    def _mock_get_category_by_slug(self, tenant_id, slug):
        """Mock implementation of get_category_by_slug."""
        for category in _mock_categories.values():
            if category.tenant_id == tenant_id and category.slug == slug:
                return category
        return None
    
    def _mock_create_category(self, tenant_id, name, slug, description, parent_id, active):
        """Mock implementation of create_category."""
        # Generate a new ID
        category_id = str(uuid.uuid4())
        
        # Create a new category object
        class MockCategory:
            def __init__(self, id, tenant_id, name, slug, description=None, parent_id=None, active=True):
                self.id = id
                self.tenant_id = tenant_id
                self.name = name
                self.slug = slug
                self.description = description
                self.parent_id = parent_id
                self.active = active
                self.products = []
        
        category = MockCategory(
            id=category_id,
            tenant_id=tenant_id,
            name=name,
            slug=slug,
            description=description,
            parent_id=parent_id,
            active=active
        )
        
        # Store it
        _mock_categories[category_id] = category
        
        return category
    
    def _mock_update_category(self, category, kwargs, category_id):
        """Mock implementation of update_category."""
        # Update the category
        for field, value in kwargs.items():
            if field in ["name", "slug", "description", "parent_id", "active"]:
                setattr(category, field, value)
        
        return category
    
    def _mock_delete_category(self, category_id, category):
        """Mock implementation of delete_category."""
        # Check for subcategories
        for cat in _mock_categories.values():
            if cat.parent_id == category_id:
                return False
        
        # Delete the category
        if category_id in _mock_categories:
            del _mock_categories[category_id]
        
        # Remove associations
        for assoc_key in list(_mock_associations.keys()):
            if assoc_key.endswith(f"_{category_id}"):
                del _mock_associations[assoc_key]
        
        return True
    
    def _mock_get_product_and_category(self, product_id, category_id):
        """Mock implementation of get_product_and_category."""
        # We'd need product data for this, return a simplified version
        class MockProduct:
            def __init__(self, id, tenant_id):
                self.id = id
                self.tenant_id = "ea6c4bc0-d5aa-4d4f-862c-5d47e7c3f410"  # Tech Gadgets tenant ID
                self.categories = []
        
        product = MockProduct(id=product_id, tenant_id="ea6c4bc0-d5aa-4d4f-862c-5d47e7c3f410")
        category = _mock_categories.get(category_id)
        
        return product, category
    
    def _mock_assign_product_to_category(self, product_id, category_id, product, category):
        """Mock implementation of assign_product_to_category."""
        # Create association key
        assoc_key = f"{product_id}_{category_id}"
        
        # Check if it already exists
        if assoc_key in _mock_associations:
            return True
        
        # Add the association
        _mock_associations[assoc_key] = True
        
        # Add to products list
        if hasattr(category, 'products'):
            category.products.append(product)
        
        return True
    
    def _mock_check_and_remove_association(self, product_id, category_id):
        """Mock implementation of check_and_remove_association."""
        # Create association key
        assoc_key = f"{product_id}_{category_id}"
        
        # Check if it exists
        if assoc_key not in _mock_associations:
            return False, None, None
        
        # Remove the association
        del _mock_associations[assoc_key]
        
        # Mock product and category for return
        class MockProduct:
            def __init__(self, id, tenant_id):
                self.id = id
                self.tenant_id = "ea6c4bc0-d5aa-4d4f-862c-5d47e7c3f410"  # Tech Gadgets tenant ID
                self.categories = []
        
        product = MockProduct(id=product_id, tenant_id="ea6c4bc0-d5aa-4d4f-862c-5d47e7c3f410")
        category = _mock_categories.get(category_id)
        
        return True, product, category

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