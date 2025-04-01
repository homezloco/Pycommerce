"""
Main entry point for the PyCommerce Platform.

This file is the gunicorn-compatible adapter for the FastAPI app.
"""

from asgi_wsgi_app import app

# This is the WSGI application used by gunicorn
__all__ = ['app']

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web_server:app", host="0.0.0.0", port=5000, reload=True)