#!/usr/bin/env python3
"""
Create test media files with different sharing levels.

This script creates sample media files for testing the media sharing functionality.
It generates simple SVG images with different shapes and colors for each tenant,
and assigns different sharing levels to them.
"""
import os
import sys
import logging
import uuid
import random
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from pycommerce.services.media_service import MediaService
    from pycommerce.models.tenant import TenantManager
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    sys.exit(1)

def create_test_media_files():
    """
    Create test media files for each tenant with different sharing levels.
    """
    logger.info("Starting test media file creation")
    
    media_service = MediaService()
    tenant_manager = TenantManager()
    
    # Ensure static media directories exist
    uploads_dir = os.path.join(project_root, 'static', 'media', 'uploads')
    generated_dir = os.path.join(project_root, 'static', 'media', 'generated')
    
    os.makedirs(uploads_dir, exist_ok=True)
    os.makedirs(generated_dir, exist_ok=True)
    
    # Get all tenants
    tenants = tenant_manager.get_all()
    if not tenants:
        logger.error("No tenants found")
        return
    
    # Common shapes for SVG generation
    shapes = ['circle', 'rect', 'ellipse', 'polygon']
    colors = ['#ff5733', '#33ff57', '#3357ff', '#f3ff33', '#ff33f3', '#33fff3']
    
    # Store count of created files
    created_count = 0
    
    # Create media files for each tenant
    for tenant in tenants:
        tenant_id = str(tenant.id)
        logger.info(f"Creating media for tenant: {tenant.name} ({tenant_id})")
        
        # Create 3 files with different sharing levels for this tenant
        sharing_levels = ['store', 'my_stores', 'community']
        
        for sharing_level in sharing_levels:
            # Generate a unique filename
            filename = f"{tenant.slug}_{sharing_level}_{uuid.uuid4()}.svg"
            filepath = os.path.join(uploads_dir, filename)
            
            # Create an SVG image
            shape = random.choice(shapes)
            color = random.choice(colors)
            
            svg_content = create_svg_image(shape, color, tenant.name, sharing_level)
            
            # Save SVG file
            with open(filepath, 'w') as f:
                f.write(svg_content)
            
            # Determine if image is public based on sharing level
            is_public = sharing_level == 'community'
            
            # Create metadata
            meta_data = {
                'sharing_level': sharing_level,
                'creation_date': datetime.now().isoformat(),
                'test_image': True,
                'tenant_name': tenant.name
            }
            
            # Create media record
            try:
                media_data = {
                    "tenant_id": uuid.UUID(tenant_id),
                    "filename": f"{tenant.slug}_{sharing_level}_{uuid.uuid4()}.svg",
                    "original_filename": filename,
                    "file_path": filepath,
                    "file_type": "image/svg+xml",
                    "file_size": len(svg_content),
                    "description": f"This is a test image with {sharing_level} sharing level for tenant {tenant.name}",
                    "is_public": is_public,
                    "meta_data": meta_data
                }
                
                media = media_service.media_manager.create(media_data)
                if media:
                    created_count += 1
                    logger.info(f"Created media for tenant {tenant.name} with sharing level {sharing_level}")
                else:
                    logger.warning(f"Failed to create media for tenant {tenant.name}")
            except Exception as e:
                logger.error(f"Error creating media for tenant {tenant.name}: {str(e)}")
    
    logger.info(f"Finished creating test media files. Created {created_count} files.")
    return created_count

def create_svg_image(shape, color, tenant_name, sharing_level):
    """Create a simple SVG image with the given shape and color."""
    svg_start = f'<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">'
    svg_end = '</svg>'
    
    # Create background
    background = f'<rect width="200" height="200" fill="#f0f0f0" />'
    
    # Create shape
    shape_element = ''
    if shape == 'circle':
        shape_element = f'<circle cx="100" cy="100" r="80" fill="{color}" />'
    elif shape == 'rect':
        shape_element = f'<rect x="20" y="20" width="160" height="160" fill="{color}" />'
    elif shape == 'ellipse':
        shape_element = f'<ellipse cx="100" cy="100" rx="80" ry="60" fill="{color}" />'
    elif shape == 'polygon':
        shape_element = f'<polygon points="100,20 180,180 20,180" fill="{color}" />'
    
    # Add text
    text_elements = [
        f'<text x="100" y="100" font-family="Arial" font-size="16" text-anchor="middle" fill="black">{tenant_name}</text>',
        f'<text x="100" y="125" font-family="Arial" font-size="14" text-anchor="middle" fill="black">{sharing_level}</text>'
    ]
    
    # Combine all elements
    svg_content = svg_start + background + shape_element + ''.join(text_elements) + svg_end
    return svg_content

if __name__ == "__main__":
    created = create_test_media_files()
    print(f"Test media creation complete!")
    print(f"Created {created} test media files with different sharing levels.")
    print("Refresh the media page to see the new files.")