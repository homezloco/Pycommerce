
/**
 * Debug script to check JavaScript execution in the page editor.
 * Add this to the console while on the page editor to diagnose issues.
 */

(function() {
  console.log("===== Page Editor Debug =====");
  
  // Check if TinyMCE is loaded
  if (typeof tinymce === 'undefined') {
    console.error("❌ TinyMCE is not loaded");
  } else {
    console.log("✅ TinyMCE is loaded:", tinymce.majorVersion + "." + tinymce.minorVersion);
    
    // Check active editors
    const editors = tinymce.get();
    console.log(`TinyMCE editors: ${editors.length}`);
    editors.forEach(editor => {
      console.log(`- Editor ID: ${editor.id}`);
    });
  }
  
  // Check if Bootstrap is properly loaded
  if (typeof bootstrap === 'undefined') {
    console.error("❌ Bootstrap JS is not loaded");
  } else {
    console.log("✅ Bootstrap JS is loaded");
    
    // Check modal functionality
    const modalElements = document.querySelectorAll('.modal');
    console.log(`Found ${modalElements.length} modal elements`);
    
    try {
      modalElements.forEach(element => {
        const modalInstance = bootstrap.Modal.getInstance(element);
        console.log(`- Modal ${element.id}: ${modalInstance ? 'instance found' : 'no instance'}`);
      });
    } catch (e) {
      console.error("Error checking modal instances:", e);
    }
  }
  
  // Check event listeners on key elements
  try {
    const addSectionBtn = document.getElementById('addSectionBtn');
    const savePageBtn = document.getElementById('savePageBtn');
    
    if (addSectionBtn) {
      console.log("✅ Add Section button found");
    } else {
      console.error("❌ Add Section button not found");
    }
    
    if (savePageBtn) {
      console.log("✅ Save Page button found");
    } else {
      console.error("❌ Save Page button not found");
    }
  } catch (e) {
    console.error("Error checking page editor buttons:", e);
  }
  
  // Check the API endpoints
  try {
    const testApi = async (url, method = 'GET') => {
      try {
        const response = await fetch(url, { method });
        return {
          status: response.status,
          ok: response.ok
        };
      } catch (e) {
        return { error: e.message };
      }
    };
    
    // Test API endpoints asynchronously
    (async () => {
      console.log("Testing API endpoints...");
      
      const apiTests = [
        await testApi('/admin/api/pages'),
        await testApi('/admin/debug-pages'),
        await testApi('/admin/pages')
      ];
      
      console.log("API test results:", apiTests);
    })();
    
  } catch (e) {
    console.error("Error testing API endpoints:", e);
  }
  
  console.log("===== End Debug =====");
})();


/**
 * Debug script to check JavaScript execution in the page editor.
 * Add this to the console while on the page editor to diagnose issues.
 */

(function() {
  console.log("===== Page Editor Debug =====");
  
  // Check if TinyMCE is loaded
  if (typeof tinymce === 'undefined') {
    console.error("❌ TinyMCE is not loaded");
  } else {
    console.log("✅ TinyMCE is loaded:", tinymce.majorVersion + "." + tinymce.minorVersion);
    
    // Check active editors
    const editors = tinymce.get();
    console.log(`TinyMCE editors: ${editors.length}`);
    editors.forEach(editor => {
      console.log(`- Editor ID: ${editor.id}`);
    });
  }
  
  // Check if Bootstrap is properly loaded
  if (typeof bootstrap === 'undefined') {
    console.error("❌ Bootstrap JS is not loaded");
  } else {
    console.log("✅ Bootstrap JS is loaded");
    
    // Check modal functionality
    const modalElements = document.querySelectorAll('.modal');
    console.log(`Found ${modalElements.length} modal elements`);
    
    try {
      modalElements.forEach(element => {
        const modalInstance = bootstrap.Modal.getInstance(element);
        console.log(`- Modal ${element.id}: ${modalInstance ? 'instance found' : 'no instance'}`);
      });
    } catch (e) {
      console.error("Error checking modal instances:", e);
    }
  }
  
  // Check event listeners on key elements
  try {
    const addSectionBtn = document.getElementById('addSectionBtn');
    const savePageBtn = document.getElementById('savePageBtn');
    
    if (addSectionBtn) {
      console.log("✅ Add Section button found");
    } else {
      console.error("❌ Add Section button not found");
    }
    
    if (savePageBtn) {
      console.log("✅ Save Page button found");
    } else {
      console.error("❌ Save Page button not found");
    }
  } catch (e) {
    console.error("Error checking page editor buttons:", e);
  }
  
  // Check the API endpoints
  try {
    const testApi = async (url, method = 'GET') => {
      try {
        const response = await fetch(url, { method });
        return {
          status: response.status,
          ok: response.ok
        };
      } catch (e) {
        return { error: e.message };
      }
    };
    
    // Test API endpoints asynchronously
    (async () => {
      console.log("Testing API endpoints...");
      
      const apiTests = [
        await testApi('/admin/api/pages'),
        await testApi('/admin/debug-pages'),
        await testApi('/admin/pages')
      ];
      
      console.log("API test results:", apiTests);
    })();
    
  } catch (e) {
    console.error("Error testing API endpoints:", e);
  }
  
  console.log("===== End Debug =====");
})();
