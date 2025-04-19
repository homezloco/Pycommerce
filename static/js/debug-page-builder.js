/**
 * Debug script to check JavaScript execution in the page editor.
 * This file can be included in the page or executed via the console
 * to diagnose issues with the page builder.
 */

window.debugPageBuilderEditor = function() {
  console.log("===== Page Editor Debug =====");

  // Check if Quill debug utility is loaded
  if (typeof PyCommerceQuillDebug !== 'undefined') {
    console.log("Running PyCommerceQuillDebug diagnostic...");
    PyCommerceQuillDebug.diagnose();
    return;
  }

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
        window.debugPageBuilderEditor();
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

  // Check for AI Assist button in Quill toolbar
  try {
    const aiButtons = document.querySelectorAll('.ql-toolbar .btn-primary, .ql-toolbar .ai-assist-btn');
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

    // Add repair function if no AI buttons found
    if (aiButtons.length === 0 && typeof window.PyCommerceQuill !== 'undefined') {
      console.log("Checking if we can add missing AI assist button...");
      const toolbars = document.querySelectorAll('.ql-toolbar');
      if (toolbars.length > 0) {
        toolbars.forEach((toolbar, i) => {
          if (!toolbar.querySelector('.ai-assist-btn')) {
            console.log(`Adding missing AI assist button to toolbar #${i}`);
            const aiButton = document.createElement('button');
            aiButton.className = 'btn btn-primary btn-sm ms-2 ai-assist-btn';
            aiButton.innerHTML = '<i class="fas fa-robot"></i> AI Assist';
            aiButton.type = 'button';

            aiButton.onclick = function() {
              const modal = document.getElementById('aiAssistModal');
              if (modal && typeof bootstrap !== 'undefined') {
                const modalInstance = new bootstrap.Modal(modal);
                modalInstance.show();
              }
            };

            toolbar.appendChild(aiButton);
          }
        });
      }
    }
  } catch (e) {
    console.error("Error checking AI buttons:", e);
  }

  // Check media selector functionality
  try {
    const mediaSelectorModal = document.getElementById('mediaSelectorModal');
    if (mediaSelectorModal) {
      console.log("✅ Media selector modal found");

      // Check if the media selector function exists
      if (typeof window.openMediaSelector === 'function') {
        console.log("✅ openMediaSelector function available");
      } else {
        console.warn("⚠️ openMediaSelector function not defined");

        // Try to add the function if missing
        if (!window.openMediaSelector) {
          console.log("Adding missing openMediaSelector function");
          window.openMediaSelector = function(callback) {
            window.mediaSelectionCallback = callback;

            // Show the media selector modal
            if (typeof bootstrap !== 'undefined') {
              const mediaSelectorModal = new bootstrap.Modal(document.getElementById('mediaSelectorModal'));
              mediaSelectorModal.show();
            }

            // Load media items
            if (typeof loadMediaItems === 'function') {
              loadMediaItems();
            }
          };
        }
      }
    } else {
      console.warn("❌ Media selector modal not found");
    }
  } catch (e) {
    console.error("Error checking media selector:", e);
  }

  console.log("===== End Debug =====");
};

// Auto-run debug when loaded on a page with content editor
document.addEventListener('DOMContentLoaded', function() {
  // Check if we're on a page that might have the editor
  const hasContentEditor = document.querySelector('#content') || 
                          document.querySelector('[id*="editor"]') || 
                          document.querySelector('textarea[name*="content"]');

  if (hasContentEditor) {
    console.log("Content editor detected, running automatic debug...");
    setTimeout(window.debugPageBuilderEditor, 1000);
  }
});

// Add a debug button to the page for easy testing
function addDebugButton() {
  if (document.getElementById('quill-debug-button')) {
    return; // Button already exists
  }

  const button = document.createElement('button');
  button.id = 'quill-debug-button';
  button.className = 'btn btn-sm btn-info position-fixed';
  button.style.bottom = '20px';
  button.style.right = '20px';
  button.style.zIndex = '9999';
  button.innerHTML = '<i class="fas fa-bug"></i> Debug Quill';
  button.onclick = function() {
    window.debugPageBuilderEditor();
  };

  document.body.appendChild(button);
  console.log("Debug button added to page");
}

// Try to add the debug button when the script loads
setTimeout(addDebugButton, 1500);
/**
 * Debug utility for the page builder interface
 * This script provides helpful diagnostics and troubleshooting for the page builder
 */

(function() {
    console.log("===== Page Builder Debug Utility =====");
    
    window.debugPageBuilderEditor = function() {
        console.log("Running page builder editor diagnostics...");
        
        // Check for editor container
        const editorContainer = document.querySelector('#content, #page-editor-container, [data-page-builder]');
        if (!editorContainer) {
            console.error("❌ No page editor container found");
            return false;
        }
        
        console.log(`✅ Found editor container: ${editorContainer.id || editorContainer.className}`);
        
        // Check for Quill integration
        if (typeof Quill !== 'undefined') {
            console.log("✅ Quill is available");
            
            // Check if there's a Quill instance
            try {
                const quillInstance = Quill.find(editorContainer);
                if (quillInstance) {
                    console.log("✅ Active Quill instance found");
                    console.log(`   - Content length: ${quillInstance.getText().length} characters`);
                } else {
                    console.warn("⚠️ No Quill instance found for the editor container");
                }
            } catch (e) {
                console.error("❌ Error checking Quill instance:", e);
            }
        } else {
            console.error("❌ Quill is not loaded");
        }
        
        // Check form integration
        const form = editorContainer.closest('form');
        if (form) {
            console.log(`✅ Editor is within a form: ${form.id || 'unnamed form'}`);
            console.log(`   - Form action: ${form.action}`);
            console.log(`   - Form method: ${form.method}`);
            
            // Check for submit handler
            const formSubmitEvents = getEventListeners(form, 'submit');
            console.log(`   - Form has ${formSubmitEvents.length} submit handlers`);
        } else {
            console.warn("⚠️ Editor is not within a form");
        }
        
        // Check for media selector integration
        const mediaSelectorModal = document.getElementById('mediaSelectorModal');
        if (mediaSelectorModal) {
            console.log("✅ Media selector modal found");
            
            // Check if it's properly initialized with Bootstrap
            if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                try {
                    const modalInstance = bootstrap.Modal.getInstance(mediaSelectorModal);
                    console.log(`   - Modal initialized: ${modalInstance !== null}`);
                } catch (e) {
                    console.warn("⚠️ Modal not properly initialized:", e);
                }
            } else {
                console.warn("⚠️ Bootstrap modal functionality not available");
            }
        } else {
            console.warn("⚠️ Media selector modal not found");
        }
        
        // Check for page sections handling
        const pageSections = document.querySelectorAll('.page-section, [data-section-id]');
        if (pageSections.length > 0) {
            console.log(`✅ Found ${pageSections.length} page sections`);
            
            pageSections.forEach((section, index) => {
                const sectionId = section.dataset.sectionId || 'unknown';
                const sectionType = section.dataset.sectionType || 'unknown';
                console.log(`   - Section #${index + 1}: ID=${sectionId}, Type=${sectionType}`);
            });
        } else {
            console.log("ℹ️ No page sections found (may be a new page)");
        }
        
        // Check content blocks
        const contentBlocks = document.querySelectorAll('.content-block, [data-block-id]');
        if (contentBlocks.length > 0) {
            console.log(`✅ Found ${contentBlocks.length} content blocks`);
        } else {
            console.log("ℹ️ No content blocks found (may be a new page)");
        }
        
        // Check template functionality
        if (window.pageBuilderTemplates) {
            console.log(`✅ Page builder templates available: ${Object.keys(window.pageBuilderTemplates).length} templates`);
        } else {
            console.warn("⚠️ Page builder templates not defined");
        }
        
        console.log("===== End of Page Builder Diagnostics =====");
        return true;
    };
    
    // Helper function to get event listeners (browser support varies)
    function getEventListeners(element, eventType) {
        // This is a simplified version since getEventListeners is only in Chrome DevTools
        try {
            // For browsers that support getEventListeners in console
            if (window.getEventListeners) {
                return window.getEventListeners(element)[eventType] || [];
            } else {
                // For browsers that don't support it, we can't reliably tell
                return [];
            }
        } catch (e) {
            console.log("Cannot determine event listeners count");
            return [];
        }
    }
    
    // Auto-run detection on page load
    setTimeout(function() {
        // Only run on pages that likely have the page builder
        if (document.querySelector('#content, #page-editor-container, [data-page-builder]')) {
            console.log("Page builder detected, debug utility ready (call window.debugPageBuilderEditor() to run diagnostics)");
        }
    }, 1000);
})();
