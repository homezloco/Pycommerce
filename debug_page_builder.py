
"""
Script to debug page builder data in the database.
"""
import logging
import sys
from sqlalchemy import inspect
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
        tenant_manager = TenantManager()
        tenant_manager.session = session  # Set the session directly for TenantManager
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
                    
                    # Check page sections if any
                    try:
                        if hasattr(page, 'sections') and page.sections:
                            print(f"      Sections: {len(page.sections)}")
                            for section in page.sections:
                                print(f"        - Section: {section.section_type} (position: {section.position})")
                                
                                # Check content blocks if any
                                if hasattr(section, 'blocks') and section.blocks:
                                    print(f"          Blocks: {len(section.blocks)}")
                    except Exception as section_err:
                        print(f"      Error checking sections: {str(section_err)}")
            except Exception as e:
                print(f"  Error listing pages: {str(e)}")
                
        # Check database tables to verify schema
        print("\nChecking database schema:")
        inspector = inspect(session.get_bind())
        tables = inspector.get_table_names()
        print(f"Tables in database: {tables}")
        
        # Check if pages table exists
        pages_exists = 'pages' in tables
        print(f"Pages table exists: {pages_exists}")
        
        if pages_exists:
            # Get columns in pages table
            columns = [col['name'] for col in inspector.get_columns('pages')]
            print(f"Columns in pages table: {columns}")
            
    finally:
        session.close()

if __name__ == "__main__":
    debug_page_data()
