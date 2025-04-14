
/**
 * Debug script to check JavaScript execution in the page editor.
 * Add this to the console while on the page editor to diagnose issues.
 */

(function() {
  console.log("===== Page Editor Debug =====");

  // Check if Quill is loaded
  if (typeof Quill === 'undefined') {
    console.error("❌ Quill is not loaded");
  } else {
    console.log("✅ Quill is loaded:", Quill.version);

    // Check active editors
    const editors = document.querySelectorAll('.ql-container');
    console.log(`Quill editor containers: ${editors.length}`);

    editors.forEach((container, index) => {
      const quillInstance = Quill.find(container);
      if (quillInstance) {
        console.log(`- Quill editor #${index}: active`);
        console.log(`  - Content length: ${quillInstance.getText().length} characters`);
      } else {
        console.log(`- Quill editor container #${index}: no Quill instance`);
      }
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

  // Check for the AI Assist button in Quill toolbar
  try {
    const aiButtons = document.querySelectorAll('.ql-toolbar .btn-primary');
    if (aiButtons.length > 0) {
      console.log(`✅ Found ${aiButtons.length} AI Assist buttons`);
    } else {
      console.warn("⚠️ No AI Assist buttons found in Quill toolbar");
    }
  } catch (e) {
    console.error("Error checking AI buttons:", e);
  }

  console.log("===== End Debug =====");
})();
