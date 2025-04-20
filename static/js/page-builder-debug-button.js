
/**
 * This script adds a floating debug button to page builder pages
 * to make it easier to run diagnostics when needed.
 */
(function() {
  function addDebugButton() {
    // Check if we're on an admin page
    if (!window.location.pathname.includes('/admin/')) {
      return;
    }
    
    // Don't add button if it already exists
    if (document.getElementById('page-builder-debug-btn')) {
      return;
    }
    
    // Create the button
    const button = document.createElement('button');
    button.id = 'page-builder-debug-btn';
    button.className = 'btn btn-info position-fixed';
    button.style.bottom = '20px';
    button.style.right = '20px';
    button.style.zIndex = '9999';
    button.innerHTML = '<i class="fas fa-bug"></i> Debug Page Builder';
    
    // Add click handler
    button.addEventListener('click', function() {
      console.log("Running page builder diagnostics...");
      
      // Create modal for displaying results
      const modal = document.createElement('div');
      modal.className = 'modal fade';
      modal.id = 'debugResultsModal';
      modal.setAttribute('tabindex', '-1');
      modal.setAttribute('aria-hidden', 'true');
      
      modal.innerHTML = `
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Page Builder Diagnostics</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
              <div id="debugResults">
                <div class="text-center">
                  <div class="spinner-border text-primary" role="status"></div>
                  <p>Running diagnostics...</p>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Close</button>
            </div>
          </div>
        </div>
      `;
      
      document.body.appendChild(modal);
      
      // Show the modal
      const bsModal = new bootstrap.Modal(modal);
      bsModal.show();
      
      // Run client-side diagnostics
      if (typeof window.debugPageBuilderEditor === 'function') {
        window.debugPageBuilderEditor();
      } else {
        // Load the debug script if not already loaded
        const script = document.createElement('script');
        script.src = '/static/js/debug-page-builder.js';
        script.onload = function() {
          if (typeof window.debugPageBuilderEditor === 'function') {
            window.debugPageBuilderEditor();
          } else {
            console.error("Debug function not found after loading script");
          }
        };
        document.head.appendChild(script);
      }
      
      // Fetch server-side debug information
      fetch('/admin/debug-pages')
        .then(response => response.json())
        .then(data => {
          const resultsDiv = document.getElementById('debugResults');
          
          let html = '<h4>Page Builder Debug Results</h4>';
          
          // Database info
          if (data.database_info) {
            html += '<h5>Database Information</h5>';
            html += '<div class="card mb-3"><div class="card-body">';
            html += '<table class="table table-sm">';
            html += '<thead><tr><th>Table</th><th>Exists</th><th>Record Count</th></tr></thead>';
            html += '<tbody>';
            
            for (const tableName in data.database_info.tables_exist) {
              const exists = data.database_info.tables_exist[tableName];
              const count = data.database_info.record_counts ? data.database_info.record_counts[tableName] : 'N/A';
              
              html += `<tr>
                <td>${tableName}</td>
                <td>${exists ? '✅' : '❌'}</td>
                <td>${count}</td>
              </tr>`;
            }
            
            html += '</tbody></table>';
            html += '</div></div>';
          }
          
          // Tenant info
          html += '<h5>Tenant Information</h5>';
          html += '<div class="card mb-3"><div class="card-body">';
          html += `<p>Selected tenant: ${data.selected_tenant_slug || 'None'}</p>`;
          html += `<p>Found ${data.tenants_count} tenants</p>`;
          html += '</div></div>';
          
          // Page info
          html += '<h5>Page Information</h5>';
          html += '<div class="card mb-3"><div class="card-body">';
          html += `<p>Found ${data.pages_count || 0} pages</p>`;
          
          if (data.pages && data.pages.length > 0) {
            html += '<table class="table table-sm">';
            html += '<thead><tr><th>ID</th><th>Title</th><th>Slug</th></tr></thead>';
            html += '<tbody>';
            
            data.pages.forEach(page => {
              html += `<tr>
                <td>${page.id}</td>
                <td>${page.title}</td>
                <td>${page.slug}</td>
              </tr>`;
            });
            
            html += '</tbody></table>';
          } else {
            html += '<p>No pages found</p>';
          }
          
          html += '</div></div>';
          
          resultsDiv.innerHTML = html;
        })
        .catch(error => {
          document.getElementById('debugResults').innerHTML = 
            `<div class="alert alert-danger">Error fetching debug data: ${error.message}</div>`;
        });
    });
    
    // Add button to the page
    document.body.appendChild(button);
  }
  
  // Run on page load
  if (document.readyState === 'complete') {
    addDebugButton();
  } else {
    window.addEventListener('load', addDebugButton);
  }
})();
