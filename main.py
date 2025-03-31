"""
Main entry point for the PyCommerce Demo application.

This file imports and exposes the Flask app from the demo package.
"""

from demo.main import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)