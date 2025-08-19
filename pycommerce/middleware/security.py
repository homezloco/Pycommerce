
"""
Security middleware for PyCommerce.
"""

import re
from typing import Dict, Any
from fastapi import Request, HTTPException
from fastapi.responses import Response
import logging

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    """Security middleware for adding security headers and validation."""
    
    def __init__(self):
        self.allowed_origins = [
            "https://*.replit.dev",
            "https://*.replit.app", 
            "https://*.replit.co"
        ]
    
    async def __call__(self, request: Request, call_next):
        # Add security headers
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; font-src 'self' https://cdn.jsdelivr.net;"
        
        return response

def validate_input(data: str, max_length: int = 1000) -> str:
    """Validate and sanitize input data."""
    if not data:
        return ""
    
    # Remove null bytes and control characters except newlines and tabs
    data = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', str(data))
    
    # Limit length
    if len(data) > max_length:
        raise HTTPException(status_code=400, detail=f"Input exceeds maximum length of {max_length}")
    
    return data.strip()

def validate_admin_access(request: Request) -> bool:
    """Validate admin access with additional security checks."""
    # Check if request is from admin routes
    if not request.url.path.startswith('/admin'):
        return True
    
    # Add additional security checks for admin routes
    user_agent = request.headers.get('user-agent', '').lower()
    
    # Block known bad user agents
    blocked_agents = ['bot', 'crawler', 'spider', 'scraper']
    if any(agent in user_agent for agent in blocked_agents):
        logger.warning(f"Blocked suspicious user agent: {user_agent}")
        raise HTTPException(status_code=403, detail="Access denied")
    
    return True
