"""
Flask web application for the PyCommerce platform.

This module provides a Flask web application that serves as a proxy to the
PyCommerce FastAPI application.
"""

import os
import sys
import logging
import subprocess
import threading
import time
from flask import Flask, render_template_string, jsonify, request, redirect, url_for
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "pycommerce-secret-key")

# Define constants
FASTAPI_PORT = 8000
FASTAPI_URL = f"http://127.0.0.1:{FASTAPI_PORT}"
fastapi_process = None

# HTML template for the home page
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PyCommerce Platform</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .header { padding: 2rem 1rem; background-color: #f8f9fa; }
        .feature-icon { font-size: 2rem; color: #0d6efd; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header text-center mb-5">
            <h1>PyCommerce Platform</h1>
            <p class="lead">A modular Python ecommerce SDK with plugin architecture</p>
        </div>
        
        <div class="row mb-5">
            <div class="col-md-4">
                <div class="card mb-4">
                    <div class="card-body text-center">
                        <div class="feature-icon mb-3">🛍️</div>
                        <h3>Multi-tenant</h3>
                        <p>Support for multiple stores with data isolation</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card mb-4">
                    <div class="card-body text-center">
                        <div class="feature-icon mb-3">🔌</div>
                        <h3>Plugin Architecture</h3>
                        <p>Extensible with payment and shipping plugins</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card mb-4">
                    <div class="card-body text-center">
                        <div class="feature-icon mb-3">⚡</div>
                        <h3>FastAPI Integration</h3>
                        <p>Modern REST API with async support</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mb-5">
            <div class="col-md-6 mx-auto">
                <div class="card">
                    <div class="card-header">
                        <h3>Demo API Links</h3>
                    </div>
                    <div class="card-body">
                        <ul class="list-group list-group-flush">
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Health Check
                                <a href="/health" class="btn btn-sm btn-primary">View</a>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                All Tenants
                                <a href="/tenants" class="btn btn-sm btn-primary">View</a>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Products (Default Tenant)
                                <a href="/products?tenant=default" class="btn btn-sm btn-primary">View</a>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Generate Sample Data
                                <a href="/generate-sample-data" class="btn btn-sm btn-success">Create</a>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <footer class="bg-light py-4">
        <div class="container text-center">
            <p>PyCommerce Platform &copy; 2025</p>
        </div>
    </footer>
</body>
</html>
"""

def start_fastapi_server():
    """Start the FastAPI server in a separate process."""
    global fastapi_process
    try:
        logger.info("Starting FastAPI server...")
        fastapi_process = subprocess.Popen([
            sys.executable,
            "-c", 
            "import uvicorn; uvicorn.run('main:app', host='127.0.0.1', port=8000)"
        ])
        logger.info("Started FastAPI server on port 8000")
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

# Start FastAPI server
start_thread = threading.Thread(target=start_fastapi_server)
start_thread.daemon = True
start_thread.start()
time.sleep(2)  # Give it a moment to start

@app.route('/')
def index():
    """Home page with links to API endpoints."""
    return render_template_string(HOME_TEMPLATE)

@app.route('/health')
def health():
    """Health check endpoint."""
    try:
        response = requests.get(f"{FASTAPI_URL}/health")
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error checking FastAPI health: {e}")
        # Create a backup health response if FastAPI server is not available
        return jsonify({
            "status": "warning",
            "version": "0.1.0",
            "message": "Flask proxy is running, but FastAPI server is unavailable"
        })

@app.route('/tenants')
def tenants():
    """Get all tenants."""
    try:
        response = requests.get(f"{FASTAPI_URL}/tenants")
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error getting tenants: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/products')
def products():
    """Get products."""
    try:
        # Forward all query params
        params = request.args.to_dict()
        response = requests.get(f"{FASTAPI_URL}/products", params=params)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/generate-sample-data')
def generate_sample_data():
    """Generate sample data for testing."""
    try:
        response = requests.get(f"{FASTAPI_URL}/generate-sample-data")
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error generating sample data: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)