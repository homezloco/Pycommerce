"""
Simple Flask server for PyCommerce.

This is a bare minimum Flask app to test if Flask is working correctly.
"""

import os
import logging
from flask import Flask, jsonify, render_template_string

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# HTML template for the home page
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PyCommerce Simple Test</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
</head>
<body>
    <div class="container my-5">
        <div class="row">
            <div class="col-md-8 mx-auto">
                <div class="card">
                    <div class="card-header bg-dark">
                        <h1 class="text-center">PyCommerce Test Page</h1>
                    </div>
                    <div class="card-body">
                        <p class="lead">This page confirms that the Flask server is working correctly.</p>
                        <div class="d-grid gap-2">
                            <a href="/health" class="btn btn-info">Health Check</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

# Create app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "pycommerce-dev-key")

# Routes
@app.route('/')
def index():
    """Simple home page."""
    logger.debug("Home page requested")
    return render_template_string(HOME_TEMPLATE)

@app.route('/health')
def health():
    """Health check endpoint."""
    logger.debug("Health check requested")
    return jsonify({
        "status": "ok",
        "message": "Flask server is working correctly"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)