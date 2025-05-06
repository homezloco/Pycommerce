"""
Flask adapter for FastAPI application.

This module creates a Flask application that serves as a proxy to the FastAPI app.
"""

import os
import logging
from flask import Flask, render_template, redirect, url_for, request, Response, session, jsonify
import requests
from urllib.parse import urljoin
import threading
import time
import subprocess
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "pycommerce-secret-key")

# Export Flask app for import elsewhere
flask_app = app

# Define port for FastAPI service
FASTAPI_PORT = 8001  # Changed to match the UVICORN_PORT in asgi_wsgi_app.py
FASTAPI_URL = f"http://127.0.0.1:{FASTAPI_PORT}"
fastapi_process = None

def start_fastapi_server():
    """Start the FastAPI server in a separate process."""
    global fastapi_process
    try:
        logger.info("Starting FastAPI server...")
        fastapi_process = subprocess.Popen([
            sys.executable, 
            "-c", 
            f"import uvicorn; uvicorn.run('web_app:app', host='127.0.0.1', port={FASTAPI_PORT})"
        ])
        logger.info(f"Started FastAPI server on port {FASTAPI_PORT}")
        return True
    except Exception as e:
        logger.error(f"Failed to start FastAPI server: {e}")
        return False

def is_fastapi_running():
    """Check if FastAPI server is running."""
    try:
        response = requests.get(f"{FASTAPI_URL}/health", timeout=1)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def wait_for_fastapi(max_retries=10, delay=1):
    """Wait for FastAPI server to start."""
    for i in range(max_retries):
        if is_fastapi_running():
            logger.info("FastAPI server is running")
            return True
        logger.info(f"Waiting for FastAPI server... {i+1}/{max_retries}")
        time.sleep(delay)
    return False

# Disable automatic FastAPI server start - let asgi_wsgi_app.py handle this instead
# start_thread = threading.Thread(target=start_fastapi_server)
# start_thread.daemon = True
# start_thread.start()
# time.sleep(2)  # Give it a moment to start
logger.info("Automatic FastAPI server start disabled - delegating to asgi_wsgi_app.py")

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        response = requests.get(f"{FASTAPI_URL}/health")
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error checking FastAPI health: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def proxy(path):
    """Proxy all requests to the FastAPI server."""
    try:
        # Forward the request to the FastAPI server
        url = urljoin(FASTAPI_URL, path)
        
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
    except requests.exceptions.ConnectionError:
        # Don't try to restart the server, just report the error
        # Server startup is now handled by asgi_wsgi_app.py
        logger.warning("FastAPI server is not available or not running.")
        return jsonify({"error": "FastAPI server is not available. Server is managed by asgi_wsgi_app.py"}), 503
    except Exception as e:
        logger.error(f"Error proxying request: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)