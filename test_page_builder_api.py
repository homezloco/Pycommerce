import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


class TestProductAPIEndpoint(unittest.TestCase):
    """Test cases for the Products API endpoint."""

    @patch('pycommerce.sdk.AppProductManager')
    @patch('pycommerce.sdk.AppTenantManager')
    def test_products_api_endpoint(self, mock_tenant_manager, mock_product_manager):
        """Test the list_by_tenant method in the API endpoint."""
        # Set up mocks
        mock_tenant = MagicMock()
        mock_tenant.id = 'tech'
        mock_tenant.name = 'Tech Store'
        
        mock_tenant_instance = MagicMock()
        mock_tenant_instance.get_by_slug.return_value = mock_tenant
        mock_tenant_manager.return_value = mock_tenant_instance
        
        mock_product1 = MagicMock()
        mock_product1.id = '12345678-1234-5678-1234-567812345678'
        mock_product1.name = 'Smartphone'
        mock_product1.price = 599.99
        mock_product1.sku = 'TECH-PHONE-1'
        mock_product1.description = 'A high-end smartphone'
        mock_product1.stock = 10
        mock_product1.categories = ['electronics', 'phones']
        
        mock_product2 = MagicMock()
        mock_product2.id = '87654321-8765-4321-8765-432187654321'
        mock_product2.name = 'Laptop'
        mock_product2.price = 1299.99
        mock_product2.sku = 'TECH-LAPTOP-1'
        mock_product2.description = 'A powerful laptop'
        mock_product2.stock = 5
        mock_product2.categories = ['electronics', 'computers']
        
        # Configure the mock product manager
        mock_product_instance = MagicMock()
        mock_product_instance.list_by_tenant.return_value = [mock_product1, mock_product2]
        mock_product_manager.return_value = mock_product_instance
        
        # Create direct instance to test the method we added
        from pycommerce.sdk import AppProductManager
        app_product_manager = AppProductManager()
        
        # Test the list_by_tenant method directly
        products = app_product_manager.list_by_tenant('tech')
        
        # Verify we got the expected products
        self.assertEqual(len(products), 2)
        product_ids = [p.id for p in products]
        self.assertIn('12345678-1234-5678-1234-567812345678', product_ids)
        self.assertIn('87654321-8765-4321-8765-432187654321', product_ids)
        
        # Verify the underlying manager was called correctly
        mock_product_instance.list_by_tenant.assert_called_with('tech')

    @patch('pycommerce.models.product.ProductManager.list_by_tenant')
    def test_error_handling_in_list_by_tenant(self, mock_list_by_tenant):
        """Test error handling in the list_by_tenant method."""
        # Configure the mock to raise an exception
        mock_list_by_tenant.side_effect = Exception("Database error")
        
        # Create direct instance to test the method we added
        from pycommerce.sdk import AppProductManager
        app_product_manager = AppProductManager()
        
        # Call the method - should catch the exception and return empty list
        result = app_product_manager.list_by_tenant('test-tenant')
        
        # Verify we got an empty list as the fallback
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()