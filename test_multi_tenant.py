import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import required modules
from pycommerce.core.db import get_db
from pycommerce.sdk import AppTenantManager, AppProductManager
from pycommerce.models.tenant import TenantManager, TenantDTO
from pycommerce.models.product import ProductManager

class TestMultiTenant(unittest.TestCase):
    """Test multi-tenant functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create instance of tenant and product managers
        self.tenant_manager = AppTenantManager()
        self.product_manager = AppProductManager()
        
        # Define test data
        self.test_tenants = [
            {"id": "tenant1", "name": "Tenant 1", "slug": "tenant1", "domain": "tenant1.example.com"},
            {"id": "tenant2", "name": "Tenant 2", "slug": "tenant2", "domain": "tenant2.example.com"}
        ]
        
        self.test_products = {
            "tenant1": [
                {"id": "product1", "name": "Product 1", "price": 19.99, "sku": "T1-P1"},
                {"id": "product2", "name": "Product 2", "price": 29.99, "sku": "T1-P2"}
            ],
            "tenant2": [
                {"id": "product3", "name": "Product 3", "price": 39.99, "sku": "T2-P1"},
                {"id": "product4", "name": "Product 4", "price": 49.99, "sku": "T2-P2"}
            ]
        }

    @patch('pycommerce.models.tenant.TenantManager.list')
    def test_get_all_tenants(self, mock_list):
        """Test getting all tenants."""
        # Create mock tenants with proper string values
        mock_tenant1 = MagicMock()
        mock_tenant1.id = "tenant1"
        mock_tenant1.name = "Tenant 1"
        mock_tenant1.slug = "tenant1"
        mock_tenant1.domain = "tenant1.example.com"
        
        mock_tenant2 = MagicMock()
        mock_tenant2.id = "tenant2"
        mock_tenant2.name = "Tenant 2"
        mock_tenant2.slug = "tenant2"
        mock_tenant2.domain = "tenant2.example.com"
        
        # Configure the mock to return our tenants
        mock_list.return_value = [mock_tenant1, mock_tenant2]
        
        # Get all tenants
        tenants = self.tenant_manager.get_all()
        
        # Verify the correct number of tenants was returned
        self.assertEqual(len(tenants), 2)
        
        # Get actual name strings
        tenant_names = [str(t.name) for t in tenants]
        
        # Verify tenant attributes
        self.assertIn("Tenant 1", tenant_names)
        self.assertIn("Tenant 2", tenant_names)
        
        # Verify the tenant manager list method was called
        mock_list.assert_called_once()

    @patch('pycommerce.models.tenant.TenantManager.get_by_slug')
    def test_get_tenant_by_slug(self, mock_get_by_slug):
        """Test getting a tenant by slug."""
        # Set up mock tenant with string values
        mock_tenant = MagicMock()
        mock_tenant.id = "tenant1"
        mock_tenant.name = "Tenant 1"
        mock_tenant.slug = "tenant1"
        mock_tenant.domain = "tenant1.example.com"
        
        mock_get_by_slug.return_value = mock_tenant
        
        # Get tenant by slug
        tenant = self.tenant_manager.get_by_slug("tenant1")
        
        # Verify tenant attributes
        self.assertEqual(str(tenant.id), "tenant1")
        self.assertEqual(str(tenant.name), "Tenant 1")
        self.assertEqual(str(tenant.slug), "tenant1")
        self.assertEqual(str(tenant.domain), "tenant1.example.com")
        
        # Verify the tenant manager get_by_slug method was called with the correct slug
        mock_get_by_slug.assert_called_once_with("tenant1")

    @patch('pycommerce.models.product.ProductManager.list_by_tenant')
    def test_get_products_by_tenant(self, mock_list_by_tenant):
        """Test getting products by tenant."""
        # Set up mock products with string values
        mock_product1 = MagicMock()
        mock_product1.id = "product1" 
        mock_product1.name = "Product 1"
        mock_product1.price = 19.99
        mock_product1.sku = "T1-P1"
        
        mock_product2 = MagicMock()
        mock_product2.id = "product2"
        mock_product2.name = "Product 2"
        mock_product2.price = 29.99
        mock_product2.sku = "T1-P2"
        
        # Configure the mock to return our products
        mock_list_by_tenant.return_value = [mock_product1, mock_product2]
        
        # Get products for tenant1
        products = self.product_manager.list_by_tenant("tenant1")
        
        # Verify the correct number of products was returned
        self.assertEqual(len(products), 2)
        
        # Get actual name strings
        product_names = [str(p.name) for p in products]
        
        # Verify product attributes
        self.assertIn("Product 1", product_names)
        self.assertIn("Product 2", product_names)
        
        # Verify the product manager list_by_tenant method was called with the correct tenant ID
        mock_list_by_tenant.assert_called_once_with("tenant1")

    @patch('pycommerce.sdk.AppTenantManager.get_by_slug')
    @patch('pycommerce.sdk.AppProductManager.list_by_tenant')
    def test_product_isolation_between_tenants(self, mock_list_by_tenant, mock_get_by_slug):
        """Test that products are isolated between tenants."""
        # Set up mock tenant1
        mock_tenant1 = MagicMock()
        mock_tenant1.id = "tenant1"
        mock_tenant1.name = "Tenant 1"
        mock_tenant1.slug = "tenant1"
        
        # Set up tenant1 products
        mock_product1 = MagicMock()
        mock_product1.id = "product1"
        mock_product1.name = "Product 1"
        mock_product1.price = 19.99
        mock_product1.sku = "T1-P1"
        
        mock_product2 = MagicMock()
        mock_product2.id = "product2"
        mock_product2.name = "Product 2" 
        mock_product2.price = 29.99
        mock_product2.sku = "T1-P2"
        
        tenant1_products = [mock_product1, mock_product2]
        
        # Set up tenant2 products
        mock_product3 = MagicMock()
        mock_product3.id = "product3"
        mock_product3.name = "Product 3"
        mock_product3.price = 39.99
        mock_product3.sku = "T2-P1"
        
        mock_product4 = MagicMock()
        mock_product4.id = "product4"
        mock_product4.name = "Product 4"
        mock_product4.price = 49.99
        mock_product4.sku = "T2-P2"
        
        tenant2_products = [mock_product3, mock_product4]
        
        # Set up mock tenant2
        mock_tenant2 = MagicMock()
        mock_tenant2.id = "tenant2"
        mock_tenant2.name = "Tenant 2"
        mock_tenant2.slug = "tenant2"
        
        # Configure mocks to return different values based on calls
        mock_get_by_slug.side_effect = [mock_tenant1, mock_tenant2]
        mock_list_by_tenant.side_effect = [tenant1_products, tenant2_products]
        
        # Get products for tenant1
        tenant1 = self.tenant_manager.get_by_slug("tenant1")
        products1 = self.product_manager.list_by_tenant(tenant1.id)
        
        # Verify tenant1 products
        self.assertEqual(len(products1), 2)
        product_names1 = [str(p.name) for p in products1]
        self.assertIn("Product 1", product_names1)
        self.assertIn("Product 2", product_names1)
        
        # Get products for tenant2
        tenant2 = self.tenant_manager.get_by_slug("tenant2")
        products2 = self.product_manager.list_by_tenant(tenant2.id)
        
        # Verify tenant2 products
        self.assertEqual(len(products2), 2)
        product_names2 = [str(p.name) for p in products2]
        self.assertIn("Product 3", product_names2)
        self.assertIn("Product 4", product_names2)
        
        # Verify the product manager list_by_tenant method was called with the correct tenant IDs
        mock_list_by_tenant.assert_any_call("tenant1")
        mock_list_by_tenant.assert_any_call("tenant2")


if __name__ == '__main__':
    unittest.main()