
/**
 * This script adds a debug button to the admin pages list if it doesn't exist
 */
(function() {
  console.log("Checking for debug button...");
  
  // Check if the debug button exists
  const debugBtn = document.getElementById('debugPageBuilderBtn');
  
  if (!debugBtn) {
    console.log("Debug button not found, adding it now");
    
    // Find the button container - typically next to the "Create Page" button
    const headerActions = document.querySelector('.card-header .d-flex.justify-content-between.align-items-center div:last-child');
    
    if (headerActions) {
      // Create the new debug button
      const newDebugBtn = document.createElement('button');
      newDebugBtn.id = 'debugPageBuilderBtn';
      newDebugBtn.className = 'btn btn-secondary btn-sm ms-2';
      newDebugBtn.innerHTML = '<i class="fas fa-bug me-1"></i> Debug Page Builder';
      
      // Add click event to run debug
      newDebugBtn.addEventListener('click', function() {
        console.log("Debug button clicked");
        
        // Create a debug info display area if it doesn't exist
        let debugInfo = document.getElementById('pageBuilderDebugInfo');
        if (!debugInfo) {
          debugInfo = document.createElement('div');
          debugInfo.id = 'pageBuilderDebugInfo';
          debugInfo.className = 'mt-4 p-3 border bg-light';
          document.querySelector('.card-body').appendChild(debugInfo);
        }
        
        // Show loading state
        debugInfo.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">Running diagnostics...</p></div>';
        
        // Fetch debug data
        fetch('/admin/debug-pages')
          .then(response => response.json())
          .then(data => {
            // Display debug information
            let html = '<h4>Page Builder Debug Information</h4>';
            html += '<div class="alert alert-info">This information helps diagnose page builder issues</div>';
            
            // Tenant information
            html += '<h5>Tenant Information</h5>';
            html += `<p>Selected tenant: ${data.selected_tenant_slug || 'None'}</p>`;
            html += `<p>Tenants count: ${data.tenants_count}</p>`;
            
            // Pages information
            html += '<h5>Pages Information</h5>';
            html += `<p>Pages count: ${data.pages_count || 0}</p>`;
            
            // Database information
            if (data.database_info) {
              html += '<h5>Database Information</h5>';
              html += '<table class="table table-sm table-bordered">';
              html += '<thead><tr><th>Table</th><th>Exists</th><th>Records</th></tr></thead><tbody>';
              
              for (const table in data.database_info.tables_exist) {
                html += `<tr>
                  <td>${table}</td>
                  <td>${data.database_info.tables_exist[table] ? '✅' : '❌'}</td>
                  <td>${data.database_info.record_counts ? data.database_info.record_counts[table] : 'N/A'}</td>
                </tr>`;
              }
              
              html += '</tbody></table>';
            }
            
            debugInfo.innerHTML = html;
          })
          .catch(error => {
            console.error('Error fetching debug info:', error);
            debugInfo.innerHTML = `<div class="alert alert-danger">Error fetching debug information: ${error.message}</div>`;
          });
      });
      
      // Add the button to the page
      headerActions.appendChild(newDebugBtn);
      console.log("Debug button added successfully");
    } else {
      console.error("Could not find button container to add debug button");
    }
  } else {
    console.log("Debug button already exists");
  }
})();
/**
 * Add Debug Button
 * 
 * This script adds a debug button to the page for diagnosing editor issues.
 * It can be included directly in the page or loaded dynamically.
 */
(function() {
  // Only add if not already present
  if (document.getElementById('quill-debug-btn')) return;
  
  function addDebugButton() {
    const btn = document.createElement('button');
    btn.id = 'quill-debug-btn';
    btn.className = 'btn btn-info position-fixed';
    btn.style.bottom = '20px';
    btn.style.right = '20px';
    btn.style.zIndex = '9999';
    btn.innerHTML = '<i class="fas fa-bug"></i> Debug Editor';
    
    btn.onclick = function() {
      // Load and run Quill debug utility if not already loaded
      if (typeof PyCommerceQuillDebug === 'undefined') {
        console.log("Loading Quill debug utility...");
        const script = document.createElement('script');
        script.src = '/static/js/quill-debug-utility.js';
        script.onload = function() {
          console.log("Running diagnostics...");
          if (typeof PyCommerceQuillDebug !== 'undefined') {
            PyCommerceQuillDebug.diagnose();
          } else {
            console.error("Failed to load PyCommerceQuillDebug");
          }
        };
        document.head.appendChild(script);
      } else {
        PyCommerceQuillDebug.diagnose();
      }
    };
    
    document.body.appendChild(btn);
    console.log("Debug button added");
  }
  
  // Add the button after a delay to ensure the page is loaded
  setTimeout(addDebugButton, 1000);
})();
