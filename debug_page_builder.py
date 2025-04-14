
"""
Script to debug page builder data in the database.
"""
import logging
from pycommerce.core.db import SessionLocal
from pycommerce.models.tenant import TenantManager
from pycommerce.models.page_builder import PageManager

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_page_data():
    """Check page data for all tenants."""
    session = SessionLocal()
    try:
        # Get managers
        tenant_manager = TenantManager(session)
        page_manager = PageManager(session)
        
        # Get all tenants
        tenants = tenant_manager.get_all()
        print(f"Found {len(tenants)} tenants")
        
        # Check pages for each tenant
        for tenant in tenants:
            print(f"Tenant: {tenant.name} (slug: {tenant.slug})")
            try:
                pages = page_manager.list_by_tenant(str(tenant.id), include_unpublished=True)
                print(f"  Pages: {len(pages)}")
                
                # Print details for each page
                for page in pages:
                    print(f"    - Page: {page.title} (slug: {page.slug}, published: {page.is_published})")
            except Exception as e:
                print(f"  Error listing pages: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    debug_page_data()
