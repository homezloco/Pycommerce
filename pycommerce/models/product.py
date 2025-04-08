"""
Product-related models and management.

This module defines the Product model and ProductManager class for
managing products in the PyCommerce SDK.
"""

import logging
from typing import Dict, List, Optional, Union, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator
from datetime import datetime

logger = logging.getLogger("pycommerce.models.product")

class Product(BaseModel):
    """
    Represents a product in the system.
    """
    id: UUID = Field(default_factory=uuid4)
    sku: str
    name: str
    description: str = ""
    price: float
    stock: int = 0
    images: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('price')
    def price_must_be_positive(cls, v):
        if v < 0:
            raise ValueError('Price must be non-negative')
        return v
    
    @validator('stock')
    def stock_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError('Stock must be non-negative')
        return v
    
    class Config:
        arbitrary_types_allowed = True


class ProductManager:
    """
    Manages product operations.
    """
    
    def __init__(self):
        """Initialize a new ProductManager."""
        self._products: Dict[UUID, Product] = {}
        self._sku_index: Dict[str, UUID] = {}
    
    def create(self, product_data: dict) -> Product:
        """
        Create a new product.
        
        Args:
            product_data: Dictionary containing product data
            
        Returns:
            The created product
            
        Raises:
            ProductError: If product creation fails
        """
        from pycommerce.core.exceptions import ProductError
        
        try:
            # Check if SKU already exists
            if product_data.get('sku') and product_data['sku'] in self._sku_index:
                raise ProductError(f"Product with SKU '{product_data['sku']}' already exists")
            
            # Create and store the product
            product = Product(**product_data)
            self._products[product.id] = product
            self._sku_index[product.sku] = product.id
            
            logger.debug(f"Created product: {product.name} (ID: {product.id})")
            return product
            
        except ValueError as e:
            raise ProductError(f"Invalid product data: {str(e)}")
    
    def get(self, product_id: Union[UUID, str]) -> Product:
        """
        Get a product by ID.
        
        Args:
            product_id: The ID of the product to get
            
        Returns:
            The product
            
        Raises:
            ProductError: If the product is not found
        """
        from pycommerce.core.exceptions import ProductError
        
        # Convert string ID to UUID if needed
        if isinstance(product_id, str):
            try:
                product_id = UUID(product_id)
            except ValueError:
                # Check if this is a SKU
                if product_id in self._sku_index:
                    product_id = self._sku_index[product_id]
                else:
                    raise ProductError(f"Invalid product ID or SKU: {product_id}")
        
        if product_id not in self._products:
            raise ProductError(f"Product not found: {product_id}")
        
        return self._products[product_id]
    
    def update(self, product_id: Union[UUID, str], product_data: dict) -> Product:
        """
        Update a product.
        
        Args:
            product_id: The ID of the product to update
            product_data: Dictionary containing updated product data
            
        Returns:
            The updated product
            
        Raises:
            ProductError: If the product is not found or update fails
        """
        from pycommerce.core.exceptions import ProductError
        
        # Get the product first
        product = self.get(product_id)
        
        try:
            # Handle SKU changes
            if 'sku' in product_data and product_data['sku'] != product.sku:
                if product_data['sku'] in self._sku_index:
                    raise ProductError(f"Product with SKU '{product_data['sku']}' already exists")
                # Update SKU index
                del self._sku_index[product.sku]
                self._sku_index[product_data['sku']] = product.id
            
            # Update the product
            for key, value in product_data.items():
                setattr(product, key, value)
            
            # Update timestamp
            product.updated_at = datetime.utcnow()
            
            logger.debug(f"Updated product: {product.name} (ID: {product.id})")
            return product
            
        except ValueError as e:
            raise ProductError(f"Invalid product data: {str(e)}")
    
    def delete(self, product_id: Union[UUID, str]) -> None:
        """
        Delete a product.
        
        Args:
            product_id: The ID of the product to delete
            
        Raises:
            ProductError: If the product is not found
        """
        # Get the product first (this will validate the ID)
        product = self.get(product_id)
        
        # Remove from indexes
        del self._sku_index[product.sku]
        del self._products[product.id]
        
        logger.debug(f"Deleted product: {product.name} (ID: {product.id})")
    
    def list(self, 
             category: Optional[str] = None, 
             min_price: Optional[float] = None,
             max_price: Optional[float] = None,
             in_stock: Optional[bool] = None) -> List[Product]:
        """
        List products with optional filtering.
        
        Args:
            category: Filter by category
            min_price: Filter by minimum price
            max_price: Filter by maximum price
            in_stock: Filter by stock availability
            
        Returns:
            List of products matching the filters
        """
        products = list(self._products.values())
        
        # Apply filters
        if category:
            products = [p for p in products if category in p.categories]
        
        if min_price is not None:
            products = [p for p in products if p.price >= min_price]
        
        if max_price is not None:
            products = [p for p in products if p.price <= max_price]
        
        if in_stock is not None:
            if in_stock:
                products = [p for p in products if p.stock > 0]
            else:
                products = [p for p in products if p.stock == 0]
        
        return products
    
    def search(self, query: str) -> List[Product]:
        """
        Search for products.
        
        Args:
            query: The search query
            
        Returns:
            List of products matching the search query
        """
        query = query.lower()
        results = []
        
        for product in self._products.values():
            # Search in name, description, and SKU
            if (query in product.name.lower() or 
                query in product.description.lower() or 
                query in product.sku.lower()):
                results.append(product)
        
        return results
        
    def get_by_tenant(self, tenant_id: str) -> List[Product]:
        """
        Get all products for a specific tenant.
        
        Args:
            tenant_id: The ID of the tenant
            
        Returns:
            List of products for the tenant
        """
        # Try to query directly from the database
        try:
            from pycommerce.models.db_registry import Product as DbProduct
            from pycommerce.core.db import get_db
            
            logger.info(f"Querying database for products of tenant: {tenant_id}")
            
            # Get a session for direct database access
            session = get_db()
            db_products = session.query(DbProduct).filter(DbProduct.tenant_id == tenant_id).all()
            
            # Convert DB products to API products
            products = []
            for db_product in db_products:
                product = Product(
                    id=UUID(db_product.id) if isinstance(db_product.id, str) else db_product.id,
                    sku=db_product.sku,
                    name=db_product.name,
                    description=db_product.description or "",
                    price=db_product.price,
                    stock=db_product.stock,
                    categories=db_product.categories or [],
                    metadata={"tenant_id": db_product.tenant_id}
                )
                products.append(product)
                
            logger.info(f"Found {len(products)} products for tenant {tenant_id} in database")
            return products
            
        except Exception as e:
            logger.error(f"Error querying database for tenant products: {str(e)}")
            logger.info(f"Falling back to in-memory products for tenant: {tenant_id}")
            # Fallback to in-memory implementation
            return list(self._products.values())
