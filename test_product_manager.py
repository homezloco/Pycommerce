import unittest
from unittest.mock import patch, MagicMock
from uuid import UUID
import sys
import os

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from pycommerce.models.product import ProductManager, Product


class TestProductManager(unittest.TestCase):
    """Test cases for the ProductManager class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.product_manager = ProductManager()
        
        # Create some test products
        self.test_product1 = Product(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            sku="TEST-SKU-1",
            name="Test Product 1",
            description="This is test product 1",
            price=19.99,
            stock=10,
            categories=["test", "electronics"],
            metadata={"tenant_id": "test-tenant"}
        )
        
        self.test_product2 = Product(
            id=UUID("87654321-8765-4321-8765-432187654321"),
            sku="TEST-SKU-2",
            name="Test Product 2",
            description="This is test product 2",
            price=29.99,
            stock=5,
            categories=["test", "clothing"],
            metadata={"tenant_id": "test-tenant"}
        )
        
        # Add test products to the manager
        self.product_manager._products[self.test_product1.id] = self.test_product1
        self.product_manager._sku_index[self.test_product1.sku] = self.test_product1.id
        self.product_manager._products[self.test_product2.id] = self.test_product2
        self.product_manager._sku_index[self.test_product2.sku] = self.test_product2.id

    def test_get_product_by_id(self):
        """Test getting a product by ID."""
        product = self.product_manager.get(self.test_product1.id)
        self.assertEqual(product.name, "Test Product 1")
        self.assertEqual(product.price, 19.99)
        
        # Test with string ID
        product = self.product_manager.get(str(self.test_product1.id))
        self.assertEqual(product.name, "Test Product 1")

    def test_get_product_by_sku(self):
        """Test getting a product by SKU."""
        product = self.product_manager.get("TEST-SKU-1")
        self.assertEqual(product.id, self.test_product1.id)
        self.assertEqual(product.name, "Test Product 1")

    def test_list_products(self):
        """Test listing all products."""
        products = self.product_manager.list()
        self.assertEqual(len(products), 2)
        
        # Test with filters
        products = self.product_manager.list(category="electronics")
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].name, "Test Product 1")
        
        products = self.product_manager.list(min_price=20.0)
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].name, "Test Product 2")
        
        products = self.product_manager.list(max_price=20.0)
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].name, "Test Product 1")
        
        products = self.product_manager.list(in_stock=True)
        self.assertEqual(len(products), 2)
        
        products = self.product_manager.list(in_stock=False)
        self.assertEqual(len(products), 0)

    def test_search_products(self):
        """Test searching for products."""
        products = self.product_manager.search("test")
        self.assertEqual(len(products), 2)
        
        products = self.product_manager.search("product 1")
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].name, "Test Product 1")
        
        products = self.product_manager.search("nonexistent")
        self.assertEqual(len(products), 0)

    def test_update_product(self):
        """Test updating a product."""
        update_data = {
            "name": "Updated Product Name",
            "price": 24.99,
            "stock": 15
        }
        
        updated_product = self.product_manager.update(self.test_product1.id, update_data)
        
        self.assertEqual(updated_product.name, "Updated Product Name")
        self.assertEqual(updated_product.price, 24.99)
        self.assertEqual(updated_product.stock, 15)
        self.assertEqual(updated_product.description, "This is test product 1")  # Unchanged
        
        # Verify product was actually updated in the manager
        product = self.product_manager.get(self.test_product1.id)
        self.assertEqual(product.name, "Updated Product Name")
        self.assertEqual(product.price, 24.99)

    def test_delete_product(self):
        """Test deleting a product."""
        self.product_manager.delete(self.test_product1.id)
        
        # Verify product was deleted
        with self.assertRaises(Exception):
            self.product_manager.get(self.test_product1.id)
        
        # Verify product is no longer in SKU index
        self.assertNotIn(self.test_product1.sku, self.product_manager._sku_index)
        
        # Verify other product is still there
        product = self.product_manager.get(self.test_product2.id)
        self.assertEqual(product.name, "Test Product 2")

    @patch('pycommerce.core.db.get_db')
    def test_get_by_tenant(self, mock_get_db):
        """Test getting products by tenant."""
        # Mock database session
        mock_session = MagicMock()
        mock_get_db.return_value = mock_session
        
        # Mock DB products
        mock_db_product1 = MagicMock()
        mock_db_product1.id = str(self.test_product1.id)
        mock_db_product1.sku = self.test_product1.sku
        mock_db_product1.name = self.test_product1.name
        mock_db_product1.description = self.test_product1.description
        mock_db_product1.price = self.test_product1.price
        mock_db_product1.stock = self.test_product1.stock
        mock_db_product1.categories = self.test_product1.categories
        mock_db_product1.tenant_id = "test-tenant"
        
        mock_db_product2 = MagicMock()
        mock_db_product2.id = str(self.test_product2.id)
        mock_db_product2.sku = self.test_product2.sku
        mock_db_product2.name = self.test_product2.name
        mock_db_product2.description = self.test_product2.description
        mock_db_product2.price = self.test_product2.price
        mock_db_product2.stock = self.test_product2.stock
        mock_db_product2.categories = self.test_product2.categories
        mock_db_product2.tenant_id = "test-tenant"
        
        # Set up the mock query result
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.all.return_value = [mock_db_product1, mock_db_product2]
        
        # Test get_by_tenant method
        products = self.product_manager.get_by_tenant("test-tenant")
        
        # Verify we got two products back
        self.assertEqual(len(products), 2)
        
        # Verify products have correct data
        product_names = {p.name for p in products}
        self.assertIn("Test Product 1", product_names)
        self.assertIn("Test Product 2", product_names)
        
        # Verify tenant_id was set correctly in metadata
        for product in products:
            self.assertEqual(product.metadata["tenant_id"], "test-tenant")
    
    def test_list_by_tenant(self):
        """Test list_by_tenant method calls get_by_tenant."""
        with patch.object(self.product_manager, 'get_by_tenant') as mock_get_by_tenant:
            mock_get_by_tenant.return_value = [self.test_product1, self.test_product2]
            
            products = self.product_manager.list_by_tenant("test-tenant")
            
            # Verify get_by_tenant was called with correct tenant_id
            mock_get_by_tenant.assert_called_once_with("test-tenant")
            
            # Verify we got the expected products back
            self.assertEqual(len(products), 2)
            product_ids = {p.id for p in products}
            self.assertIn(self.test_product1.id, product_ids)
            self.assertIn(self.test_product2.id, product_ids)


if __name__ == '__main__':
    unittest.main()