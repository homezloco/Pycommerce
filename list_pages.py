#!/usr/bin/env python3
"""List all pages for all tenants"""

from pycommerce.models.page_builder import PageManager
from pycommerce.models.tenant import TenantManager

def list_tenant_pages():
    """List all pages for all tenants"""
    tenant_manager = TenantManager()
    page_manager = PageManager()
    
    tenants = tenant_manager.get_all()
    
    for tenant in tenants:
        print(f'Pages for tenant {tenant.name} (slug: {tenant.slug}):')
        pages = page_manager.list_by_tenant(str(tenant.id), include_unpublished=True)
        
        if not pages or len(pages) == 0:
            print("  No pages found")
        else:
            for page in pages:
                print(f'- {page.title} (slug: {page.slug}, published: {page.is_published})')
        
        print('---')

if __name__ == "__main__":
    list_tenant_pages()