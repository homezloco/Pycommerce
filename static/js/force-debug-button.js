
// Force Debug Button script
console.log("Force debug button script loaded");

document.addEventListener('DOMContentLoaded', function() {
  console.log("DOM fully loaded, checking for debug button...");
  
  // Function to add the debug button
  function addDebugButton() {
    console.log("Adding debug button forcibly");
    
    // Find the container for the button (next to Create Page button)
    const headerActions = document.querySelector('.card-header .d-flex.justify-content-between.align-items-center div:last-child');
    
    if (!headerActions) {
      console.error("Could not find header actions container");
      // Try to find any container we can use
      const anyHeader = document.querySelector('.card-header');
      if (anyHeader) {
        console.log("Found a card header, will add button there");
        // Create a container if none exists
        const newContainer = document.createElement('div');
        newContainer.className = 'd-flex justify-content-between align-items-center';
        anyHeader.appendChild(newContainer);
        
        const buttonContainer = document.createElement('div');
        newContainer.appendChild(buttonContainer);
        
        // Add the debug button to this container
        addButtonToContainer(buttonContainer);
      } else {
        console.error("No suitable container found for debug button");
      }
    } else {
      console.log("Found header actions container");
      // Add button to the existing container
      addButtonToContainer(headerActions);
    }
  }
  
  function addButtonToContainer(container) {
    // Check if button already exists
    if (document.getElementById('debugPageBuilderBtn')) {
      console.log("Debug button already exists, not adding another");
      return;
    }
    
    // Create the debug button
    const debugBtn = document.createElement('button');
    debugBtn.id = 'debugPageBuilderBtn';
    debugBtn.className = 'btn btn-warning btn-sm ms-2';
    debugBtn.innerHTML = '<i class="fas fa-bug me-1"></i> Debug Page Builder';
    
    // Add click event
    debugBtn.addEventListener('click', function() {
      console.log("Debug button clicked");
      debugPageBuilder();
    });
    
    // Add to container
    container.appendChild(debugBtn);
    console.log("Debug button added successfully");
  }
  
  function debugPageBuilder() {
    console.log("Running page builder debug...");
    
    // Create a debug information display area if it doesn't exist
    let debugInfo = document.getElementById('pageBuilderDebugInfo');
    if (!debugInfo) {
      debugInfo = document.createElement('div');
      debugInfo.id = 'pageBuilderDebugInfo';
      debugInfo.className = 'mt-4 p-3 border bg-light';
      
      // Find a good place to add the debug info
      const cardBody = document.querySelector('.card-body');
      if (cardBody) {
        cardBody.appendChild(debugInfo);
      } else {
        // If no card-body found, add it after the first card we find
        const card = document.querySelector('.card');
        if (card && card.parentNode) {
          card.parentNode.insertBefore(debugInfo, card.nextSibling);
        } else {
          // Last resort - add to body
          document.body.appendChild(debugInfo);
        }
      }
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
  }
  
  // Check if we're on the pages list page
  if (window.location.pathname.includes('/admin/pages')) {
    console.log("We are on the pages list page, adding debug button");
    
    // Give the page a moment to fully render
    setTimeout(addDebugButton, 500);
  } else {
    console.log("Not on pages list page, current path: " + window.location.pathname);
  }
});
