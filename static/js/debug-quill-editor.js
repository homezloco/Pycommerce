
/**
 * Debug Quill Editor
 * 
 * This script can be added to your page to diagnose issues with the Quill editor.
 * Copy this to the browser console to run the diagnostics.
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
        
        // Check for textareas that might be intended for editors
        const richTextareas = document.querySelectorAll('textarea[name*="content"], textarea[name*="body"], textarea[name*="text"], textarea[id*="content"], textarea[id*="editor"]');
        console.log(`Found ${richTextareas.length} textareas that might be intended for rich text editing`);
        
        richTextareas.forEach((textarea, index) => {
            console.log(`Textarea #${index}: ${textarea.id || 'no-id'} (name: ${textarea.name})`);
            console.log(`  - Visible: ${textarea.style.display !== 'none'}`);
            console.log(`  - Has content: ${textarea.value.length > 0 ? 'Yes' : 'No'}`);
            
            // Check if there's a Quill container nearby
            const siblings = Array.from(textarea.parentNode.children);
            const nearbyQuillContainer = siblings.find(el => el.className.includes('ql-container') || el.id?.includes('quill'));
            
            if (nearbyQuillContainer) {
                console.log(`  - Has nearby Quill container: ${nearbyQuillContainer.id || 'unnamed'}`);
            } else {
                console.log(`  - No nearby Quill container`);
            }
        });
        
        // Check for forms that might submit editor content
        const forms = document.querySelectorAll('form');
        console.log(`Found ${forms.length} forms that might contain editors`);
        
        forms.forEach((form, index) => {
            const richTextareas = form.querySelectorAll('textarea[id*="content"], textarea[id*="editor"], [data-quill-editor]');
            if (richTextareas.length > 0) {
                console.log(`Form #${index}: ${form.id || 'no-id'} has ${richTextareas.length} potential rich text fields`);
                
                // Check for submit handlers
                const hasInlineHandler = form.hasAttribute('onsubmit');
                const hasEventHandler = typeof jQuery !== 'undefined' ? 
                    jQuery._data(form, "events")?.submit?.length > 0 : 
                    form._events?.submit?.length > 0;
                
                console.log(`  - Has inline submit handler: ${hasInlineHandler}`);
                console.log(`  - Has event submit handler: ${hasEventHandler ? 'Yes' : 'Unknown'}`);
            }
        });
        
        // Check for PyCommerceQuill
        if (typeof window.PyCommerceQuill !== 'undefined') {
            console.log("✅ PyCommerceQuill integration is available");
            
            // Try to fix any issues automatically
            const potentialEditors = document.querySelectorAll('[id*="content"], [id*="editor"], textarea[name*="content"]');
            console.log(`Found ${potentialEditors.length} potential editors that could be initialized`);
            
            potentialEditors.forEach((editor, index) => {
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
    
    console.log("===== End Diagnostics =====");
})();
/**
 * Debug Quill Editor
 * 
 * This script can be added to your page to diagnose issues with the Quill editor.
 * Copy this to the browser console to run the diagnostics.
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
        
        // Check for textareas that might be intended for editors
        const richTextareas = document.querySelectorAll('textarea[name*="content"], textarea[name*="body"], textarea[name*="text"], textarea[id*="content"], textarea[id*="editor"]');
        console.log(`Found ${richTextareas.length} textareas that might be intended for rich text editing`);
        
        richTextareas.forEach((textarea, index) => {
            console.log(`Textarea #${index}: ${textarea.id || 'no-id'} (name: ${textarea.name})`);
            console.log(`  - Visible: ${textarea.style.display !== 'none'}`);
            console.log(`  - Has content: ${textarea.value.length > 0 ? 'Yes' : 'No'}`);
            
            // Check if there's a Quill container nearby
            const siblings = Array.from(textarea.parentNode.children);
            const nearbyQuillContainer = siblings.find(el => el.className.includes('ql-container') || el.id?.includes('quill'));
            
            if (nearbyQuillContainer) {
                console.log(`  - Has nearby Quill container: ${nearbyQuillContainer.id || 'unnamed'}`);
            } else {
                console.log(`  - No nearby Quill container`);
            }
        });
        
        // Check for forms that might submit editor content
        const forms = document.querySelectorAll('form');
        console.log(`Found ${forms.length} forms that might contain editors`);
        
        forms.forEach((form, index) => {
            const richTextareas = form.querySelectorAll('textarea[id*="content"], textarea[id*="editor"], [data-quill-editor]');
            if (richTextareas.length > 0) {
                console.log(`Form #${index}: ${form.id || 'no-id'} has ${richTextareas.length} potential rich text fields`);
                
                // Check for submit handlers
                const hasInlineHandler = form.hasAttribute('onsubmit');
                const hasEventHandler = typeof jQuery !== 'undefined' ? 
                    jQuery._data(form, "events")?.submit?.length > 0 : 
                    form._events?.submit?.length > 0;
                
                console.log(`  - Has inline submit handler: ${hasInlineHandler}`);
                console.log(`  - Has event submit handler: ${hasEventHandler ? 'Yes' : 'Unknown'}`);
            }
        });
        
        // Check for PyCommerceQuill
        if (typeof window.PyCommerceQuill !== 'undefined') {
            console.log("✅ PyCommerceQuill integration is available");
            
            // Try to fix any issues automatically
            const potentialEditors = document.querySelectorAll('[id*="content"], [id*="editor"], textarea[name*="content"]');
            console.log(`Found ${potentialEditors.length} potential editors that could be initialized`);
            
            potentialEditors.forEach((editor, index) => {
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
    
    console.log("===== End Diagnostics =====");
})();
