"""
WSGI adapter for FastAPI app.

This module provides a WSGI adapter for the FastAPI app so it can be run with gunicorn.
"""

import logging
import sys
from fastapi.middleware.wsgi import WSGIMiddleware
from main import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log startup
logger.info("Starting PyCommerce WSGI adapter")

# This is what gunicorn loads
application = app

# For testing 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)