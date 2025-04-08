"""
ASGI to WSGI adapter for FastAPI.

This module adapts the FastAPI app (ASGI) to work with gunicorn (WSGI server).
"""
import os
import logging
from web_app import app as asgi_app

import uvicorn
import httpx
import multiprocessing
import signal
import sys
import subprocess
import threading
import time

from wsgiref.handlers import SimpleHandler
from wsgiref.util import setup_testing_defaults
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a ProcessPoolExecutor for handling ASGI requests
UVICORN_PORT = 8000
UVICORN_HOST = "127.0.0.1"
UVICORN_SERVER = f"http://{UVICORN_HOST}:{UVICORN_PORT}"

# Global variable to store uvicorn server process
uvicorn_process = None

def start_uvicorn_server():
    """Start the uvicorn server in a separate process."""
    global uvicorn_process
    if uvicorn_process is not None and uvicorn_process.poll() is None:
        logger.info("Uvicorn server is already running")
        return

    cmd = [
        sys.executable, "-m", "uvicorn", "web_app:app",
        "--host", UVICORN_HOST, "--port", str(UVICORN_PORT),
        "--reload", "--no-use-colors"
    ]
    logger.info(f"Starting uvicorn server with command: {' '.join(cmd)}")
    
    uvicorn_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    
    # Start a thread to log uvicorn output
    def log_output():
        for line in iter(uvicorn_process.stdout.readline, ""):
            logger.info(f"Uvicorn: {line.strip()}")
    
    threading.Thread(target=log_output, daemon=True).start()
    
    # Register a signal handler to clean up the uvicorn process
    def cleanup_uvicorn(signum, frame):
        logger.info("Received signal, terminating uvicorn server")
        if uvicorn_process and uvicorn_process.poll() is None:
            uvicorn_process.terminate()
            uvicorn_process.wait(timeout=5)
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, cleanup_uvicorn)
    signal.signal(signal.SIGINT, cleanup_uvicorn)
    
    # Wait for uvicorn to start
    wait_for_uvicorn()

def is_uvicorn_running():
    """Check if uvicorn server is running."""
    try:
        response = httpx.get(f"{UVICORN_SERVER}/api/health")
        return response.status_code == 200
    except Exception:
        return False

def wait_for_uvicorn(max_retries=10, delay=1):
    """Wait for uvicorn server to start."""
    logger.info("Waiting for uvicorn server to start...")
    for i in range(max_retries):
        if is_uvicorn_running():
            logger.info("Uvicorn server is running")
            return True
        logger.info(f"Waiting for uvicorn server (attempt {i+1}/{max_retries})")
        time.sleep(delay)
    
    logger.error("Failed to start uvicorn server")
    return False

def proxy_to_uvicorn(environ, start_response):
    """WSGI app that proxies requests to the uvicorn server."""
    # Make sure uvicorn is running
    if not is_uvicorn_running():
        start_uvicorn_server()
        if not is_uvicorn_running():
            start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
            return [b'Failed to start uvicorn server']
    
    # Extract request details from WSGI environ
    method = environ['REQUEST_METHOD']
    path = environ['PATH_INFO']
    query_string = environ.get('QUERY_STRING', '')
    url = f"{UVICORN_SERVER}{path}"
    if query_string:
        url = f"{url}?{query_string}"
    
    # Get request body
    content_length = int(environ.get('CONTENT_LENGTH', 0) or 0)
    body = environ['wsgi.input'].read(content_length) if content_length > 0 else None
    
    # Get headers
    headers = {
        k[5:]: v for k, v in environ.items()
        if k.startswith('HTTP_') and k != 'HTTP_HOST'
    }
    
    # Standard CGI headers
    if 'CONTENT_TYPE' in environ:
        headers['Content-Type'] = environ['CONTENT_TYPE']
    if 'CONTENT_LENGTH' in environ:
        headers['Content-Length'] = environ['CONTENT_LENGTH']
    
    try:
        # Make the request to uvicorn
        with httpx.Client() as client:
            response = client.request(
                method=method,
                url=url,
                headers=headers,
                content=body,
                timeout=30.0,
                follow_redirects=True
            )
        
        # Prepare the WSGI response
        wsgi_headers = [(k, v) for k, v in response.headers.items()]
        status = f"{response.status_code} {response.reason_phrase}"
        
        # Send the response headers
        start_response(status, wsgi_headers)
        
        # Return response body
        return [response.content]
    
    except Exception as e:
        logger.error(f"Error proxying request to uvicorn: {e}")
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
        return [f"Error proxying request to uvicorn: {e}".encode('utf-8')]

# This is the WSGI application
app = proxy_to_uvicorn

if __name__ == "__main__":
    # For local development, use a simple WSGI server
    from wsgiref.simple_server import make_server
    httpd = make_server('', 5000, app)
    print("Serving on port 5000...")
    httpd.serve_forever()