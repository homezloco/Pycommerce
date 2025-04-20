"""
Debug routes for administration.
Provides tools to diagnose and fix common issues.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from pycommerce.core.db import SessionLocal
from pycommerce.models.tenant import TenantManager
from pycommerce.models.page_builder import PageManager, PageSectionManager, ContentBlockManager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin", "debug"])

# Template setup will be passed from main app
templates = None

def setup_routes(jinja_templates: Jinja2Templates = None):
    """Set up debug routes."""
    global templates
    templates = jinja_templates
    return router

@router.get("/debug", response_class=HTMLResponse)
async def debug_dashboard(request: Request):
    """Main debug dashboard."""
    # Initialize a session for this request
    session = SessionLocal()

    try:
        # Check database connectivity
        db_status = "Unknown"
        try:
            # Try to get tenants as a simple DB check
            tenant_manager = TenantManager(session)
            tenants = tenant_manager.get_all()
            tenant_count = len(tenants) if tenants else 0
            db_status = f"Connected (Found {tenant_count} tenants)"
        except Exception as e:
            db_status = f"Error: {str(e)}"

        # Check template directory
        template_dir = Path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "templates"))
        template_status = f"Found ({len(list(template_dir.glob('**/*.html')))} templates)" if template_dir.exists() else "Not found"

        # Check static directory
        static_dir = Path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "static"))
        static_status = f"Found ({len(list(static_dir.glob('**/*.*')))} files)" if static_dir.exists() else "Not found"

        # Check debug script
        debug_script_path = Path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "debug_page_builder.py"))
        debug_script_status = "Found" if debug_script_path.exists() else "Not found"

        # Return HTML directly since we might have template issues
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>PyCommerce Diagnostic Dashboard</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
            <style>
                .debug-card {{
                    margin-bottom: 1rem;
                    border-radius: 0.5rem;
                }}
            </style>
        </head>
        <body>
            <div class="container py-4">
                <h1 class="mb-4">PyCommerce Diagnostic Dashboard</h1>

                <div class="row">
                    <div class="col-md-6">
                        <div class="card debug-card">
                            <div class="card-header">
                                <h5>System Status</h5>
                            </div>
                            <div class="card-body">
                                <p><strong>Database:</strong> {db_status}</p>
                                <p><strong>Templates:</strong> {template_status}</p>
                                <p><strong>Static Files:</strong> {static_status}</p>
                                <p><strong>Debug Script:</strong> {debug_script_status}</p>
                                <p><strong>Server Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                            </div>
                        </div>

                        <div class="card debug-card">
                            <div class="card-header">
                                <h5>Debug Tools</h5>
                            </div>
                            <div class="card-body">
                                <div class="d-grid gap-2">
                                    <a href="/admin/debug-pages" class="btn btn-primary" target="_blank">
                                        Debug Page Builder API
                                    </a>
                                    <a href="/admin/pages-debug" class="btn btn-info" target="_blank">
                                        Page Builder Debug UI
                                    </a>
                                    <button id="runDebugBtn" class="btn btn-warning">
                                        Run Full Diagnostics
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="col-md-6">
                        <div class="card debug-card">
                            <div class="card-header">
                                <h5>Debug Results</h5>
                            </div>
                            <div class="card-body">
                                <div id="debugResults">
                                    <p class="text-muted">Click "Run Full Diagnostics" to see results</p>
                                </div>
                            </div>
                        </div>

                        <div class="card debug-card">
                            <div class="card-header">
                                <h5>JavaScript Debug Console</h5>
                            </div>
                            <div class="card-body">
                                <div class="mb-3">
                                    <label for="jsDebugCode" class="form-label">Run JavaScript Debug Code:</label>
                                    <textarea id="jsDebugCode" class="form-control" rows="3">window.debugPageBuilderEditor();</textarea>
                                </div>
                                <button id="runJsDebugBtn" class="btn btn-sm btn-secondary">
                                    Run JavaScript
                                </button>
                                <div id="jsResults" class="mt-2 border p-2 bg-light">
                                    <p class="text-muted">JavaScript output will appear here</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                // Load debug script
                const debugScript = document.createElement('script');
                debugScript.src = '/static/js/debug-page-builder.js';
                document.head.appendChild(debugScript);

                // Run diagnostics button
                document.getElementById('runDebugBtn').addEventListener('click', function() {
                    const resultsDiv = document.getElementById('debugResults');
                    resultsDiv.innerHTML = '<div class="d-flex justify-content-center"><div class="spinner-border text-primary" role="status"></div></div><p class="text-center mt-2">Running diagnostics...</p>';

                    fetch('/admin/debug-pages')
                        .then(response => response.json())
                        .then(data => {
                            let html = '<div class="accordion" id="debugAccordion">';

                            // Database info
                            html += '<div class="accordion-item">';
                            html += '<h2 class="accordion-header"><button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseDatabase">Database Information</button></h2>';
                            html += '<div id="collapseDatabase" class="accordion-collapse collapse show" data-bs-parent="#debugAccordion"><div class="accordion-body">';

                            if (data.database_info && data.database_info.tables_exist) {
                                html += '<table class="table table-sm">';
                                html += '<thead><tr><th>Table</th><th>Status</th><th>Records</th></tr></thead><tbody>';

                                for (const table in data.database_info.tables_exist) {
                                    const exists = data.database_info.tables_exist[table];
                                    const count = data.database_info.record_counts ? data.database_info.record_counts[table] : 'N/A';

                                    html += `<tr>
                                        <td>${table}</td>
                                        <td>${exists ? '<span class="badge bg-success">✓</span>' : '<span class="badge bg-danger">✗</span>'}</td>
                                        <td>${count}</td>
                                    </tr>`;
                                }

                                html += '</tbody></table>';
                            } else {
                                html += '<div class="alert alert-warning">No database information available</div>';
                            }

                            html += '</div></div></div>';

                            // Tenant info
                            html += '<div class="accordion-item">';
                            html += '<h2 class="accordion-header"><button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseTenants">Tenant Information</button></h2>';
                            html += '<div id="collapseTenants" class="accordion-collapse collapse" data-bs-parent="#debugAccordion"><div class="accordion-body">';

                            html += `<p>Current tenant: <strong>${data.selected_tenant_slug || 'None'}</strong></p>`;
                            html += `<p>Found ${data.tenants_count || 0} tenants</p>`;

                            if (data.tenants && data.tenants.length > 0) {
                                html += '<table class="table table-sm">';
                                html += '<thead><tr><th>ID</th><th>Name</th><th>Slug</th></tr></thead><tbody>';

                                data.tenants.forEach(tenant => {
                                    html += `<tr>
                                        <td>${tenant.id}</td>
                                        <td>${tenant.name}</td>
                                        <td>${tenant.slug}</td>
                                    </tr>`;
                                });

                                html += '</tbody></table>';
                            }

                            html += '</div></div></div>';

                            // Pages info
                            html += '<div class="accordion-item">';
                            html += '<h2 class="accordion-header"><button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapsePages">Pages Information</button></h2>';
                            html += '<div id="collapsePages" class="accordion-collapse collapse" data-bs-parent="#debugAccordion"><div class="accordion-body">';

                            html += `<p>Found ${data.pages_count || 0} pages</p>`;

                            if (data.pages && data.pages.length > 0) {
                                html += '<table class="table table-sm">';
                                html += '<thead><tr><th>Title</th><th>Slug</th><th>Published</th></tr></thead><tbody>';

                                data.pages.forEach(page => {
                                    html += `<tr>
                                        <td>${page.title}</td>
                                        <td>${page.slug}</td>
                                        <td>${page.is_published ? 'Yes' : 'No'}</td>
                                    </tr>`;
                                });

                                html += '</tbody></table>';
                            } else {
                                html += '<div class="alert alert-info">No pages found for current tenant</div>';
                            }

                            html += '</div></div></div>';

                            html += '</div>'; // Close accordion

                            resultsDiv.innerHTML = html;
                        })
                        .catch(error => {
                            resultsDiv.innerHTML = `<div class="alert alert-danger">Error fetching debug info: ${error.message}</div>`;
                        });
                });

                // Run JS button
                document.getElementById('runJsDebugBtn').addEventListener('click', function() {
                    const code = document.getElementById('jsDebugCode').value;
                    const resultsDiv = document.getElementById('jsResults');

                    // Capture console.log output
                    const origConsoleLog = console.log;
                    const origConsoleError = console.error;
                    const origConsoleWarn = console.warn;
                    const logs = [];

                    console.log = function(...args) {
                        logs.push(['log', args.map(a => String(a)).join(' ')]);
                        origConsoleLog.apply(console, args);
                    };

                    console.error = function(...args) {
                        logs.push(['error', args.map(a => String(a)).join(' ')]);
                        origConsoleError.apply(console, args);
                    };

                    console.warn = function(...args) {
                        logs.push(['warn', args.map(a => String(a)).join(' ')]);
                        origConsoleWarn.apply(console, args);
                    };

                    try {
                        // Run the code
                        const result = eval(code);

                        // Build output HTML
                        let html = '<div class="border-bottom pb-2 mb-2"><strong>Result:</strong> ';

                        if (result !== undefined) {
                            if (typeof result === 'object') {
                                html += `<pre>${JSON.stringify(result, null, 2)}</pre>`;
                            } else {
                                html += `<span>${result}</span>`;
                            }
                        } else {
                            html += '<span class="text-muted">undefined</span>';
                        }

                        html += '</div>';

                        // Add logs
                        if (logs.length > 0) {
                            html += '<div><strong>Console output:</strong></div>';
                            html += '<div class="mt-2 console-output">';

                            logs.forEach(([type, message]) => {
                                let className = 'text-dark';
                                if (type === 'error') className = 'text-danger';
                                if (type === 'warn') className = 'text-warning';

                                html += `<div class="${className}">${message}</div>`;
                            });

                            html += '</div>';
                        }

                        resultsDiv.innerHTML = html;
                    } catch (e) {
                        resultsDiv.innerHTML = `<div class="text-danger">Error: ${e.message}</div>`;
                    } finally {
                        // Restore console functions
                        console.log = origConsoleLog;
                        console.error = origConsoleError;
                        console.warn = origConsoleWarn;
                    }
                });
            </script>
        </body>
        </html>
        """

        return HTMLResponse(content=html)
    except Exception as e:
        logger.error(f"Error in debug dashboard: {str(e)}")
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)
    finally:
        session.close()