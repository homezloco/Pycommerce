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

# Flag to track if a server start is in progress
_server_start_in_progress = False

def start_uvicorn_server():
    """Start the uvicorn server in a separate process."""
    global uvicorn_process, _server_start_in_progress
    
    # If we're already in the process of starting a server, return immediately
    # This prevents multiple simultaneous start attempts from different requests
    if _server_start_in_progress:
        logger.info("Server start already in progress, waiting...")
        time.sleep(2)  # Give the current start process a chance to finish
        return
    
    try:
        _server_start_in_progress = True
        
        # First check if we can connect to an existing uvicorn server
        if is_uvicorn_running():
            logger.info("Uvicorn server is already running and responsive")
            return
            
        # Check if our process reference is still active but unresponsive
        if uvicorn_process is not None and uvicorn_process.poll() is None:
            logger.info("Uvicorn process is still running, waiting for it to become responsive")
            if wait_for_uvicorn(max_retries=3, delay=1):
                return
            else:
                # Process is running but not responsive, terminate it
                logger.warning("Uvicorn process is running but not responsive, restarting it")
                try:
                    uvicorn_process.terminate()
                    try:
                        uvicorn_process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        logger.warning("Failed to terminate previous uvicorn process, killing it")
                        uvicorn_process.kill()
                        try:
                            uvicorn_process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            logger.error("Failed to kill unresponsive process, may need manual intervention")
                except Exception as e:
                    logger.error(f"Error terminating previous process: {e}")
        
        # Clean up - try to find any existing uvicorn processes and terminate them
        # BUT only if they are stuck or not working - don't terminate working servers!
        try:
            import psutil
            current_pid = os.getpid()
            
            # First try to make a health check request before doing any cleanup
            # If a server is already running and working, don't terminate it!
            try:
                response = httpx.get(f"{UVICORN_SERVER}/api/health", timeout=2.0)
                if response.status_code == 200:
                    logger.info("Found a working uvicorn server, not terminating it")
                    return
            except Exception:
                # Only proceed with cleanup if the health check failed
                pass
                
            # Get all uvicorn processes using our port
            uvicorn_procs = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        cmdline = proc.info.get('cmdline', [])
                        if cmdline and 'uvicorn' in ' '.join(cmdline) and str(UVICORN_PORT) in ' '.join(cmdline):
                            if proc.pid != current_pid:
                                uvicorn_procs.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # We only terminate processes if the server is not responding
            # This keeps a working server running
            if not uvicorn_procs:
                logger.info("No existing uvicorn processes found")
            else:
                logger.warning(f"Found {len(uvicorn_procs)} non-responsive uvicorn processes")
                
                # Terminate all found processes in order
                for proc in uvicorn_procs:
                    try:
                        logger.warning(f"Terminating non-responsive uvicorn process (PID: {proc.pid})")
                        proc.terminate()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # Wait for termination to complete and kill any remaining that don't respond
                time.sleep(1)  # Give the processes a chance to terminate
                for proc in uvicorn_procs:
                    try:
                        if proc.is_running():
                            logger.warning(f"Process {proc.pid} didn't terminate, using stronger measures")
                            proc.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                    
        except ImportError:
            logger.warning("psutil not available, skipping uvicorn process cleanup")
        except Exception as e:
            logger.warning(f"Error trying to clean up uvicorn processes: {e}")
    
        # Start new uvicorn process with a small delay to ensure port is free
        time.sleep(1)
        cmd = [
            sys.executable, "-m", "uvicorn", "web_app:app",
            "--host", UVICORN_HOST, "--port", str(UVICORN_PORT),
            "--reload", "--no-use-colors"
        ]
        logger.info(f"Starting uvicorn server with command: {' '.join(cmd)}")
        
        try:
            uvicorn_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except Exception as e:
            logger.error(f"Failed to start uvicorn process: {e}")
            return None
        
        # Start a thread to log uvicorn output if the process was created successfully
        if uvicorn_process and uvicorn_process.stdout:
            def log_output():
                try:
                    for line in iter(uvicorn_process.stdout.readline, ""):
                        logger.info(f"Uvicorn: {line.strip()}")
                except Exception as e:
                    logger.error(f"Error in log output thread: {e}")
            
            threading.Thread(target=log_output, daemon=True).start()
        else:
            logger.warning("Uvicorn process or stdout not available, cannot log output")
        
        # Register a signal handler to clean up the uvicorn process
        def cleanup_uvicorn(signum, frame):
            logger.info("Received signal, terminating uvicorn server")
            if uvicorn_process and uvicorn_process.poll() is None:
                try:
                    uvicorn_process.terminate()
                    uvicorn_process.wait(timeout=5)
                except Exception:
                    pass
            sys.exit(0)
        
        signal.signal(signal.SIGTERM, cleanup_uvicorn)
        signal.signal(signal.SIGINT, cleanup_uvicorn)
        
        # Wait for uvicorn to start
        wait_for_uvicorn()
        
    finally:
        _server_start_in_progress = False

# Cache to avoid making too many health check requests
_last_health_check = None
_last_health_time = 0
_health_cache_ttl = 5  # seconds

def is_uvicorn_running():
    """Check if uvicorn server is running with caching to avoid hammering the health endpoint."""
    global _last_health_check, _last_health_time
    
    # Use cached result if it's recent enough
    current_time = time.time()
    if _last_health_check is not None and (current_time - _last_health_time) < _health_cache_ttl:
        logger.debug(f"Using cached health check result: {_last_health_check}")
        return _last_health_check
    
    try:
        # Use a short timeout to avoid hanging
        response = httpx.get(f"{UVICORN_SERVER}/api/health", timeout=2.0)
        result = response.status_code == 200
        
        # Cache the result
        _last_health_check = result
        _last_health_time = current_time
        
        return result
    except Exception as e:
        logger.debug(f"Health check failed: {e}")
        
        # Cache the failed result too
        _last_health_check = False
        _last_health_time = current_time
        
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
    path = environ.get('PATH_INFO', '')
    
    # Special handling for admin/categories route - don't restart server if it's already running
    # This helps prevent the common issue where accessing the categories page causes server crashes
    is_categories_request = path and '/admin/categories' in path
    if is_categories_request:
        logger.info("Categories page requested, being extra careful with server status")
    
    # Make sure uvicorn is running - we'll only check health URL once
    try:
        health_check = is_uvicorn_running()
    except Exception as e:
        logger.error(f"Error checking uvicorn health: {e}")
        health_check = False
        
    if not health_check:
        # Only try to start the server if it's not already trying to start
        # This avoids repeated restart attempts that can cause conflicts
        if not _server_start_in_progress:
            logger.info("Attempting to start uvicorn server")
            start_uvicorn_server()
            
            # Do one final check if the server started
            try:
                if not is_uvicorn_running():
                    # For categories page requests, try to be more lenient - it might still be starting up
                    if is_categories_request:
                        logger.warning("Categories page requested but server not fully ready. Waiting longer...")
                        time.sleep(3)  # Give it a bit more time
                        if not is_uvicorn_running():
                            logger.error("Could not start uvicorn server after extended wait for categories page")
                            start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
                            return [b'Failed to start uvicorn server for categories page - please try again in a moment']
                    else:
                        logger.error("Could not start uvicorn server after attempt")
                        start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
                        return [b'Failed to start uvicorn server']
            except Exception as e:
                logger.error(f"Final health check failed: {e}")
                start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
                return [f"Error checking uvicorn health: {e}".encode('utf-8')]
        else:
            # Let the user know the server is in the process of starting
            logger.info("Server start already in progress, waiting...")
            start_response('503 Service Unavailable', [('Content-Type', 'text/plain'), ('Retry-After', '5')])
            return [b'Server is starting up, please try again in a few seconds']
    
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