#!/usr/bin/env python3
"""
Debug script for the page builder functionality.
This provides more detailed diagnostics than the regular verification script.
"""

import os
import sys
import logging
import importlib
import json
import traceback
from pathlib import Path
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
import uuid
from datetime import datetime

# Configure logging with more detailed format
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s.%(msecs)03d %(levelname)s %(name)s - %(message)s',
                   datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('page_builder_debug')

def check_file_exists(file_path):
    """Check if a file exists and return its details."""
    path = Path(file_path)
    if path.exists():
        file_info = {
            "exists": True,
            "size": path.stat().st_size,
            "last_modified": path.stat().st_mtime,
            "is_empty": path.stat().st_size == 0
        }
        
        # Check if it's readable
        try:
            with open(path, 'r') as f:
                sample_content = f.read(100)
                file_info["readable"] = True
                file_info["sample"] = sample_content
        except Exception as e:
            file_info["readable"] = False
            file_info["error"] = str(e)
            
        return file_info
    else:
        return {"exists": False}

def check_import(module_name, verbose=False):
    """Check if a module can be imported and provide detailed diagnostics."""
    try:
        module = importlib.import_module(module_name)
        if verbose:
            module_attrs = dir(module)
            logger.info(f"✅ Successfully imported {module_name} with attributes: {', '.join(attr for attr in module_attrs if not attr.startswith('_'))}")
        else:
            logger.info(f"✅ Successfully imported {module_name}")
        return {"success": True, "module": module}
    except ImportError as e:
        logger.error(f"❌ Failed to import {module_name}: {str(e)}")
        # Try to find the file associated with the module
        module_path = module_name.replace('.', '/')
        possible_paths = [
            f"{module_path}.py",
            f"{module_path}/__init__.py"
        ]
        
        file_checks = {}
        for path in possible_paths:
            file_checks[path] = check_file_exists(path)
            
        # Check for package nesting issues
        parts = module_name.split('.')
        if len(parts) > 1:
            parent_module = '.'.join(parts[:-1])
            try:
                parent = importlib.import_module(parent_module)
                logger.info(f"Parent module {parent_module} exists")
                parent_check = {"success": True}
            except ImportError as parent_error:
                logger.error(f"Parent module {parent_module} import failed: {str(parent_error)}")
                parent_check = {"success": False, "error": str(parent_error)}
        else:
            parent_check = {"success": None, "note": "No parent module"}
            
        result = {
            "success": False,
            "error": str(e),
            "file_checks": file_checks,
            "parent_module_check": parent_check,
            "traceback": traceback.format_exc()
        }
        return result
    except Exception as e:
        logger.error(f"❌ Failed to import {module_name} with unexpected error: {str(e)}")
        return {"success": False, "error": str(e), "type": "unexpected", "traceback": traceback.format_exc()}

def check_database(db_url):
    """Check database connectivity and page builder tables."""
    logger.info(f"Checking database at {db_url.split('@')[1] if '@' in db_url else db_url}")
    
    try:
        # Create engine
        engine = create_engine(db_url)
        
        # Test connection
        with engine.connect() as conn:
            # Get database info
            db_info = {}
            try:
                result = conn.execute(text("SELECT version()")).scalar()
                db_info["version"] = result
                logger.info(f"Database version: {result}")
            except:
                db_info["version"] = "Unknown"
                
            # Check tables
            tables_to_check = ['pages', 'page_sections', 'content_blocks', 'page_templates']
            inspector = inspect(engine)
            all_tables = inspector.get_table_names()
            logger.info(f"Found {len(all_tables)} tables in database")
            
            table_results = {}
            for table in tables_to_check:
                exists = table in all_tables
                status = "✅" if exists else "❌"
                logger.info(f"{status} Table '{table}'")
                
                if exists:
                    # Count records
                    count_query = text(f"SELECT COUNT(*) FROM {table}")
                    count = conn.execute(count_query).scalar()
                    logger.info(f"  - Contains {count} records")
                    
                    # Get columns
                    columns = inspector.get_columns(table)
                    column_names = [col['name'] for col in columns]
                    logger.info(f"  - Columns: {', '.join(column_names)}")
                    
                    table_results[table] = {
                        "exists": True,
                        "record_count": count,
                        "columns": column_names
                    }
                    
                    # Sample a record if there are any
                    if count > 0:
                        try:
                            sample_query = text(f"SELECT * FROM {table} LIMIT 1")
                            result = conn.execute(sample_query).fetchone()
                            sample_data = {}
                            for idx, col_name in enumerate(column_names):
                                value = result[idx]
                                # Convert non-serializable types to string
                                if isinstance(value, (datetime, uuid.UUID)):
                                    value = str(value)
                                sample_data[col_name] = value
                            table_results[table]["sample_record"] = sample_data
                        except Exception as e:
                            logger.error(f"Error getting sample record: {str(e)}")
                else:
                    table_results[table] = {"exists": False}
        
        return {
            "success": True,
            "db_info": db_info,
            "tables": table_results
        }
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "type": "database",
            "traceback": traceback.format_exc()
        }
    except Exception as e:
        logger.error(f"Unexpected error checking database: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "type": "unexpected",
            "traceback": traceback.format_exc()
        }

def check_template_files():
    """Check if page builder template files exist and are valid."""
    template_base = "templates/admin/pages"
    templates_to_check = [
        f"{template_base}/list.html",
        f"{template_base}/create.html",
        f"{template_base}/editor.html"
    ]
    
    results = {}
    for template_path in templates_to_check:
        logger.info(f"Checking template: {template_path}")
        file_info = check_file_exists(template_path)
        if file_info.get("exists", False):
            logger.info(f"✅ Template exists: {template_path}")
            results[template_path] = file_info
        else:
            logger.error(f"❌ Template not found: {template_path}")
            results[template_path] = {"exists": False}
            
            # Check if parent directories exist
            parent_dir = os.path.dirname(template_path)
            if not os.path.exists(parent_dir):
                logger.error(f"❌ Parent directory does not exist: {parent_dir}")
                
                # Check each level up
                parts = parent_dir.split('/')
                current_path = ""
                for part in parts:
                    current_path = os.path.join(current_path, part)
                    if os.path.exists(current_path):
                        logger.info(f"✅ Directory exists: {current_path}")
                    else:
                        logger.error(f"❌ Directory not found: {current_path}")
                        break
    
    return results

def check_static_files():
    """Check if page builder static files exist."""
    static_files_to_check = [
        "static/js/page-editor.js",
        "static/js/page-builder.js",
        "static/css/page-builder.css"
    ]
    
    results = {}
    for file_path in static_files_to_check:
        logger.info(f"Checking static file: {file_path}")
        file_info = check_file_exists(file_path)
        if file_info.get("exists", False):
            logger.info(f"✅ Static file exists: {file_path}")
            results[file_path] = file_info
        else:
            logger.warning(f"⚠️ Static file not found: {file_path}")
            results[file_path] = {"exists": False}
    
    return results

import logging
import os
import sys
from sqlalchemy import inspect
from pycommerce.core.db import engine, SessionLocal
from pycommerce.models.page_builder import Page, PageSection, ContentBlock, PageTemplate
from pycommerce.models.tenant import Tenant, TenantManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger('main')

def check_templates():
    """Check if all required template files exist."""
    logger.info("Checking template files...")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(base_dir, "templates")

    # Check admin page templates
    admin_pages_dir = os.path.join(template_dir, "admin", "pages")
    template_files = [
        os.path.join(admin_pages_dir, "list.html"),
        os.path.join(admin_pages_dir, "create.html"),
        os.path.join(admin_pages_dir, "editor.html"),
    ]

    all_exist = True
    for template in template_files:
        if os.path.exists(template):
            logger.info(f"✅ Template exists: {template}")
        else:
            logger.error(f"❌ Template missing: {template}")
            all_exist = False

    # Check AI modal
    ai_modal_path = os.path.join(template_dir, "admin", "partials", "ai_modal.html")
    if os.path.exists(ai_modal_path):
        logger.info(f"✅ AI modal template exists: {ai_modal_path}")
    else:
        logger.error(f"❌ AI modal template missing: {ai_modal_path}")
        all_exist = False

    return all_exist

def check_database_tables():
    """Check if all required database tables exist and have records."""
    logger.info("Checking database tables...")

    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    required_tables = ['pages', 'page_sections', 'content_blocks', 'page_templates']
    missing_tables = [table for table in required_tables if table not in existing_tables]

    if missing_tables:
        logger.error(f"❌ Missing tables: {missing_tables}")
        return False

    logger.info(f"✅ All required tables exist: {required_tables}")

    # Check record counts
    session = SessionLocal()
    try:
        pages_count = session.query(Page).count()
        sections_count = session.query(PageSection).count()
        blocks_count = session.query(ContentBlock).count()
        templates_count = session.query(PageTemplate).count()

        logger.info(f"Pages count: {pages_count}")
        logger.info(f"Sections count: {sections_count}")
        logger.info(f"Blocks count: {blocks_count}")
        logger.info(f"Templates count: {templates_count}")

        # Check if there's at least one page template
        if templates_count == 0:
            logger.warning("⚠️ No page templates found. This will prevent creating new pages.")
    except Exception as e:
        logger.error(f"❌ Error querying tables: {str(e)}")
        return False
    finally:
        session.close()

    return True

def check_routes_setup():
    """Check if page builder routes are properly set up."""
    logger.info("Checking routes setup...")

    routes_file = os.path.join("routes", "admin", "page_builder.py")

    if not os.path.exists(routes_file):
        logger.error(f"❌ Page builder routes file not found: {routes_file}")
        return False

    logger.info(f"✅ Page builder routes file exists: {routes_file}")

    try:
        # Import the routes module to check if it works
        import importlib.util
        spec = importlib.util.spec_from_file_location("page_builder", routes_file)
        page_builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(page_builder)

        logger.info("✅ Page builder routes module imported successfully")

        # Check if the setup_routes function exists
        if hasattr(page_builder, "setup_routes"):
            logger.info("✅ setup_routes function exists")

            # Check if router is defined
            if hasattr(page_builder, "router"):
                logger.info("✅ router object exists")
            else:
                logger.error("❌ router object not found in page_builder module")
                return False
        else:
            logger.error("❌ setup_routes function not found in page_builder module")
            return False
    except Exception as e:
        logger.error(f"❌ Error importing page_builder module: {str(e)}")
        return False

    return True

def check_js_files():
    """Check if required JavaScript files exist."""
    logger.info("Checking JavaScript files...")

    js_files = [
        os.path.join("static", "js", "page-builder.js"),
        os.path.join("static", "js", "page-editor.js"),
        os.path.join("static", "js", "add-debug-button.js"),
    ]

    all_exist = True
    for js_file in js_files:
        if os.path.exists(js_file):
            logger.info(f"✅ JavaScript file exists: {js_file}")
        else:
            logger.warning(f"⚠️ JavaScript file missing: {js_file}")
            all_exist = False

    return all_exist

def check_ai_config():
    """Check if AI configuration is properly set up."""
    logger.info("Checking AI configuration...")

    # Check if AI configuration files exist
    ai_init = os.path.join("pycommerce", "plugins", "ai", "__init__.py")
    ai_config = os.path.join("pycommerce", "plugins", "ai", "config.py")
    ai_providers = os.path.join("pycommerce", "plugins", "ai", "providers.py")

    all_exist = True
    for file_path in [ai_init, ai_config, ai_providers]:
        if os.path.exists(file_path):
            logger.info(f"✅ AI config file exists: {file_path}")
        else:
            logger.error(f"❌ AI config file missing: {file_path}")
            all_exist = False

    return all_exist

def create_test_template():
    """Create a test page template if none exists."""
    logger.info("Checking for page templates...")

    session = SessionLocal()
    try:
        templates_count = session.query(PageTemplate).count()

        if templates_count == 0:
            logger.info("Creating a default page template...")

            default_template = PageTemplate(
                name="Basic Page",
                description="A simple page with a content section",
                is_system=True,
                template_data={
                    "sections": [
                        {
                            "section_type": "content",
                            "settings": {
                                "padding": "medium",
                                "background": "white"
                            }
                        }
                    ]
                }
            )

            session.add(default_template)
            session.commit()
            logger.info("✅ Default page template created successfully")
        else:
            logger.info(f"✅ Found {templates_count} existing page templates")
    except Exception as e:
        logger.error(f"❌ Error creating default template: {str(e)}")
        session.rollback()
    finally:
        session.close()

def check_web_app_integration():
    """Check if page builder is properly integrated in web_app.py."""
    logger.info("Checking web_app.py integration...")

    web_app_file = "web_app.py"

    if not os.path.exists(web_app_file):
        logger.error(f"❌ web_app.py file not found")
        return False

    try:
        with open(web_app_file, 'r') as f:
            content = f.read()

        if "setup_page_builder_routes" in content:
            logger.info("✅ setup_page_builder_routes found in web_app.py")
        else:
            logger.error("❌ setup_page_builder_routes not found in web_app.py")
            return False

        if "page_builder_router = setup_page_builder_routes(templates)" in content:
            logger.info("✅ Page builder router initialized in web_app.py")
        else:
            logger.warning("⚠️ Page builder router initialization may be incorrect")
    except Exception as e:
        logger.error(f"❌ Error checking web_app.py: {str(e)}")
        return False

    return True

def main():
    """Main function to check page builder functionality."""
    logger.info("Starting page builder verification")

    # Run all checks
    templates_ok = check_templates()
    tables_ok = check_database_tables()
    routes_ok = check_routes_setup()
    js_ok = check_js_files()
    ai_ok = check_ai_config()
    webapp_ok = check_web_app_integration()

    # Create a test template if needed
    create_test_template()

    # Summary
    logger.info("\n=== Page Builder Verification Summary ===")
    logger.info(f"Templates: {'✅ OK' if templates_ok else '❌ Issues found'}")
    logger.info(f"Database tables: {'✅ OK' if tables_ok else '❌ Issues found'}")
    logger.info(f"Routes setup: {'✅ OK' if routes_ok else '❌ Issues found'}")
    logger.info(f"JavaScript files: {'✅ OK' if js_ok else '⚠️ Issues found'}")
    logger.info(f"AI configuration: {'✅ OK' if ai_ok else '❌ Issues found'}")
    logger.info(f"Web app integration: {'✅ OK' if webapp_ok else '❌ Issues found'}")

    if all([templates_ok, tables_ok, routes_ok, ai_ok, webapp_ok]):
        logger.info("✅ All essential checks passed. Page builder should work properly.")
        return 0
    else:
        logger.error("❌ Some checks failed. Page builder may not work correctly.")
        return 1

if __name__ == "__main__":
    sys.exit(main())