
/**
 * Debug script for Page Builder
 * Add this to your page to diagnose issues with the page builder
 */

console.log("Page Builder Debug Helper loaded");

(function() {
  // Check if required libraries are loaded
  const libraries = {
    "jQuery": typeof jQuery !== 'undefined',
    "Bootstrap": typeof bootstrap !== 'undefined',
    "TinyMCE": typeof tinymce !== 'undefined',
    "Quill": typeof Quill !== 'undefined',
    "Sortable": typeof Sortable !== 'undefined'
  };

  console.log("Library status:", libraries);

  // Check template elements
  const elements = {
    "Page container": document.getElementById('pageContainer') !== null,
    "Editor container": document.querySelector('.editor-container') !== null,
    "Sections container": document.getElementById('sectionsContainer') !== null,
    "Add section button": document.getElementById('addSectionBtn') !== null,
    "Save page button": document.getElementById('savePageBtn') !== null
  };

  console.log("Elements status:", elements);

  // Add a button to help debug
  const debugButton = document.createElement('button');
  debugButton.innerText = 'Debug Page Builder';
  debugButton.className = 'btn btn-warning position-fixed';
  debugButton.style.bottom = '20px';
  debugButton.style.right = '20px';
  debugButton.style.zIndex = '9999';
  
  debugButton.onclick = function() {
    alert('Page Builder Debug Information: Check console for details');
    console.log('Page Builder Debug triggered manually');
    
    // Check templates
    const templatePaths = [
      '/admin/pages/list.html',
      '/admin/pages/create.html',
      '/admin/pages/editor.html'
    ];
    
    console.log("Checking template accessibility...");
    templatePaths.forEach(path => {
      fetch(path)
        .then(response => {
          console.log(`Template ${path}: ${response.status === 200 ? 'Accessible' : 'Not accessible'}`);
        })
        .catch(error => {
          console.error(`Error checking template ${path}:`, error);
        });
    });
  };
  
  document.body.appendChild(debugButton);
})();
