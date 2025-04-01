"""
Run script for PyCommerce FastAPI application.

This script starts the FastAPI application using uvicorn directly.
"""
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.environ.get("PORT", "5000"))
    
    logger.info(f"Starting PyCommerce API server on port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)