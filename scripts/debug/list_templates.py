#!/usr/bin/env python3
"""List all page templates"""

import json
from pycommerce.models.page_builder import PageTemplateManager
from pycommerce.core.db import SessionLocal

def list_page_templates():
    """List all page templates"""
    session = SessionLocal()
    template_manager = PageTemplateManager(session)
    
    try:
        templates = template_manager.list_templates()
        
        print(f"Found {len(templates)} page templates:")
        for template in templates:
            print(f"\n- Template: {template.name}")
            print(f"  Description: {template.description}")
            print(f"  ID: {template.id}")
            print(f"  System template: {template.is_system}")
            
            # Pretty print template data structure
            sections = template.template_data.get("sections", [])
            print(f"  Sections: {len(sections)}")
            for i, section in enumerate(sections):
                print(f"    {i+1}. {section.get('section_type')} section")
                print(f"       Settings: {json.dumps(section.get('settings', {}), indent=2)}")
    finally:
        session.close()

if __name__ == "__main__":
    list_page_templates()