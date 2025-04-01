"""
Flask wrapper for FastAPI application.

This module creates a Flask application that wraps the FastAPI app,
making it compatible with gunicorn in the Replit environment.
"""

import os
import logging
from flask import Flask, request, Response
import requests
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "pycommerce-secret-key")

# Define port for FastAPI service
FASTAPI_PORT = 8000

def start_fastapi_server():
    """Start the FastAPI server in a separate process."""
    import subprocess
    import sys
    
    try:
        subprocess.Popen([
            sys.executable, 
            "-c", 
            "import uvicorn; uvicorn.run('main:app', host='127.0.0.1', port=8000)"
        ])
        logger.info("Started FastAPI server on port 8000")
    except Exception as e:
        logger.error(f"Failed to start FastAPI server: {e}")

# Start FastAPI server
start_fastapi_server()

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def proxy(path):
    """Proxy all requests to the FastAPI server."""
    try:
        # Forward the request to the FastAPI server
        url = urljoin(f"http://127.0.0.1:{FASTAPI_PORT}/", path)
        
        # Get all headers from the request
        headers = {key: value for key, value in request.headers if key.lower() != 'host'}
        
        # Get request data/params
        data = request.get_data()
        params = request.args
        
        # Send the request to the FastAPI server
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=data,
            params=params,
            cookies=request.cookies,
            allow_redirects=False
        )
        
        # Create response
        response = Response(
            resp.content,
            resp.status_code,
            headers=dict(resp.headers)
        )
        return response
    except Exception as e:
        logger.error(f"Error proxying request: {e}")
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)