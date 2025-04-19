
/**
 * Debug Quill Editor
 * 
 * This script can be added to your page to diagnose issues with the Quill editor.
 * It provides detailed diagnostics and troubleshooting for the PyCommerce page builder.
 */

(function() {
    console.log("===== Quill Editor Diagnostics =====");
    
    // Check for Quill availability
    if (typeof Quill === 'undefined') {
        console.error("❌ Quill is not loaded");
        console.log("Checking for Quill script...");
        
        const quillScript = document.querySelector('script[src*="quill"]');
        if (quillScript) {
            console.log(`Found Quill script: ${quillScript.src}`);
            console.log(`Script load state: ${quillScript.readyState || 'unknown'}`);
        } else {
            console.error("No Quill script found in document");
            console.log("Attempting to load Quill dynamically...");
            
            const script = document.createElement('script');
            script.src = 'https://cdn.quilljs.com/1.3.6/quill.min.js';
            script.onload = function() {
                console.log("✅ Quill loaded dynamically");
                runQuillDiagnostics();
            };
            document.head.appendChild(script);
            
            // Also ensure the CSS is loaded
            if (!document.querySelector('link[href*="quill.snow.css"]')) {
                const link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = 'https://cdn.quilljs.com/1.3.6/quill.snow.css';
                document.head.appendChild(link);
                console.log("✅ Added Quill CSS");
            }
        }
    } else {
        console.log(`✅ Quill is loaded: version ${Quill.version}`);
        runQuillDiagnostics();
    }
    
    function runQuillDiagnostics() {
        // Check for editor containers and instances
        console.log("Checking for Quill containers...");
        
        // Find editor containers (both active and potential)
        const containers = document.querySelectorAll('.ql-container, [id*="quill"], [id*="editor"], [data-quill-editor]');
        console.log(`Found ${containers.length} potential editor containers`);
        
        containers.forEach((container, index) => {
            console.log(`Container #${index}: ${container.id || 'no-id'} (${container.className})`);
            
            // Check if this container has a Quill instance
            try {
                const quillInstance = Quill.find(container);
                if (quillInstance) {
                    console.log(`✅ Active Quill instance found for container #${index}`);
                    console.log(`  - Content length: ${quillInstance.getText().length} characters`);
                    
                    // Check toolbar
                    const toolbar = container.parentNode.querySelector('.ql-toolbar');
                    if (toolbar) {
                        console.log(`  - Toolbar found with ${toolbar.children.length} elements`);
                        
                        // Check for image button and media selector
                        const imageButton = toolbar.querySelector('.ql-image');
                        if (imageButton) {
                            console.log(`  - Image button found`);
                            // Check if we have an event listener
                            const mediaModal = document.getElementById('mediaSelectorModal');
                            if (mediaModal) {
                                console.log(`  - Media selector modal found`);
                            } else {
                                console.warn(`  - No media selector modal found`);
                            }
                        }
                        
                        // Check for AI assist button
                        const aiButton = toolbar.querySelector('.ai-assist-btn');
                        if (aiButton) {
                            console.log(`  - AI assist button found`);
                        }
                    } else {
                        console.warn(`  - No toolbar found for this editor`);
                    }
                } else {
                    console.log(`❌ No Quill instance for container #${index}`);
                }
            } catch (e) {
                console.error(`Error checking container #${index}:`, e);
            }
        });
        
        // Look for potential editor textareas
        const contentTextareas = document.querySelectorAll('textarea[name*="content"], textarea[id*="content"]');
        console.log(`Found ${contentTextareas.length} potential content textareas`);
        
        contentTextareas.forEach((textarea, index) => {
            console.log(`Textarea #${index}: id="${textarea.id || 'none'}", name="${textarea.name || 'none'}"`);
            console.log(`  - Visibility: ${textarea.style.display === 'none' ? 'Hidden (likely has editor)' : 'Visible (no editor)'}`);
            
            // Check if there's a form connection
            const form = textarea.closest('form');
            if (form) {
                console.log(`  - Connected to form: id="${form.id || 'none'}", action="${form.action}"`);
            } else {
                console.warn(`  - Not connected to any form`);
            }
        });
        
        // Check for PyCommerceQuill integration
        if (typeof window.PyCommerceQuill !== 'undefined') {
            console.log("✅ PyCommerceQuill integration available");
            console.log(`  - Has init method: ${typeof window.PyCommerceQuill.init === 'function' ? 'Yes' : 'No'}`);
            console.log(`  - Editor instances tracked: ${Object.keys(window.PyCommerceQuill).filter(key => key !== 'init' && key !== 'loadQuill').length}`);
            
            // Try to auto-fix any textareas that don't have editors
            contentTextareas.forEach((editor, index) => {
                if (editor.tagName === 'TEXTAREA' && !editor.hasAttribute('data-quill-editor')) {
                    console.log(`Adding data-quill-editor to ${editor.id || 'unnamed textarea'}`);
                    editor.setAttribute('data-quill-editor', '');
                    editor.setAttribute('data-quill-height', '400px');
                }
            });
            
            // Check if initialization can be triggered
            if (window.PyCommerceQuill.init) {
                console.log("PyCommerceQuill.init is available for manual initialization");
            }
        } else {
            console.warn("❌ PyCommerceQuill integration is not available");
        }
    }
    
    // Add "Fix Quill" button to repair common issues
    function addFixQuillButton() {
        // Only add if not already present
        if (document.getElementById('fix-quill-btn')) return;
        
        const btn = document.createElement('button');
        btn.id = 'fix-quill-btn';
        btn.className = 'btn btn-warning position-fixed';
        btn.style.bottom = '60px';
        btn.style.right = '20px';
        btn.style.zIndex = '9999';
        btn.innerHTML = '<i class="fas fa-wrench"></i> Fix Editor';
        
        btn.onclick = function() {
            console.log("Attempting to fix Quill editor issues...");
            
            // Step 1: Ensure Quill is loaded
            if (typeof Quill === 'undefined') {
                const script = document.createElement('script');
                script.src = 'https://cdn.quilljs.com/1.3.6/quill.min.js';
                script.onload = function() {
                    console.log("✅ Loaded Quill");
                    fixQuillStep2();
                };
                document.head.appendChild(script);
                
                // Add CSS too
                if (!document.querySelector('link[href*="quill.snow.css"]')) {
                    const link = document.createElement('link');
                    link.rel = 'stylesheet';
                    link.href = 'https://cdn.quilljs.com/1.3.6/quill.snow.css';
                    document.head.appendChild(link);
                }
            } else {
                fixQuillStep2();
            }
        };
        
        document.body.appendChild(btn);
        console.log("Added Fix Quill button to the page");
    }
    
    // Step 2 of fixing - ensure PyCommerceQuill is loaded
    function fixQuillStep2() {
        if (typeof window.PyCommerceQuill === 'undefined') {
            console.log("Loading PyCommerceQuill integration...");
            const script = document.createElement('script');
            script.src = '/static/js/quill-integration.js';
            script.onload = function() {
                console.log("✅ Loaded PyCommerceQuill integration");
                fixQuillStep3();
            };
            document.head.appendChild(script);
        } else {
            fixQuillStep3();
        }
    }
    
    // Step 3 - initialize editors
    function fixQuillStep3() {
        console.log("Initializing editors on content textareas...");
        const contentTextareas = document.querySelectorAll('textarea[name*="content"], textarea[id*="content"]');
        
        if (contentTextareas.length === 0) {
            console.warn("No content textareas found to initialize");
            return;
        }
        
        contentTextareas.forEach((textarea, index) => {
            // Skip if already hidden (might already have an editor)
            if (textarea.style.display === 'none') {
                console.log(`Textarea ${textarea.id || index} already appears to have an editor`);
                return;
            }
            
            console.log(`Initializing editor for ${textarea.id || 'unnamed textarea'}`);
            
            // Create a container for the editor
            const containerId = `quill-container-${textarea.id || index}`;
            let container = document.getElementById(containerId);
            
            if (!container) {
                container = document.createElement('div');
                container.id = containerId;
                container.style.height = '400px';
                container.style.marginBottom = '20px';
                textarea.parentNode.insertBefore(container, textarea);
            }
            
            // Hide the textarea
            textarea.style.display = 'none';
            
            // Initialize Quill
            try {
                if (window.PyCommerceQuill && window.PyCommerceQuill.init) {
                    window.PyCommerceQuill.init({
                        targetSelector: `#${textarea.id}`,
                        containerId: containerId,
                        formSelector: textarea.closest('form') ? `#${textarea.closest('form').id}` : 'form',
                        height: '400px'
                    });
                    console.log(`✅ Initialized PyCommerceQuill editor for ${textarea.id || 'unnamed textarea'}`);
                } else {
                    // Direct Quill initialization
                    const quill = new Quill(`#${containerId}`, {
                        modules: {
                            toolbar: [
                                ['bold', 'italic', 'underline', 'strike'],
                                ['blockquote', 'code-block'],
                                [{ 'header': 1 }, { 'header': 2 }],
                                [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                                [{ 'indent': '-1'}, { 'indent': '+1' }],
                                [{ 'size': ['small', false, 'large', 'huge'] }],
                                [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
                                [{ 'color': [] }, { 'background': [] }],
                                [{ 'align': [] }],
                                ['clean'],
                                ['link', 'image']
                            ]
                        },
                        theme: 'snow'
                    });
                    
                    // Handle form submission
                    const form = textarea.closest('form');
                    if (form) {
                        form.addEventListener('submit', function() {
                            textarea.value = quill.root.innerHTML;
                        });
                    }
                    
                    console.log(`✅ Initialized direct Quill editor for ${textarea.id || 'unnamed textarea'}`);
                }
            } catch (e) {
                console.error(`Failed to initialize editor for ${textarea.id || 'unnamed textarea'}:`, e);
            }
        });
        
        console.log("Editor initialization complete");
    }
    
    // Add debug and fix buttons to the page
    setTimeout(function() {
        // Add debug button
        const debugBtn = document.createElement('button');
        debugBtn.id = 'debug-quill-btn';
        debugBtn.className = 'btn btn-info position-fixed';
        debugBtn.style.bottom = '20px';
        debugBtn.style.right = '20px';
        debugBtn.style.zIndex = '9999';
        debugBtn.innerHTML = '<i class="fas fa-bug"></i> Debug Editor';
        
        debugBtn.onclick = function() {
            runQuillDiagnostics();
        };
        
        document.body.appendChild(debugBtn);
        console.log("Added Debug Quill button to the page");
        
        // Add fix button
        addFixQuillButton();
    }, 1000);
    
    console.log("===== End Diagnostics =====");
})();
