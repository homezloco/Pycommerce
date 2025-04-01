"""
WSGI adapter for FastAPI app.

This module provides a WSGI adapter for the FastAPI app so it can be run with gunicorn.
"""

import logging
from main import app
from fastapi.middleware.wsgi import WSGIMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Wrap the FastAPI app with WSGIMiddleware to make it compatible with WSGI servers
wsgi_app = WSGIMiddleware(app)

# This is the entry point for gunicorn
application = wsgi_app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)