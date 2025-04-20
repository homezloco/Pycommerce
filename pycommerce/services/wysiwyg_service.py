
"""
WYSIWYG editor service for PyCommerce.

This module provides utilities for handling WYSIWYG editor operations,
including content processing, sanitization, and integration with the media library.
"""

import logging
import re
import uuid
import json
from typing import Dict, List, Optional, Any, Tuple

import bleach
from bs4 import BeautifulSoup

from pycommerce.services.media_service import MediaService

# Configure logging
logger = logging.getLogger(__name__)

# Allowed HTML tags and attributes for sanitization
ALLOWED_TAGS = [
    'a', 'abbr', 'acronym', 'address', 'area', 'article', 'aside', 'audio', 'b', 
    'bdi', 'bdo', 'blockquote', 'br', 'button', 'canvas', 'caption', 'cite', 'code', 
    'col', 'colgroup', 'data', 'datalist', 'dd', 'del', 'details', 'dfn', 'dialog', 
    'div', 'dl', 'dt', 'em', 'embed', 'fieldset', 'figcaption', 'figure', 'footer', 
    'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'hgroup', 'hr', 'i', 'iframe', 
    'img', 'input', 'ins', 'kbd', 'keygen', 'label', 'legend', 'li', 'main', 'map', 
    'mark', 'math', 'menu', 'menuitem', 'meter', 'nav', 'noscript', 'object', 'ol', 
    'optgroup', 'option', 'output', 'p', 'param', 'picture', 'pre', 'progress', 'q', 
    'rp', 'rt', 'ruby', 's', 'samp', 'section', 'select', 'small', 'source', 'span', 
    'strong', 'style', 'sub', 'summary', 'sup', 'svg', 'table', 'tbody', 'td', 'template', 
    'textarea', 'tfoot', 'th', 'thead', 'time', 'title', 'tr', 'track', 'u', 'ul', 
    'var', 'video', 'wbr'
]

ALLOWED_ATTRS = {
    '*': ['class', 'id', 'style', 'data-*'],
    'a': ['href', 'target', 'rel', 'download', 'title'],
    'img': ['src', 'alt', 'title', 'width', 'height', 'loading', 'srcset', 'sizes', 'data-*'],
    'iframe': ['src', 'width', 'height', 'frameborder', 'allowfullscreen', 'allow'],
    'video': ['src', 'width', 'height', 'controls', 'autoplay', 'muted', 'loop', 'poster'],
    'audio': ['src', 'controls', 'autoplay', 'muted', 'loop'],
    'source': ['src', 'type', 'srcset', 'sizes', 'media'],
    'input': ['type', 'value', 'placeholder', 'checked', 'disabled', 'readonly'],
    'button': ['type', 'disabled'],
    'ol': ['start', 'reversed', 'type'],
    'li': ['value'],
    'table': ['width', 'border', 'cellspacing', 'cellpadding'],
    'th': ['width', 'colspan', 'rowspan', 'scope'],
    'td': ['width', 'colspan', 'rowspan'],
    'time': ['datetime'],
    'meta': ['charset', 'name', 'content', 'http-equiv'],
    'link': ['href', 'rel', 'type', 'media'],
}

ALLOWED_STYLES = [
    'background', 'background-color', 'border', 'border-radius', 'color', 'display',
    'float', 'font', 'font-family', 'font-size', 'font-style', 'font-weight', 'height',
    'line-height', 'margin', 'margin-bottom', 'margin-left', 'margin-right', 'margin-top',
    'padding', 'padding-bottom', 'padding-left', 'padding-right', 'padding-top', 'text-align',
    'text-decoration', 'text-indent', 'vertical-align', 'white-space', 'width'
]


class WysiwygService:
    """Service for handling WYSIWYG editor operations."""
    
    def __init__(self):
        """Initialize the WYSIWYG service."""
        self.media_service = MediaService()
    
    def sanitize_html(self, html_content: str) -> str:
        """
        Sanitize HTML content to prevent XSS attacks.
        
        Args:
            html_content: The HTML content to sanitize
            
        Returns:
            The sanitized HTML content
        """
        try:
            # Clean the HTML with bleach
            clean_html = bleach.clean(
                html_content,
                tags=ALLOWED_TAGS,
                attributes=ALLOWED_ATTRS,
                strip=True
            )
            
            # Parse the cleaned HTML with BeautifulSoup for additional processing
            soup = BeautifulSoup(clean_html, 'html.parser')
            
            # Process styles
            for tag in soup.find_all(style=True):
                styles = tag['style']
                # Filter out disallowed styles
                allowed_style_dict = {}
                style_rules = re.findall(r'([^:;]+)\s*:\s*([^;]+)', styles)
                for prop, value in style_rules:
                    prop = prop.strip().lower()
                    if any(prop.startswith(allowed) for allowed in ALLOWED_STYLES):
                        allowed_style_dict[prop] = value.strip()
                
                # Rebuild the style attribute
                if allowed_style_dict:
                    tag['style'] = '; '.join(f"{prop}: {value}" for prop, value in allowed_style_dict.items())
                else:
                    del tag['style']
            
            # Return the sanitized HTML
            return str(soup)
        except Exception as e:
            logger.error(f"Error sanitizing HTML: {str(e)}")
            # Return the original content if sanitization fails (though this is not ideal)
            return html_content
    
    def process_editor_content(self, content: str, tenant_id: Optional[str] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Process content from the WYSIWYG editor.
        
        This method:
        1. Extracts and processes any embedded media
        2. Sanitizes the HTML content
        3. Returns the processed content and a list of any media IDs referenced
        
        Args:
            content: The HTML content from the editor
            tenant_id: Optional tenant ID for media handling
            
        Returns:
            Tuple of (processed content, list of media references)
        """
        try:
            # First, sanitize the HTML
            sanitized_content = self.sanitize_html(content)
            
            # Parse the sanitized HTML
            soup = BeautifulSoup(sanitized_content, 'html.parser')
            
            # Track media references
            media_references = []
            
            # Process images
            for img in soup.find_all('img'):
                # Check if the image has a src attribute
                if not img.get('src'):
                    continue
                
                src = img['src']
                
                # Skip external images and data URIs
                if src.startswith(('http://', 'https://', 'data:')):
                    continue
                
                # Check if this is a reference to a media item in our library
                if '/static/media/' in src:
                    # Extract the filename from the URL
                    filename = src.split('/')[-1]
                    
                    # Try to find the media item by URL
                    media_items = self.media_service.list_media(
                        tenant_id=tenant_id,
                        file_type='image/',
                        limit=1
                    )
                    
                    for item in media_items:
                        if item.url == src:
                            # Add to references
                            media_references.append({
                                'id': str(item.id),
                                'type': 'image',
                                'url': item.url
                            })
                            break
            
            # Process videos
            for video in soup.find_all('video'):
                # Check if the video has a src attribute
                if not video.get('src'):
                    continue
                
                src = video['src']
                
                # Skip external videos
                if src.startswith(('http://', 'https://')):
                    continue
                
                # Check if this is a reference to a media item in our library
                if '/static/media/' in src:
                    # Extract the filename from the URL
                    filename = src.split('/')[-1]
                    
                    # Try to find the media item by URL
                    media_items = self.media_service.list_media(
                        tenant_id=tenant_id,
                        file_type='video/',
                        limit=1
                    )
                    
                    for item in media_items:
                        if item.url == src:
                            # Add to references
                            media_references.append({
                                'id': str(item.id),
                                'type': 'video',
                                'url': item.url
                            })
                            break
            
            return str(soup), media_references
        except Exception as e:
            logger.error(f"Error processing editor content: {str(e)}")
            # Return the sanitized content if processing fails
            return self.sanitize_html(content), []
    
    def get_editor_config(self, editor_type: str = 'quill', context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get configuration for a WYSIWYG editor.
        
        Args:
            editor_type: The type of editor ('quill' is the default)
            context: Optional context information
            
        Returns:
            Dictionary of editor configuration
        """
        try:
            # Base config for all editors
            base_config = {
                'media_upload_url': '/api/media/upload',
                'media_browse_url': '/api/media',
                'sanitize': True,
                'allowed_tags': ALLOWED_TAGS,
                'allowed_attrs': ALLOWED_ATTRS,
                'allowed_styles': ALLOWED_STYLES
            }
            
            # Add context information if provided
            if context:
                base_config.update(context)
            
            # Editor-specific configuration - we only support Quill now
            if editor_type == 'quill' or editor_type == 'default':
                editor_config = {
                    'theme': 'snow',
                    'placeholder': 'Start writing or use the editor tools...',
                    'modules': {
                        'toolbar': [
                            ['bold', 'italic', 'underline', 'strike'],
                            [{'header': 1}, {'header': 2}],
                            [{'list': 'ordered'}, {'list': 'bullet'}],
                            [{'indent': '-1'}, {'indent': '+1'}],
                            [{'align': []}],
                            ['link', 'image', 'video'],
                            ['clean']
                        ]
                    }
                }
            else:
                # Default to Quill configuration
                logger.warning(f"Unsupported editor type {editor_type}, defaulting to Quill")
                editor_config = {
                    'theme': 'snow',
                    'placeholder': 'Start writing or use the editor tools...',
                    'modules': {
                        'toolbar': [
                            ['bold', 'italic', 'underline', 'strike'],
                            [{'header': 1}, {'header': 2}],
                            [{'list': 'ordered'}, {'list': 'bullet'}],
                            [{'indent': '-1'}, {'indent': '+1'}],
                            [{'align': []}],
                            ['link', 'image', 'video'],
                            ['clean']
                        ]
                    }
                }
            
            # Merge the configs
            base_config.update(editor_config)
            
            return base_config
        except Exception as e:
            logger.error(f"Error getting editor config: {str(e)}")
            # Return a basic config if an error occurs
            return {
                'basic': True,
                'editor_type': editor_type
            }
