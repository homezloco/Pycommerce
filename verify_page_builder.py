
"""
Verification script for page builder.

This script checks if all the necessary components for page builder are correctly set up.
"""
import logging
import os
import sys
from sqlalchemy import inspect

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_templates():
    """Verify if all required templates for page builder exist."""
    logger.info("Verifying page builder templates...")
    
    # Get paths
    base_dir = os.getcwd()
    template_dir = os.path.join(base_dir, "templates")
    
    # Admin pages templates
    page_builder_templates = [
        os.path.join(template_dir, "admin", "pages", "list.html"),
        os.path.join(template_dir, "admin", "pages", "create.html"),
        os.path.join(template_dir, "admin", "pages", "editor.html")
    ]
    
    # Check if templates exist
    all_templates_exist = True
    for path in page_builder_templates:
        if os.path.exists(path):
            logger.info(f"✅ Template found: {path}")
        else:
            all_templates_exist = False
            logger.error(f"❌ Template NOT found: {path}")
    
    # If not all templates exist, provide more info
    if not all_templates_exist:
        logger.info("Checking template directory structure...")
        if os.path.exists(template_dir):
            logger.info(f"Contents of templates directory: {os.listdir(template_dir)}")
            admin_dir = os.path.join(template_dir, "admin")
            if os.path.exists(admin_dir):
                logger.info(f"Contents of admin directory: {os.listdir(admin_dir)}")
                # Check for the pages directory
                pages_dir = os.path.join(admin_dir, "pages")
                if os.path.exists(pages_dir):
                    logger.info(f"Contents of pages directory: {os.listdir(pages_dir)}")
                else:
                    logger.error("Pages directory not found in admin directory")
            else:
                logger.error("Admin directory not found in templates directory")
        else:
            logger.error("Templates directory not found")
    
    return all_templates_exist

def verify_database_tables():
    """Verify if the page builder tables exist in the database."""
    logger.info("Verifying page builder database tables...")
    
    try:
        from pycommerce.core.db import engine
        
        # Get list of existing tables
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # Required page builder tables
        required_tables = ['pages', 'page_sections', 'content_blocks', 'page_templates']
        
        # Check each required table
        all_tables_exist = True
        for table in required_tables:
            if table in existing_tables:
                logger.info(f"✅ Table found: {table}")
            else:
                all_tables_exist = False
                logger.error(f"❌ Table NOT found: {table}")
        
        if not all_tables_exist:
            logger.info(f"Existing tables: {existing_tables}")
            logger.info("Consider running the page builder migration script: python run_page_builder_migration.py")
        
        # Get table counts if all tables exist
        if all_tables_exist:
            from sqlalchemy import text
            with engine.connect() as conn:
                for table in required_tables:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    logger.info(f"Table {table} has {count} records")
        
        return all_tables_exist
    
    except Exception as e:
        logger.error(f"Error verifying database tables: {str(e)}")
        return False

def verify_json_serialization():
    """Verify if UUIDs can be serialized to JSON."""
    logger.info("Testing UUID JSON serialization...")
    
    try:
        import json
        import uuid
        
        # Test serialization
        class UUIDEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, uuid.UUID):
                    return str(obj)
                return json.JSONEncoder.default(self, obj)
        
        # Create a test UUID and try to serialize it
        test_uuid = uuid.uuid4()
        logger.info(f"Test UUID: {test_uuid}")
        
        # Try direct serialization (should fail)
        try:
            direct_json = json.dumps({"id": test_uuid})
            logger.info("Direct serialization successful (unexpected)")
        except TypeError:
            logger.info("Direct serialization failed as expected - UUID is not JSON serializable")
        
        # Try with custom encoder (should succeed)
        custom_json = json.dumps({"id": test_uuid}, cls=UUIDEncoder)
        logger.info(f"Custom encoder serialization: {custom_json}")
        
        # Verify result
        if custom_json:
            logger.info("✅ UUID serialization with custom encoder works correctly")
            return True
        else:
            logger.error("❌ Failed to serialize UUID even with custom encoder")
            return False
    
    except Exception as e:
        logger.error(f"Error in JSON serialization test: {str(e)}")
        return False

def main():
    """Run all verification checks."""
    logger.info("Starting page builder verification...")
    
    # Record results
    templates_ok = verify_templates()
    tables_ok = verify_database_tables()
    json_ok = verify_json_serialization()
    
    # Report overall status
    logger.info("\n=== Page Builder Verification Results ===")
    logger.info(f"Templates verification: {'✅ PASS' if templates_ok else '❌ FAIL'}")
    logger.info(f"Database tables verification: {'✅ PASS' if tables_ok else '❌ FAIL'}")
    logger.info(f"JSON serialization verification: {'✅ PASS' if json_ok else '❌ FAIL'}")
    
    if templates_ok and tables_ok and json_ok:
        logger.info("✅ All page builder components are correctly set up")
        return 0
    else:
        missing = []
        if not templates_ok:
            missing.append("templates")
        if not tables_ok:
            missing.append("database tables")
        if not json_ok:
            missing.append("JSON serialization")
        
        logger.error(f"❌ Page builder verification failed: missing or incorrect {', '.join(missing)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
import logging
import sys
from sqlalchemy import inspect
from pycommerce.core.db import engine, SessionLocal
from pycommerce.models.tenant import TenantManager
from pycommerce.models.page_builder import PageManager

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_page_builder():
    """Verify page builder setup and data."""
    logger.info("Starting page builder verification")
    
    # Check tables
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    required_tables = ['pages', 'page_sections', 'content_blocks', 'page_templates']
    missing_tables = [table for table in required_tables if table not in tables]
    
    if missing_tables:
        logger.error(f"Missing tables: {missing_tables}")
        return False
    
    logger.info(f"All required tables exist: {', '.join(required_tables)}")
    
    # Check if there are pages in the database
    session = SessionLocal()
    try:
        # Get all tenants
        tenant_manager = TenantManager(session)
        tenants = tenant_manager.get_all()
        
        logger.info(f"Found {len(tenants)} tenants")
        
        # Check if each tenant has pages
        page_manager = PageManager(session)
        
        for tenant in tenants:
            try:
                pages = page_manager.list_by_tenant(str(tenant.id), include_unpublished=True)
                logger.info(f"Tenant '{tenant.name}' (slug: {tenant.slug}) has {len(pages)} pages")
                
                # Print page details
                for page in pages:
                    logger.info(f"  - Page: '{page.title}' (slug: {page.slug}, published: {page.is_published})")
            except Exception as e:
                logger.error(f"Error checking pages for tenant '{tenant.name}': {str(e)}")
        
        return True
    except Exception as e:
        logger.error(f"Error verifying page builder: {str(e)}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    success = verify_page_builder()
    if success:
        logger.info("Page builder verification completed successfully")
    else:
        logger.error("Page builder verification failed")
        sys.exit(1)
