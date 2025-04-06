"""
This module is the entry point for the uvicorn server.

It's designed to be imported by uvicorn with the --reload flag.
"""
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn_server")

# Import the FastAPI app directly
from web_app import app

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting uvicorn server from uvicorn_server.py entry point")
    uvicorn.run(
        "uvicorn_server:app", 
        host="127.0.0.1", 
        port=8000,
        reload=True,
        reload_dirs=["."]
    )