"""
Run script for PyCommerce FastAPI application.

This script starts the FastAPI application using uvicorn directly.
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)