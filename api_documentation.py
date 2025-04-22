"""
Simple Flask application to serve API documentation.

This is a standalone Flask application that serves the API documentation
without interfering with the main application.
"""

import os
import logging
from flask import Flask, render_template_string, send_from_directory

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

@app.route('/')
def home():
    """Home page with link to API documentation."""
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PyCommerce API Documentation</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 {
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
            }
            a {
                color: #3498db;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            .container {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 20px;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <h1>PyCommerce API Documentation</h1>
        <div class="container">
            <p>Welcome to the PyCommerce API documentation server.</p>
            <p>This server provides documentation for the PyCommerce API.</p>
            <p><a href="/api-docs">View API Documentation</a></p>
        </div>
    </body>
    </html>
    """)

@app.route('/api-docs')
def api_docs():
    """Serve the API documentation page."""
    try:
        with open("static/api-docs.html", "r") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error serving API documentation: {e}")
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Error - PyCommerce API Documentation</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }
                h1 {
                    color: #e74c3c;
                }
                .error-container {
                    background-color: #f9f9f9;
                    border: 1px solid #e74c3c;
                    border-radius: 5px;
                    padding: 20px;
                    margin-top: 20px;
                }
                a {
                    color: #3498db;
                    text-decoration: none;
                }
                a:hover {
                    text-decoration: underline;
                }
            </style>
        </head>
        <body>
            <h1>Error Loading API Documentation</h1>
            <div class="error-container">
                <p>There was an error loading the API documentation.</p>
                <p><strong>Error:</strong> {{ error }}</p>
                <p><a href="/">Return to Home</a></p>
            </div>
        </body>
        </html>
        """, error=str(e))

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files for the documentation."""
    return send_from_directory('static', filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)