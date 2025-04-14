
import logging
import os
import sys
import json
from sqlalchemy import inspect
from pprint import pformat

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__main__)

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Import from pycommerce
    from pycommerce.core.db import engine, SessionLocal
    from pycommerce.models.tenant import TenantManager, Tenant
    from pycommerce.models.page_builder import PageManager, Page
    
    # Check if the templates directory exists
    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
    admin_pages_dir = os.path.join(templates_dir, "admin", "pages")
    
    logger.info(f"Templates directory exists: {os.path.exists(templates_dir)}")
    logger.info(f"Admin pages directory exists: {os.path.exists(admin_pages_dir)}")

    # Check if the template files exist
    list_template = os.path.join(admin_pages_dir, "list.html")
    create_template = os.path.join(admin_pages_dir, "create.html")
    editor_template = os.path.join(admin_pages_dir, "editor.html")
    
    logger.info(f"List template exists: {os.path.exists(list_template)}")
    logger.info(f"Create template exists: {os.path.exists(create_template)}")
    logger.info(f"Editor template exists: {os.path.exists(editor_template)}")
    
    # Examine the database structure
    inspector = inspect(engine)
    
    # 1. Check if the pages table exists
    tables = inspector.get_table_names()
    logger.info(f"Tables in database: {tables}")
    
    # 2. Check if pages table has expected columns
    if 'pages' in tables:
        logger.info("Pages table exists: True")
        columns = [column['name'] for column in inspector.get_columns('pages')]
        logger.info(f"Columns in pages table: {columns}")
    else:
        logger.info("Pages table exists: False")
    
    # 3. Examine route handling logic
    session = SessionLocal()
    try:
        # Initialize managers
        tenant_manager = TenantManager(session)
        page_manager = PageManager(session)
        
        # Get all tenants
        tenants = tenant_manager.get_all()
        logger.info(f"Found {len(tenants)} tenants")
        
        for tenant in tenants:
            logger.info(f"Tenant: {tenant.name} (slug: {tenant.slug})")
            
            # Get pages for this tenant
            try:
                pages = page_manager.list_by_tenant(str(tenant.id), include_unpublished=True)
                logger.info(f"  Pages: {len(pages)}")
                
                for page in pages:
                    logger.info(f"    - Page: {page.title} (slug: {page.slug}, published: {page.is_published})")
            except Exception as e:
                logger.error(f"  Error getting pages for tenant {tenant.id}: {str(e)}")
                
        # 4. Diagnose tenant selection mechanism
        tenant_slugs = [t.slug for t in tenants]
        selected_tenant = tenant_slugs[0] if tenant_slugs else None
        
        if selected_tenant:
            logger.info(f"Selected tenant: {selected_tenant}")
            tenant = tenant_manager.get_by_slug(selected_tenant)
            
            if tenant:
                logger.info(f"Got tenant by slug: {tenant.name} (ID: {tenant.id})")
                
                # Check if we can get pages for this tenant
                try:
                    pages = page_manager.list_by_tenant(str(tenant.id), include_unpublished=True)
                    logger.info(f"Found {len(pages)} pages for tenant {tenant.id}")
                    
                    # Check the data structure of a page
                    if pages:
                        sample_page = pages[0]
                        logger.info("Sample page data:")
                        page_data = {
                            "id": str(sample_page.id),
                            "title": sample_page.title,
                            "slug": sample_page.slug,
                            "is_published": sample_page.is_published,
                            "has_layout_data": hasattr(sample_page, "layout_data") and sample_page.layout_data is not None
                        }
                        logger.info(pformat(page_data))
                except Exception as e:
                    logger.error(f"Error listing pages: {str(e)}")
            else:
                logger.error(f"No tenant found with slug: {selected_tenant}")
        else:
            logger.warning("No tenants found")
            
        # 5. Check list.html template context requirements 
        logger.info("Checking template context requirements for admin/pages/list.html")
        required_context = ["tenant", "tenants", "pages", "selected_tenant"]
        
        for item in required_context:
            if item == "tenant":
                logger.info(f"{item}: {'Present' if tenant else 'Missing'}")
            elif item == "tenants":
                logger.info(f"{item}: {'Present' if tenants else 'Missing'}")
            elif item == "pages":
                # This would be handled in the actual request context
                logger.info(f"{item}: Query logic appears functional")
            elif item == "selected_tenant":
                logger.info(f"{item}: {'Present' if selected_tenant else 'Missing'}")
                
    except Exception as e:
        logger.error(f"Error examining route handling logic: {str(e)}")
    finally:
        session.close()
        
    # 6. Try to access the debug endpoint directly 
    from fastapi import Request
    from starlette.datastructures import URL, Headers, QueryParams
    
    # Create a mock request
    mock_request = Request({
        "type": "http",
        "path": "/admin/debug-pages",
        "headers": Headers({"host": "localhost"}).raw,
        "query_string": b"",
    })
    mock_request._url = URL("/admin/debug-pages")
    
    # Import the debug_pages function
    sys.path.append("routes/admin")
    from routes.admin.page_builder import debug_pages
    
    logger.info("Attempting to call debug_pages endpoint directly")
    
    try:
        import asyncio
        # If we're in an async environment, use this
        result = asyncio.run(debug_pages(mock_request))
        logger.info(f"Debug endpoint result type: {type(result)}")
        logger.info(f"Debug result: {result}")
    except Exception as e:
        logger.error(f"Error calling debug_pages directly: {str(e)}")
        
except Exception as e:
    logger.error(f"Error in debug script: {str(e)}")
