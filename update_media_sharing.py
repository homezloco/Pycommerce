#!/usr/bin/env python3
"""
Update media sharing levels for testing.

This script updates existing media files with different sharing levels for testing purposes.
It assigns sharing levels (store, my_stores, community) to media files randomly.
"""
import os
import random
import logging
import sys
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

def update_media_sharing_levels():
    """
    Update media files with different sharing levels.
    Assigns 'store', 'my_stores', or 'community' randomly to existing media.
    """
    logger.info("Starting media sharing level update")
    
    media_service = MediaService()
    tenant_manager = TenantManager()
    
    # Get all tenants
    tenants = tenant_manager.get_all()
    if not tenants:
        logger.error("No tenants found")
        return
    
    updated_count = 0
    total_count = 0
    
    # Process media files for each tenant
    for tenant in tenants:
        tenant_id = str(tenant.id)
        logger.info(f"Processing media for tenant: {tenant.name} ({tenant_id})")
        
        # Get all media for this tenant
        media_files = media_service.list_media(tenant_id=tenant_id)
        total_count += len(media_files)
        
        # Update each media file with a random sharing level
        for media in media_files:
            try:
                # Choose a random sharing level (store, my_stores, community)
                sharing_level = random.choice(["store", "my_stores", "community"])
                
                # Set is_public based on sharing level
                is_public = sharing_level == "community"
                
                # Get existing metadata or create new
                meta_data = getattr(media, 'meta_data', {}) or {}
                if meta_data is None:
                    meta_data = {}
                
                # Update metadata with sharing level
                meta_data["sharing_level"] = sharing_level
                meta_data["updated_at"] = datetime.now().isoformat()
                
                # Update the media record
                result = media_service.update_media(
                    str(media.id),
                    is_public=is_public,
                    meta_data=meta_data
                )
                
                if result:
                    updated_count += 1
                    logger.info(f"Updated media {media.id}: set sharing level to {sharing_level}")
                else:
                    logger.warning(f"Failed to update media {media.id}")
                    
            except Exception as e:
                logger.error(f"Error updating media {media.id}: {str(e)}")
    
    logger.info(f"Finished updating media sharing levels. Updated {updated_count} of {total_count} files.")
    return updated_count, total_count

if __name__ == "__main__":
    updated, total = update_media_sharing_levels()
    print(f"Media sharing levels update complete!")
    print(f"Updated {updated} of {total} media files with random sharing levels.")
    print("Refresh the media page to see the changes.")