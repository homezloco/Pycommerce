
/**
 * Debug script to check JavaScript execution in the page editor.
 * Add this to the console while on the page editor to diagnose issues.
 */

(function() {
  console.log("===== Page Editor Debug =====");

  // Check if Quill is loaded
  if (typeof Quill === 'undefined') {
    console.error("❌ Quill is not loaded");
    console.log("Make sure Quill.js CDN is properly included in the page");
    
    // Try to load Quill dynamically
    const script = document.createElement('script');
    script.src = 'https://cdn.quilljs.com/1.3.6/quill.min.js';
    script.onload = function() {
      console.log("✅ Quill loaded dynamically");
      // Re-run this debugging script after loading
      setTimeout(() => {
        console.log("Re-running debug after loading Quill...");
        eval(document.currentScript.innerText);
      }, 500);
    };
    document.head.appendChild(script);
  } else {
    console.log("✅ Quill is loaded:", Quill.version);

    // Check active editors
    const editors = document.querySelectorAll('.ql-container');
    console.log(`Found ${editors.length} Quill editor containers`);

    editors.forEach((container, index) => {
      try {
        const quillInstance = Quill.find(container);
        if (quillInstance) {
          console.log(`- Quill editor #${index}: active`);
          console.log(`  - Content length: ${quillInstance.getText().length} characters`);
        } else {
          console.log(`- Quill container #${index}: no Quill instance`);
        }
      } catch (e) {
        console.error(`- Error checking editor #${index}:`, e);
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
      modalElements.forEach((element, index) => {
        console.log(`- Modal #${index} id: ${element.id || 'no-id'}`);
        try {
          const modalInstance = bootstrap.Modal.getInstance(element);
          console.log(`  - Modal instance: ${modalInstance ? 'found' : 'not initialized'}`);
        } catch (e) {
          console.error(`  - Error getting modal instance:`, e);
        }
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
      console.log(`  - Button text: "${addSectionBtn.innerText}"`);
    } else {
      console.error("❌ Add Section button not found");
      const possibleButtons = document.querySelectorAll('button');
      console.log(`  - Found ${possibleButtons.length} other buttons on the page`);
      const addButtons = Array.from(possibleButtons).filter(btn => 
        btn.innerText.toLowerCase().includes('add') || 
        btn.innerText.toLowerCase().includes('section'));
      if (addButtons.length > 0) {
        console.log(`  - Possible add section buttons found:`, 
          addButtons.map(btn => `"${btn.innerText}" (id: ${btn.id || 'none'})`).join(', '));
      }
    }

    if (savePageBtn) {
      console.log("✅ Save Page button found");
      console.log(`  - Button text: "${savePageBtn.innerText}"`);
    } else {
      console.error("❌ Save Page button not found");
      const possibleButtons = document.querySelectorAll('button');
      const saveButtons = Array.from(possibleButtons).filter(btn => 
        btn.innerText.toLowerCase().includes('save') || 
        btn.innerText.toLowerCase().includes('page'));
      if (saveButtons.length > 0) {
        console.log(`  - Possible save page buttons found:`, 
          saveButtons.map(btn => `"${btn.innerText}" (id: ${btn.id || 'none'})`).join(', '));
      }
    }
  } catch (e) {
    console.error("Error checking page editor buttons:", e);
  }

  // Check the API endpoints
  try {
    const testApi = async (url, method = 'GET') => {
      try {
        console.log(`Testing API endpoint: ${url}`);
        const response = await fetch(url, { method });
        
        if (!response.ok) {
          console.error(`API endpoint ${url} returned status ${response.status}`);
        } else {
          console.log(`API endpoint ${url} returned status ${response.status} (OK)`);
        }
        
        return {
          url,
          status: response.status,
          ok: response.ok
        };
      } catch (e) {
        console.error(`Error fetching ${url}:`, e.message);
        return { url, error: e.message };
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
      aiButtons.forEach((btn, i) => {
        console.log(`  - AI Button #${i} text: "${btn.innerText}"`);
      });
    } else {
      console.warn("⚠️ No AI Assist buttons found in Quill toolbar");
      // Look for any buttons in toolbar that might be AI-related
      const toolbars = document.querySelectorAll('.ql-toolbar');
      if (toolbars.length > 0) {
        const allToolbarButtons = Array.from(toolbars).flatMap(tb => 
          Array.from(tb.querySelectorAll('button')));
        console.log(`  - Found ${allToolbarButtons.length} total buttons in Quill toolbars`);
        
        const aiRelatedButtons = allToolbarButtons.filter(btn => 
          btn.innerText.toLowerCase().includes('ai') || 
          btn.className.toLowerCase().includes('ai'));
        
        if (aiRelatedButtons.length > 0) {
          console.log(`  - Possible AI-related buttons:`, 
            aiRelatedButtons.map(btn => `"${btn.innerText}" (class: ${btn.className})`).join(', '));
        }
      }
    }
  } catch (e) {
    console.error("Error checking AI buttons:", e);
  }

  console.log("===== End Debug =====");
})();
/**
 * Debug script to check JavaScript execution in the page editor.
 * Add this to the console while on the page editor to diagnose issues.
 */

(function() {
  console.log("===== Page Editor Debug =====");

  // Check if Quill is loaded
  if (typeof Quill === 'undefined') {
    console.error("❌ Quill is not loaded");
    console.log("Make sure Quill.js CDN is properly included in the page");
    
    // Try to load Quill dynamically
    const script = document.createElement('script');
    script.src = 'https://cdn.quilljs.com/1.3.6/quill.min.js';
    script.onload = function() {
      console.log("✅ Quill loaded dynamically");
      // Re-run this debugging script after loading
      setTimeout(() => {
        console.log("Re-running debug after loading Quill...");
        eval(document.currentScript.innerText);
      }, 500);
    };
    document.head.appendChild(script);
  } else {
    console.log("✅ Quill is loaded:", Quill.version);

    // Check active editors
    const editors = document.querySelectorAll('.ql-container');
    console.log(`Found ${editors.length} Quill editor containers`);

    editors.forEach((container, index) => {
      try {
        const quillInstance = Quill.find(container);
        if (quillInstance) {
          console.log(`- Quill editor #${index}: active`);
          console.log(`  - Content length: ${quillInstance.getText().length} characters`);
        } else {
          console.log(`- Quill container #${index}: no Quill instance`);
        }
      } catch (e) {
        console.error(`- Error checking editor #${index}:`, e);
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
      modalElements.forEach((element, index) => {
        console.log(`- Modal #${index} id: ${element.id || 'no-id'}`);
        try {
          const modalInstance = bootstrap.Modal.getInstance(element);
          console.log(`  - Modal instance: ${modalInstance ? 'found' : 'not initialized'}`);
        } catch (e) {
          console.error(`  - Error getting modal instance:`, e);
        }
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
      console.log(`  - Button text: "${addSectionBtn.innerText}"`);
    } else {
      console.error("❌ Add Section button not found");
      const possibleButtons = document.querySelectorAll('button');
      console.log(`  - Found ${possibleButtons.length} other buttons on the page`);
      const addButtons = Array.from(possibleButtons).filter(btn => 
        btn.innerText.toLowerCase().includes('add') || 
        btn.innerText.toLowerCase().includes('section'));
      if (addButtons.length > 0) {
        console.log(`  - Possible add section buttons found:`, 
          addButtons.map(btn => `"${btn.innerText}" (id: ${btn.id || 'none'})`).join(', '));
      }
    }

    if (savePageBtn) {
      console.log("✅ Save Page button found");
      console.log(`  - Button text: "${savePageBtn.innerText}"`);
    } else {
      console.error("❌ Save Page button not found");
      const possibleButtons = document.querySelectorAll('button');
      const saveButtons = Array.from(possibleButtons).filter(btn => 
        btn.innerText.toLowerCase().includes('save') || 
        btn.innerText.toLowerCase().includes('page'));
      if (saveButtons.length > 0) {
        console.log(`  - Possible save page buttons found:`, 
          saveButtons.map(btn => `"${btn.innerText}" (id: ${btn.id || 'none'})`).join(', '));
      }
    }
  } catch (e) {
    console.error("Error checking page editor buttons:", e);
  }

  // Check the API endpoints
  try {
    const testApi = async (url, method = 'GET') => {
      try {
        console.log(`Testing API endpoint: ${url}`);
        const response = await fetch(url, { method });
        
        if (!response.ok) {
          console.error(`API endpoint ${url} returned status ${response.status}`);
        } else {
          console.log(`API endpoint ${url} returned status ${response.status} (OK)`);
        }
        
        return {
          url,
          status: response.status,
          ok: response.ok
        };
      } catch (e) {
        console.error(`Error fetching ${url}:`, e.message);
        return { url, error: e.message };
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
      aiButtons.forEach((btn, i) => {
        console.log(`  - AI Button #${i} text: "${btn.innerText}"`);
      });
    } else {
      console.warn("⚠️ No AI Assist buttons found in Quill toolbar");
      // Look for any buttons in toolbar that might be AI-related
      const toolbars = document.querySelectorAll('.ql-toolbar');
      if (toolbars.length > 0) {
        const allToolbarButtons = Array.from(toolbars).flatMap(tb => 
          Array.from(tb.querySelectorAll('button')));
        console.log(`  - Found ${allToolbarButtons.length} total buttons in Quill toolbars`);
        
        const aiRelatedButtons = allToolbarButtons.filter(btn => 
          btn.innerText.toLowerCase().includes('ai') || 
          btn.className.toLowerCase().includes('ai'));
        
        if (aiRelatedButtons.length > 0) {
          console.log(`  - Possible AI-related buttons:`, 
            aiRelatedButtons.map(btn => `"${btn.innerText}" (class: ${btn.className})`).join(', '));
        }
      }
    }
  } catch (e) {
    console.error("Error checking AI buttons:", e);
  }

  console.log("===== End Debug =====");
})();
