
"""
Debug script to check frontend template and JavaScript issues in the page builder.
"""
import logging
import os
import sys
from fastapi.templating import Jinja2Templates
from jinja2 import TemplateError

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_template_syntax():
    """Check template syntax for common errors."""
    logger.info("Checking template syntax...")
    
    # Get paths
    base_dir = os.getcwd()
    template_dir = os.path.join(base_dir, "templates")
    
    # Initialize Jinja2 environment
    try:
        templates = Jinja2Templates(directory=template_dir)
        logger.info("✅ Jinja2 templates initialization successful")
    except Exception as e:
        logger.error(f"❌ Error initializing Jinja2 templates: {str(e)}")
        return False
    
    # Try to parse critical templates
    critical_templates = [
        "admin/pages/create.html",
        "admin/pages/editor.html",
        "admin/pages/list.html",
        "store/page.html"
    ]
    
    all_valid = True
    for template_name in critical_templates:
        try:
            # Just get the template to check syntax
            template_path = os.path.join(template_dir, template_name)
            if not os.path.exists(template_path):
                logger.error(f"❌ Template file not found: {template_path}")
                all_valid = False
                continue
                
            with open(template_path, 'r') as f:
                template_content = f.read()
                
            # Check for unbalanced tags
            if template_content.count('{% block') != template_content.count('{% endblock'):
                logger.error(f"❌ Unbalanced block tags in {template_name}")
                all_valid = False
                
            if template_content.count('{% if') != template_content.count('{% endif'):
                logger.error(f"❌ Unbalanced if tags in {template_name}")
                all_valid = False
                
            if template_content.count('{% for') != template_content.count('{% endfor'):
                logger.error(f"❌ Unbalanced for tags in {template_name}")
                all_valid = False
                
            # Check for tinymce initialization
            if 'tinymce.init' in template_content:
                logger.info(f"✅ TinyMCE initialization found in {template_name}")
                
            logger.info(f"✅ Template syntax check passed: {template_name}")
            
        except Exception as e:
            logger.error(f"❌ Error checking template {template_name}: {str(e)}")
            all_valid = False
            
    return all_valid

def check_js_files():
    """Check JavaScript files for common errors."""
    logger.info("Checking JavaScript files...")
    
    js_files = [
        os.path.join("static", "js", "tinymce-ai.js"),
        os.path.join("static", "js", "quill-integration.js")
    ]
    
    all_valid = True
    for js_file in js_files:
        if not os.path.exists(js_file):
            logger.error(f"❌ JavaScript file not found: {js_file}")
            all_valid = False
            continue
            
        try:
            with open(js_file, 'r') as f:
                js_content = f.read()
                
            # Check for unbalanced braces
            if js_content.count('{') != js_content.count('}'):
                logger.error(f"❌ Unbalanced braces in {js_file}")
                all_valid = False
                
            # Check for unbalanced parentheses
            if js_content.count('(') != js_content.count(')'):
                logger.error(f"❌ Unbalanced parentheses in {js_file}")
                all_valid = False
                
            logger.info(f"✅ JavaScript syntax check passed: {js_file}")
            
        except Exception as e:
            logger.error(f"❌ Error checking JavaScript file {js_file}: {str(e)}")
            all_valid = False
            
    return all_valid

def check_tinymce_integration():
    """Check TinyMCE integration in templates."""
    logger.info("Checking TinyMCE integration...")
    
    create_template = os.path.join("templates", "admin", "pages", "create.html")
    if not os.path.exists(create_template):
        logger.error(f"❌ Template file not found: {create_template}")
        return False
        
    try:
        with open(create_template, 'r') as f:
            template_content = f.read()
            
        # Check for TinyMCE CDN script
        if 'tinymce.min.js' not in template_content:
            logger.error("❌ TinyMCE CDN script not found in create.html")
            return False
            
        # Check for TinyMCE initialization
        if 'tinymce.init' not in template_content:
            logger.error("❌ TinyMCE initialization not found in create.html")
            return False
            
        logger.info("✅ TinyMCE integration check passed")
        return True
            
    except Exception as e:
        logger.error(f"❌ Error checking TinyMCE integration: {str(e)}")
        return False

def main():
    """Run all frontend checks."""
    logger.info("Starting frontend verification...")
    
    # Record results
    templates_ok = check_template_syntax()
    js_ok = check_js_files()
    tinymce_ok = check_tinymce_integration()
    
    # Report overall status
    logger.info("\n=== Frontend Verification Results ===")
    logger.info(f"Template syntax check: {'✅ PASS' if templates_ok else '❌ FAIL'}")
    logger.info(f"JavaScript syntax check: {'✅ PASS' if js_ok else '❌ FAIL'}")
    logger.info(f"TinyMCE integration check: {'✅ PASS' if tinymce_ok else '❌ FAIL'}")
    
    if templates_ok and js_ok and tinymce_ok:
        logger.info("✅ All frontend components are correctly set up")
        return 0
    else:
        missing = []
        if not templates_ok:
            missing.append("template syntax")
        if not js_ok:
            missing.append("JavaScript syntax")
        if not tinymce_ok:
            missing.append("TinyMCE integration")
        
        logger.error(f"❌ Frontend verification failed: issues with {', '.join(missing)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
