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
import datetime
import traceback
from pathlib import Path
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
import uuid

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
                                if isinstance(value, (datetime.datetime, uuid.UUID)):
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

def run_debug():
    """Run the full page builder debugging process."""
    logger.info("Starting page builder advanced diagnostic")

    results = {}

    # Get database URL from environment or use default
    database_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/pycommerce')

    # Check database connection and tables
    logger.info("Checking database configuration...")
    results["database"] = check_database(database_url)

    # Check template files
    logger.info("Checking template files...")
    results["templates"] = check_template_files()

    # Check static files
    logger.info("Checking static files...")
    results["static_files"] = check_static_files()

    # Check imports for key components
    logger.info("Checking imports for page builder components...")
    results["imports"] = {}

    import_checks = [
        "routes.admin.page_builder",
        "pycommerce.models.page_builder",
        "routes.admin.ai_content",
        "pycommerce.models.tenant",
        "pycommerce.services.wysiwyg_service"
    ]

    for module_name in import_checks:
        results["imports"][module_name] = check_import(module_name, verbose=True)

    # Check if we can load the model classes
    logger.info("Checking model classes...")
    try:
        from pycommerce.models.page_builder import Page, PageSection, ContentBlock, PageTemplate
        results["model_classes"] = {
            "success": True,
            "classes": ["Page", "PageSection", "ContentBlock", "PageTemplate"]
        }
        logger.info("✅ Successfully imported model classes")
    except Exception as e:
        results["model_classes"] = {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        logger.error(f"❌ Failed to import model classes: {str(e)}")

    # Save results to file
    with open("page_builder_debug_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info("Debug results saved to page_builder_debug_results.json")

    # Print summary
    success_count = sum(1 for result in results["imports"].values() if result.get("success", False))
    logger.info(f"Import checks: {success_count}/{len(results['imports'])} successful")

    if results["database"]["success"]:
        table_check = results["database"]["tables"]
        table_success_count = sum(1 for table_info in table_check.values() if table_info.get("exists", False))
        logger.info(f"Table checks: {table_success_count}/{len(table_check)} tables exist")

    template_success_count = sum(1 for template_info in results["templates"].values() if template_info.get("exists", False))
    logger.info(f"Template checks: {template_success_count}/{len(results['templates'])} templates exist")

    static_success_count = sum(1 for file_info in results["static_files"].values() if file_info.get("exists", False))
    logger.info(f"Static file checks: {static_success_count}/{len(results['static_files'])} files exist")

    logger.info("Page builder diagnostics completed")

    # Notify if there are any critical issues
    if not results.get("model_classes", {}).get("success", False):
        logger.error("❌ CRITICAL: Unable to load model classes")

    if not results["database"].get("success", False):
        logger.error("❌ CRITICAL: Database connection failed")
    else:
        missing_tables = [table for table, info in results["database"]["tables"].items() if not info.get("exists", False)]
        if missing_tables:
            logger.error(f"❌ CRITICAL: Missing tables: {', '.join(missing_tables)}")

    return results

if __name__ == "__main__":
    run_debug()