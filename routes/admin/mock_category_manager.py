"""
Mock Category Manager for Admin routes.

This module provides a simplified CategoryManager that works with FastAPI routes
without requiring Flask's application context.
"""
import logging
import uuid
from typing import List, Optional, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

# Dict to store sample categories by tenant
SAMPLE_CATEGORIES = {}

class MockCategoryManager:
    """
    A simplified CategoryManager for use in FastAPI routes.
    This class provides a similar interface to the real CategoryManager
    but uses sample data to avoid Flask's application context requirements.
    """
    
    def __init__(self):
        """Initialize the MockCategoryManager."""
        logger.info("MockCategoryManager initialized")
        self._load_sample_categories()
        
    def _load_sample_categories(self):
        """Load sample categories for demo purposes."""
        global SAMPLE_CATEGORIES
        
        # Tech Gadgets tenant categories (real tenant ID: ea6c4bc0-d5aa-4d4f-862c-5d47e7c3f410)
        tech_categories = [
            {
                "id": "a193dafe-bd3f-4e69-ae56-f48cfdc71400",
                "name": "Laptops",
                "slug": "laptops",
                "description": "Portable computing devices",
                "parent_id": None,
                "active": True,
                "product_count": 2,
                "subcategory_count": 0,
                "tenant_id": "ea6c4bc0-d5aa-4d4f-862c-5d47e7c3f410"
            },
            {
                "id": "25159982-5668-4945-be05-d6b5d196593d",
                "name": "Electronics",
                "slug": "electronics",
                "description": "Electronic devices and gadgets",
                "parent_id": None,
                "active": True,
                "product_count": 2,
                "subcategory_count": 0,
                "tenant_id": "ea6c4bc0-d5aa-4d4f-862c-5d47e7c3f410"
            },
            {
                "id": "f6b28d76-e19a-40ea-8e01-e3ef70dbd221",
                "name": "Audio",
                "slug": "audio",
                "description": "Audio equipment and accessories",
                "parent_id": None,
                "active": True,
                "product_count": 2,
                "subcategory_count": 0,
                "tenant_id": "ea6c4bc0-d5aa-4d4f-862c-5d47e7c3f410"
            },
            {
                "id": "30c3b35f-3b8f-498f-b6cd-7f640c61a930",
                "name": "Accessories",
                "slug": "accessories",
                "description": "Tech accessories for all devices",
                "parent_id": None,
                "active": True,
                "product_count": 3,
                "subcategory_count": 0,
                "tenant_id": "ea6c4bc0-d5aa-4d4f-862c-5d47e7c3f410"
            },
            {
                "id": "6d3b2c61-270a-4f3e-bd3f-d86712fc88e1",
                "name": "Phones",
                "slug": "phones",
                "description": "Smartphones and mobile devices",
                "parent_id": None,
                "active": True,
                "product_count": 1,
                "subcategory_count": 0,
                "tenant_id": "ea6c4bc0-d5aa-4d4f-862c-5d47e7c3f410"
            },
            {
                "id": "47353a62-140c-4cab-9f77-a9b542aad8ef",
                "name": "Smart Home",
                "slug": "smart-home",
                "description": "Smart home devices and systems",
                "parent_id": None,
                "active": True,
                "product_count": 1,
                "subcategory_count": 0,
                "tenant_id": "ea6c4bc0-d5aa-4d4f-862c-5d47e7c3f410"
            }
        ]
        
        # Demo Store 1 tenant categories
        demo_categories = [
            {
                "id": str(uuid.uuid4()),
                "name": "Clothing",
                "slug": "clothing",
                "description": "Apparel and fashion items",
                "parent_id": None,
                "active": True,
                "product_count": 3,
                "subcategory_count": 2,
                "tenant_id": "0a38d2a1-00fe-47ea-a6d2-f1595048aab0"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Men's Clothing",
                "slug": "mens-clothing",
                "description": "Clothing for men",
                "parent_id": None,
                "active": True,
                "product_count": 2,
                "subcategory_count": 0,
                "tenant_id": "0a38d2a1-00fe-47ea-a6d2-f1595048aab0"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Women's Clothing",
                "slug": "womens-clothing",
                "description": "Clothing for women",
                "parent_id": None,
                "active": True,
                "product_count": 1,
                "subcategory_count": 0,
                "tenant_id": "0a38d2a1-00fe-47ea-a6d2-f1595048aab0"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Shoes",
                "slug": "shoes",
                "description": "Footwear",
                "parent_id": None,
                "active": True,
                "product_count": 2,
                "subcategory_count": 0,
                "tenant_id": "0a38d2a1-00fe-47ea-a6d2-f1595048aab0"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Accessories",
                "slug": "accessories",
                "description": "Fashion accessories",
                "parent_id": None,
                "active": True,
                "product_count": 1,
                "subcategory_count": 0,
                "tenant_id": "0a38d2a1-00fe-47ea-a6d2-f1595048aab0"
            }
        ]
        
        # Store the categories by tenant ID
        SAMPLE_CATEGORIES = {
            "ea6c4bc0-d5aa-4d4f-862c-5d47e7c3f410": tech_categories,
            "0a38d2a1-00fe-47ea-a6d2-f1595048aab0": demo_categories,
            # Add other tenants as needed
        }
    
    def get_all_categories(self, tenant_id: str, include_inactive: bool = False) -> List:
        """
        Get all categories for a tenant.
        
        Args:
            tenant_id: The tenant ID
            include_inactive: Whether to include inactive categories
            
        Returns:
            List of Category objects
        """
        global SAMPLE_CATEGORIES
        
        # If we don't have data for this tenant, return an empty list
        if tenant_id not in SAMPLE_CATEGORIES:
            logger.warning(f"No categories found for tenant {tenant_id}")
            return []
        
        # Filter by active status if needed
        categories = SAMPLE_CATEGORIES[tenant_id]
        if not include_inactive:
            categories = [cat for cat in categories if cat["active"]]
            
        # Convert to category objects
        return [MockCategory(**cat) for cat in categories]
    
    def get_category(self, category_id: str) -> Optional:
        """
        Get a category by ID.
        
        Args:
            category_id: The category ID
            
        Returns:
            Category object or None if not found
        """
        global SAMPLE_CATEGORIES
        
        # Look for the category in all tenants
        for tenant_categories in SAMPLE_CATEGORIES.values():
            for cat in tenant_categories:
                if cat["id"] == category_id:
                    return MockCategory(**cat)
        
        return None
    
    def get_category_by_slug(self, tenant_id: str, slug: str) -> Optional:
        """
        Get a category by slug for a tenant.
        
        Args:
            tenant_id: The tenant ID
            slug: The category slug
            
        Returns:
            Category object or None if not found
        """
        categories = self.get_all_categories(tenant_id)
        for cat in categories:
            if cat.slug == slug:
                return cat
        
        return None
    
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
        global SAMPLE_CATEGORIES
        
        # Check if a category with the same slug already exists
        existing = self.get_category_by_slug(tenant_id, slug)
        if existing:
            raise ValueError(f"Category with slug '{slug}' already exists for this tenant")
        
        # Create new category
        category_dict = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "name": name,
            "slug": slug,
            "description": description,
            "parent_id": parent_id,
            "active": active,
            "product_count": 0,
            "subcategory_count": 0
        }
        
        # Add to our dictionary
        if tenant_id not in SAMPLE_CATEGORIES:
            SAMPLE_CATEGORIES[tenant_id] = []
        
        SAMPLE_CATEGORIES[tenant_id].append(category_dict)
        
        return MockCategory(**category_dict)
    
    def update_category(self, category_id: str, **kwargs):
        """
        Update a category.
        
        Args:
            category_id: The category ID
            **kwargs: Fields to update (name, slug, description, parent_id, active)
            
        Returns:
            The updated Category object or None if not found
        """
        global SAMPLE_CATEGORIES
        
        # Look for the category
        category = None
        tenant_id = None
        
        for tid, tenant_categories in SAMPLE_CATEGORIES.items():
            for i, cat in enumerate(tenant_categories):
                if cat["id"] == category_id:
                    category = cat
                    tenant_id = tid
                    category_index = i
                    break
            if category:
                break
                
        if not category:
            logger.warning(f"Category with ID {category_id} not found")
            return None
        
        # Update allowed fields
        allowed_fields = ["name", "slug", "description", "parent_id", "active"]
        for field, value in kwargs.items():
            if field in allowed_fields:
                category[field] = value
        
        # If slug is being updated, check for duplicates
        if "slug" in kwargs:
            slug = kwargs["slug"]
            for cat in SAMPLE_CATEGORIES[tenant_id]:
                if cat["slug"] == slug and cat["id"] != category_id:
                    raise ValueError(f"Category with slug '{slug}' already exists for this tenant")
        
        # Update in our dictionary
        SAMPLE_CATEGORIES[tenant_id][category_index] = category
        
        return MockCategory(**category)
    
    def delete_category(self, category_id: str) -> bool:
        """
        Delete a category.
        
        Args:
            category_id: The category ID
            
        Returns:
            True if successful, False otherwise
        """
        global SAMPLE_CATEGORIES
        
        # Look for the category
        for tenant_id, tenant_categories in SAMPLE_CATEGORIES.items():
            for i, cat in enumerate(tenant_categories):
                if cat["id"] == category_id:
                    # Check if category has subcategories
                    subcategories = [c for c in tenant_categories if c["parent_id"] == category_id]
                    if subcategories:
                        logger.warning(f"Cannot delete category {category_id} as it has {len(subcategories)} subcategories")
                        return False
                    
                    # Delete the category
                    SAMPLE_CATEGORIES[tenant_id].pop(i)
                    return True
        
        logger.warning(f"Category with ID {category_id} not found")
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
    
    def get_products_in_category(self, category_id: str, include_subcategories: bool = True) -> List:
        """
        Get all products in a category.
        
        Args:
            category_id: The category ID
            include_subcategories: Whether to include products from subcategories
            
        Returns:
            List of Product objects
        """
        # This is a mock method, we'll just return a mocked product count
        category = self.get_category(category_id)
        if not category:
            logger.warning(f"Category with ID {category_id} not found")
            return []
        
        # Return a list of the length indicated by product_count
        return [None] * category.product_count


class MockCategory:
    """
    A simplified Category class for use with the MockCategoryManager.
    """
    
    def __init__(self, **kwargs):
        """Initialize a MockCategory with the provided attributes."""
        self.id = kwargs.get("id", str(uuid.uuid4()))
        self.tenant_id = kwargs.get("tenant_id", "")
        self.name = kwargs.get("name", "")
        self.slug = kwargs.get("slug", "")
        self.description = kwargs.get("description", "")
        self.parent_id = kwargs.get("parent_id", None)
        self.active = kwargs.get("active", True)
        self.product_count = kwargs.get("product_count", 0)
        self.subcategory_count = kwargs.get("subcategory_count", 0)
        self.products = []