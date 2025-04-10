"""
Category management module for PyCommerce.

This module provides the CategoryManager class for managing product categories.
"""
import logging
import uuid
from typing import List, Optional, Dict, Any, Union

from models import db, Category, ProductCategory, Product, Tenant

# Configure logging
logger = logging.getLogger(__name__)

class CategoryManager:
    """Manager class for category operations."""

    def __init__(self):
        """Initialize the CategoryManager."""
        self.db = db
        logger.info("CategoryManager initialized")

    def get_all_categories(self, tenant_id: str, include_inactive: bool = False) -> List[Category]:
        """
        Get all categories for a tenant.
        
        Args:
            tenant_id: The tenant ID
            include_inactive: Whether to include inactive categories
            
        Returns:
            List of Category objects
        """
        query = Category.query.filter_by(tenant_id=tenant_id)
        
        if not include_inactive:
            query = query.filter_by(active=True)
            
        return query.all()
    
    def get_category(self, category_id: str) -> Optional[Category]:
        """
        Get a category by ID.
        
        Args:
            category_id: The category ID
            
        Returns:
            Category object or None if not found
        """
        return Category.query.get(category_id)
    
    def get_category_by_slug(self, tenant_id: str, slug: str) -> Optional[Category]:
        """
        Get a category by slug for a tenant.
        
        Args:
            tenant_id: The tenant ID
            slug: The category slug
            
        Returns:
            Category object or None if not found
        """
        return Category.query.filter_by(tenant_id=tenant_id, slug=slug).first()
    
    def create_category(self, tenant_id: str, name: str, slug: str, 
                        description: Optional[str] = None, 
                        parent_id: Optional[str] = None,
                        active: bool = True) -> Category:
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
        self.db.session.add(category)
        self.db.session.commit()
        
        return category
    
    def update_category(self, category_id: str, **kwargs) -> Optional[Category]:
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
        
        self.db.session.commit()
        return category
    
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
        
        # Check if category has subcategories
        subcategories = Category.query.filter_by(parent_id=category_id).count()
        if subcategories > 0:
            logger.warning(f"Cannot delete category {category_id} as it has {subcategories} subcategories")
            return False
        
        # Remove product associations
        ProductCategory.query.filter_by(category_id=category_id).delete()
        
        # Delete the category
        self.db.session.delete(category)
        self.db.session.commit()
        
        return True
    
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
        # Check if product and category exist
        product = Product.query.get(product_id)
        category = Category.query.get(category_id)
        
        if not product or not category:
            logger.warning(f"Product {product_id} or category {category_id} not found")
            return False
        
        # Check if they belong to the same tenant
        if product.tenant_id != category.tenant_id:
            logger.warning(f"Product {product_id} and category {category_id} belong to different tenants")
            return False
        
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
        self.db.session.add(association)
        
        # Update the legacy categories JSON field for backward compatibility
        if category.name not in product.categories:
            current_categories = product.categories or []
            current_categories.append(category.name)
            product.categories = current_categories
        
        self.db.session.commit()
        return True
    
    def remove_product_from_category(self, product_id: str, category_id: str) -> bool:
        """
        Remove a product from a category.
        
        Args:
            product_id: The product ID
            category_id: The category ID
            
        Returns:
            True if successful, False otherwise
        """
        # Check if the association exists
        association = ProductCategory.query.filter_by(
            product_id=product_id, 
            category_id=category_id
        ).first()
        
        if not association:
            logger.warning(f"Product {product_id} is not assigned to category {category_id}")
            return False
        
        # Delete the association
        self.db.session.delete(association)
        
        # Update the legacy categories JSON field for backward compatibility
        product = Product.query.get(product_id)
        category = Category.query.get(category_id)
        
        if product and category and category.name in product.categories:
            current_categories = product.categories or []
            current_categories.remove(category.name)
            product.categories = current_categories
        
        self.db.session.commit()
        return True
    
    def sync_product_categories(self, product_id: str, category_ids: List[str]) -> bool:
        """
        Sync a product's categories to match the provided list.
        
        Args:
            product_id: The product ID
            category_ids: List of category IDs to assign to the product
            
        Returns:
            True if successful, False otherwise
        """
        product = Product.query.get(product_id)
        if not product:
            logger.warning(f"Product {product_id} not found")
            return False
        
        # Get current category associations
        current_associations = ProductCategory.query.filter_by(product_id=product_id).all()
        current_category_ids = [assoc.category_id for assoc in current_associations]
        
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
        
        # Get all products for this tenant
        products = Product.query.filter_by(tenant_id=tenant_id).all()
        
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