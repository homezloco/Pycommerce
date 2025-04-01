"""
Gunicorn worker configuration.

This file configures Gunicorn to use Uvicorn workers for running FastAPI.
"""

import uvicorn
from uvicorn.workers import UvicornWorker

# The UvicornWorker class will be used by Gunicorn to serve our FastAPI application.
# Gunicorn will automatically detect and use this worker when specified in the command:
# gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app

class PyCommerceUvicornWorker(UvicornWorker):
    """Custom Uvicorn worker for PyCommerce application."""
    CONFIG_KWARGS = {
        "loop": "auto",
        "http": "auto",
        "lifespan": "on",
        "log_level": "info",
        "access_log": True,
        "factory": False,
        "forwarded_allow_ips": "*"
    }