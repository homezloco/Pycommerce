"""
Main entry point for the PyCommerce application.

This script is designed to be run by a WSGI server like gunicorn.
It imports the FastAPI application and adapts it to work with WSGI.
"""
import logging

from asgi_wsgi_app import proxy_to_uvicorn, start_uvicorn_server

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Start the uvicorn server in a separate process
start_uvicorn_server()

# Create app variable for WSGI server to import
# This is a WSGI app that proxies requests to the uvicorn server
app = proxy_to_uvicorn

if __name__ == "__main__":
    from web_app import app as fastapi_app
    import uvicorn
    
    # Run with uvicorn directly when file is executed
    uvicorn.run(fastapi_app, host="0.0.0.0", port=5000, reload=True)