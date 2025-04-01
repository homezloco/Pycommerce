"""
Simple Flask application for testing.

This is a standalone Flask application with no dependencies on other project files.
"""

import os
from flask import Flask, jsonify, render_template_string

# Create app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "development-key")

# HTML template for the home page
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PyCommerce Test Page</title>
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

@app.route('/')
def index():
    return render_template_string(HOME_TEMPLATE)

@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "message": "Flask server is working correctly"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)