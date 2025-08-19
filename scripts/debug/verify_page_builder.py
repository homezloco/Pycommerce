import logging
import os
import json
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
)

logger = logging.getLogger('main')

def verify_page_builder():
    """Verify page builder dependencies and configuration."""
    logger.info("Starting page builder verification")

    # Check for required template files
    template_files = [
        'templates/admin/pages/list.html',
        'templates/admin/pages/create.html',
        'templates/admin/pages/editor.html',
    ]

    for file_path in template_files:
        if os.path.exists(file_path):
            logger.info(f"✅ Template file exists: {file_path}")
        else:
            logger.error(f"❌ Missing template file: {file_path}")

    # Check for required JavaScript files
    js_files = [
        'static/js/page-builder.js',
        'static/js/page-editor.js',
        'static/js/quill-integration.js',
    ]

    for file_path in js_files:
        if os.path.exists(file_path):
            logger.info(f"✅ JavaScript file exists: {file_path}")
        else:
            logger.warning(f"⚠️ Missing JavaScript file: {file_path}")

    # Check Quill integration
    check_quill_integration()

    # Check for required routes in page_builder.py
    check_page_builder_routes()

    logger.info("Page builder verification complete")

def check_quill_integration():
    """Check Quill integration in templates."""
    logger.info("Checking Quill integration...")

    create_template = os.path.join("templates", "admin", "pages", "create.html")
    if not os.path.exists(create_template):
        logger.error(f"❌ Template file not found: {create_template}")
        return False

    try:
        with open(create_template, 'r') as f:
            template_content = f.read()

        # Check for Quill CDN script
        if 'quill.min.js' not in template_content:
            logger.error("❌ Quill CDN script not found in create.html")
            return False

        # Check for Quill initialization
        if 'new Quill' not in template_content and 'typeof Quill' not in template_content:
            logger.error("❌ Quill initialization not found in create.html")
            return False

        logger.info("✅ Quill integration check passed")
        return True

    except Exception as e:
        logger.error(f"❌ Error checking Quill integration: {e}")
        return False

def check_page_builder_routes():
    """Check if page_builder.py has required routes."""
    logger.info("Checking page builder routes...")

    routes_file = os.path.join("routes", "admin", "page_builder.py")

    if not os.path.exists(routes_file):
        logger.error(f"❌ Page builder routes file not found: {routes_file}")
        return False

    try:
        with open(routes_file, 'r') as f:
            routes_content = f.read()

        required_routes = [
            ("@router.get('/pages'", "@router.get(\"/pages\""),
            ("@router.get('/pages/create'", "@router.get(\"/pages/create\""), 
            ("@router.post('/pages/create'", "@router.post(\"/pages/create\""),
            ("@router.get('/pages/edit/{page_id}'", "@router.get(\"/pages/edit/{page_id}\"")
        ]

        for route_options in required_routes:
            if not any(option in routes_content for option in route_options):
                logger.error(f"❌ Required route not found: {route_options[0]}")
                return False

        logger.info("✅ All required page builder routes found")
        return True

    except Exception as e:
        logger.error(f"❌ Error checking page builder routes: {e}")
        return False

if __name__ == "__main__":
    verify_page_builder()