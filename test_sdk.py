import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the SDK module
from pycommerce.sdk import AppTenantManager, AppProductManager


class TestSDK(unittest.TestCase):
    """Test cases for the SDK modules."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Patch the underlying managers for isolated testing
        self.product_manager_patcher = patch('pycommerce.sdk.ProductManager')
        self.tenant_manager_patcher = patch('pycommerce.sdk.TenantManager')
        
        # Create mock managers
        self.mock_product_manager = self.product_manager_patcher.start()
        self.mock_tenant_manager = self.tenant_manager_patcher.start()
        
        # Create SDK instances using the mocks
        self.product_sdk = AppProductManager()
        self.tenant_sdk = AppTenantManager()
    
    def tearDown(self):
        """Tear down test fixtures after each test method."""
        self.product_manager_patcher.stop()
        self.tenant_manager_patcher.stop()

    def test_product_sdk_init(self):
        """Test AppProductManager initialization."""
        # Check if ProductManager was instantiated
        self.mock_product_manager.assert_called_once()
        self.assertIsNotNone(self.product_sdk.manager)

    def test_tenant_sdk_init(self):
        """Test AppTenantManager initialization."""
        # Check if TenantManager was instantiated
        self.mock_tenant_manager.assert_called_once()
        self.assertIsNotNone(self.tenant_sdk.manager)

    def test_list_products_by_tenant(self):
        """Test getting products by tenant through the SDK."""
        # Set up mock product instance
        mock_product_instance = MagicMock()
        mock_product_instance.list_by_tenant.return_value = ['product1', 'product2']
        self.mock_product_manager.return_value = mock_product_instance
        
        # Create a new SDK instance with our configured mock
        product_sdk = AppProductManager()
        
        # Call the method we're testing
        result = product_sdk.list_by_tenant('test-tenant')
        
        # Check if underlying manager method was called with correct arguments
        mock_product_instance.list_by_tenant.assert_called_once_with('test-tenant')
        
        # Check if result matches what we expect
        self.assertEqual(result, ['product1', 'product2'])

    def test_get_tenant_by_slug(self):
        """Test getting a tenant by slug through the SDK."""
        # Set up mock tenant
        mock_tenant = MagicMock()
        mock_tenant.name = 'Test Tenant'
        mock_tenant.id = 'test-tenant-id'
        
        # Set up mock tenant instance
        mock_tenant_instance = MagicMock()
        mock_tenant_instance.get_by_slug.return_value = mock_tenant
        self.mock_tenant_manager.return_value = mock_tenant_instance
        
        # Create a new SDK instance with our configured mock
        tenant_sdk = AppTenantManager()
        
        # Call the method we're testing
        result = tenant_sdk.get_by_slug('test-tenant')
        
        # Check if underlying manager method was called with correct arguments
        mock_tenant_instance.get_by_slug.assert_called_once_with('test-tenant')
        
        # Check if result matches what we expect
        self.assertEqual(result, mock_tenant)
        self.assertEqual(result.name, 'Test Tenant')
        self.assertEqual(result.id, 'test-tenant-id')
    
    def test_error_handling_in_list_products_by_tenant(self):
        """Test error handling in the SDK when manager raises exception."""
        # Set up mock product instance to raise an exception
        mock_product_instance = MagicMock()
        mock_product_instance.list_by_tenant.side_effect = Exception("Database error")
        self.mock_product_manager.return_value = mock_product_instance
        
        # Create a new SDK instance with our configured mock
        product_sdk = AppProductManager()
        
        # Call the method we're testing - should catch the exception and return empty list
        result = product_sdk.list_by_tenant('test-tenant')
        
        # Check if result is an empty list (the fallback)
        self.assertEqual(result, [])
    
    def test_tenant_get_or_default(self):
        """Test the get_or_default method of the tenant manager."""
        # Set up mock tenant
        mock_tenant1 = MagicMock()
        mock_tenant1.name = 'Test Tenant 1'
        mock_tenant1.id = 'test-tenant-1'
        mock_tenant1.slug = 'test-tenant-1'
        
        mock_tenant2 = MagicMock()
        mock_tenant2.name = 'Test Tenant 2'
        mock_tenant2.id = 'test-tenant-2'
        mock_tenant2.slug = 'test-tenant-2'
        
        # Set up mock tenant instance
        mock_tenant_instance = MagicMock()
        # First get() call returns None (not found)
        mock_tenant_instance.get.return_value = None
        # get_by_slug also returns None
        mock_tenant_instance.get_by_slug.return_value = None
        # list() returns a list of tenants
        mock_tenant_instance.list.return_value = [mock_tenant1, mock_tenant2]
        
        self.mock_tenant_manager.return_value = mock_tenant_instance
        
        # Create a new SDK instance with our configured mock
        tenant_sdk = AppTenantManager()
        
        # Call the method we're testing
        result = tenant_sdk.get_or_default('nonexistent-tenant')
        
        # Should return the first tenant as fallback
        self.assertEqual(result, mock_tenant1)
        self.assertEqual(result.name, 'Test Tenant 1')


if __name__ == '__main__':
    unittest.main()