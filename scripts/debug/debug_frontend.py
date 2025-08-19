
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
                
            # Check for Quill initialization
            if 'Quill' in template_content or 'quill' in template_content:
                logger.info(f"✅ Quill initialization found in {template_name}")
                
            logger.info(f"✅ Template syntax check passed: {template_name}")
            
        except Exception as e:
            logger.error(f"❌ Error checking template {template_name}: {str(e)}")
            all_valid = False
            
    return all_valid

def check_js_files():
    """Check JavaScript files for common errors."""
    logger.info("Checking JavaScript files...")
    
    js_files = [
        os.path.join("static", "js", "quill-integration.js"),
        os.path.join("static", "js", "page-builder.js")
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

def check_quill_integration():
    """Check Quill integration in templates."""
    logger.info("Checking Quill integration...")
    
    editor_template = os.path.join("templates", "admin", "pages", "editor.html")
    if not os.path.exists(editor_template):
        logger.error(f"❌ Template file not found: {editor_template}")
        return False
        
    try:
        with open(editor_template, 'r') as f:
            template_content = f.read()
            
        # Check for Quill CDN script
        if 'quill.min.js' not in template_content and 'cdn.quilljs.com' not in template_content:
            logger.error("❌ Quill CDN script not found in editor.html")
            return False
            
        # Check for Quill initialization
        if 'new Quill' not in template_content and 'quill-editor' not in template_content:
            logger.error("❌ Quill initialization not found in editor.html")
            return False
            
        logger.info("✅ Quill integration check passed")
        return True
            
    except Exception as e:
        logger.error(f"❌ Error checking Quill integration: {str(e)}")
        return False

def main():
    """Run all frontend checks."""
    logger.info("Starting frontend verification...")
    
    # Record results
    templates_ok = check_template_syntax()
    js_ok = check_js_files()
    quill_ok = check_quill_integration()
    
    # Report overall status
    logger.info("\n=== Frontend Verification Results ===")
    logger.info(f"Template syntax check: {'✅ PASS' if templates_ok else '❌ FAIL'}")
    logger.info(f"JavaScript syntax check: {'✅ PASS' if js_ok else '❌ FAIL'}")
    logger.info(f"Quill integration check: {'✅ PASS' if quill_ok else '❌ FAIL'}")
    
    if templates_ok and js_ok and quill_ok:
        logger.info("✅ All frontend components are correctly set up")
        return 0
    else:
        missing = []
        if not templates_ok:
            missing.append("template syntax")
        if not js_ok:
            missing.append("JavaScript syntax")
        if not quill_ok:
            missing.append("Quill integration")
        
        logger.error(f"❌ Frontend verification failed: issues with {', '.join(missing)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
