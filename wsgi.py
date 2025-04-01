"""
WSGI adapter for FastAPI application.

This module adapts the FastAPI app to work with gunicorn (WSGI server).
"""
import os
import logging
import multiprocessing
import signal
import sys
import subprocess
import threading
import time
from urllib.parse import urljoin

import requests
from flask import Flask, Response, request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app as WSGI entry point
app = Flask(__name__)

# Configuration
FASTAPI_PORT = 8000  # Use a different port for FastAPI
FASTAPI_HOST = "127.0.0.1"
FASTAPI_SERVER = f"http://{FASTAPI_HOST}:{FASTAPI_PORT}"

# Global variable to store FastAPI server process
fastapi_process = None


def start_fastapi_server():
    """Start the FastAPI server in a separate process."""
    global fastapi_process
    if fastapi_process is not None and fastapi_process.poll() is None:
        logger.info("FastAPI server is already running")
        return

    cmd = [
        sys.executable, "-m", "uvicorn", "web_server:app",
        "--host", FASTAPI_HOST, "--port", str(FASTAPI_PORT)
    ]
    logger.info(f"Starting FastAPI server with command: {' '.join(cmd)}")
    
    fastapi_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    
    # Start a thread to log FastAPI output
    def log_output():
        for line in iter(fastapi_process.stdout.readline, ""):
            logger.info(f"FastAPI: {line.strip()}")
    
    threading.Thread(target=log_output, daemon=True).start()
    
    # Register a signal handler to clean up the FastAPI process
    def cleanup_fastapi(signum, frame):
        logger.info("Received signal, terminating FastAPI server")
        if fastapi_process and fastapi_process.poll() is None:
            fastapi_process.terminate()
            fastapi_process.wait(timeout=5)
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, cleanup_fastapi)
    signal.signal(signal.SIGINT, cleanup_fastapi)
    
    # Wait for FastAPI to start
    wait_for_fastapi()


def is_fastapi_running():
    """Check if FastAPI server is running."""
    try:
        response = requests.get(f"{FASTAPI_SERVER}/health")
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def wait_for_fastapi(max_retries=10, delay=1):
    """Wait for FastAPI server to start."""
    logger.info("Waiting for FastAPI server to start...")
    for i in range(max_retries):
        if is_fastapi_running():
            logger.info("FastAPI server is running")
            return True
        logger.info(f"Waiting for FastAPI server (attempt {i+1}/{max_retries})")
        time.sleep(delay)
    
    logger.error("Failed to start FastAPI server")
    return False


@app.route("/health")
def health():
    """Health check endpoint"""
    if not is_fastapi_running():
        start_fastapi_server()
    
    try:
        response = requests.get(f"{FASTAPI_SERVER}/health")
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get("Content-Type", "application/json")
        )
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}, 500


@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def proxy(path):
    """Proxy all requests to the FastAPI server."""
    if not is_fastapi_running():
        start_fastapi_server()
    
    # Forward the request to FastAPI
    url = urljoin(FASTAPI_SERVER, path)
    
    # Get headers from the request
    headers = {key: value for key, value in request.headers if key.lower() != "host"}
    
    # Forward the request with the same method, headers, and data
    try:
        response = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            params=request.args,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=5
        )
        
        # Create a Flask response from the FastAPI response
        flask_response = Response(
            response.content,
            status=response.status_code,
        )
        
        # Copy headers from FastAPI response to Flask response
        for key, value in response.headers.items():
            if key.lower() not in ("content-length", "connection", "transfer-encoding"):
                flask_response.headers[key] = value
        
        return flask_response
    except requests.exceptions.RequestException as e:
        logger.error(f"Error proxying request to FastAPI: {e}")
        return {"status": "error", "message": str(e)}, 500


# Start FastAPI server when this module is imported
start_fastapi_server()

# Entry point for gunicorn
def create_app():
    """Create the Flask app for gunicorn."""
    return app


if __name__ == "__main__":
    # For local development
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)