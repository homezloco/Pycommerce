
/**
 * PyCommerce Quill Editor Debug Utility
 * 
 * This utility provides diagnostic and troubleshooting tools for the Quill editor
 * integration in PyCommerce. It helps identify and fix common issues with the editor.
 */

const PyCommerceQuillDebug = (function() {
    // Store diagnostic results
    let diagnosticResults = {};
    
    /**
     * Run a comprehensive diagnostic on the Quill editor setup
     * @returns {Object} Diagnostic results
     */
    function runDiagnostic() {
        console.log("===== PyCommerce Quill Editor Diagnostic =====");
        
        diagnosticResults = {
            quillLoaded: checkQuillAvailability(),
            bootstrapAvailable: checkBootstrapAvailability(),
            editorContainers: findEditorContainers(),
            mediaModalAvailable: checkMediaSelectorAvailability(),
            aiAssistAvailable: checkAIAssistAvailability(),
            formConnections: checkFormConnections()
        };
        
        // Log summary
        console.log("Diagnostic Summary:");
        console.log(`- Quill Available: ${diagnosticResults.quillLoaded ? '✅ Yes' : '❌ No'}`);
        console.log(`- Bootstrap Available: ${diagnosticResults.bootstrapAvailable ? '✅ Yes' : '❌ No'}`);
        console.log(`- Editor Containers Found: ${diagnosticResults.editorContainers.length}`);
        console.log(`- Media Selector Available: ${diagnosticResults.mediaModalAvailable ? '✅ Yes' : '❌ No'}`);
        console.log(`- AI Assist Available: ${diagnosticResults.aiAssistAvailable ? '✅ Yes' : '❌ No'}`);
        console.log(`- Form Connections: ${diagnosticResults.formConnections.length} found`);
        
        console.log("===== End of Diagnostic =====");
        
        return diagnosticResults;
    }
    
    /**
     * Check if Quill is available in the global scope
     */
    function checkQuillAvailability() {
        const quillAvailable = typeof Quill !== 'undefined';
        console.log(`Quill Availability: ${quillAvailable ? '✅ Available (v' + Quill.version + ')' : '❌ Not loaded'}`);
        
        if (!quillAvailable) {
            console.log("Checking for Quill script tags...");
            const quillScripts = document.querySelectorAll('script[src*="quill"]');
            if (quillScripts.length > 0) {
                console.log(`Found ${quillScripts.length} Quill script tags:`);
                quillScripts.forEach((script, i) => {
                    console.log(`  Script #${i+1}: ${script.src}`);
                });
            } else {
                console.log("No Quill script tags found in the document.");
            }
        }
        
        return quillAvailable;
    }
    
    /**
     * Check if Bootstrap is available for modals
     */
    function checkBootstrapAvailability() {
        const bootstrapAvailable = typeof bootstrap !== 'undefined';
        console.log(`Bootstrap Availability: ${bootstrapAvailable ? '✅ Available' : '❌ Not loaded'}`);
        return bootstrapAvailable;
    }
    
    /**
     * Find all potential Quill editor containers
     */
    function findEditorContainers() {
        // Look for actual Quill containers
        const containers = document.querySelectorAll('.ql-container');
        console.log(`Found ${containers.length} Quill containers in the document.`);
        
        const activeContainers = [];
        
        // Check each container for a Quill instance
        containers.forEach((container, i) => {
            try {
                const quillInstance = typeof Quill !== 'undefined' ? Quill.find(container) : null;
                if (quillInstance) {
                    console.log(`  Container #${i+1}: Active Quill instance`);
                    activeContainers.push({
                        element: container,
                        instance: quillInstance,
                        id: container.id || null,
                        content: quillInstance.getText().length
                    });
                } else {
                    console.log(`  Container #${i+1}: No Quill instance attached`);
                    activeContainers.push({
                        element: container,
                        instance: null,
                        id: container.id || null
                    });
                }
            } catch (e) {
                console.error(`  Error checking container #${i+1}:`, e);
                activeContainers.push({
                    element: container,
                    error: e.message
                });
            }
        });
        
        // Look for potential content areas that could become editors
        const textareas = document.querySelectorAll('textarea[name*="content"], textarea[id*="content"]');
        console.log(`Found ${textareas.length} textareas that might be content editors.`);
        
        textareas.forEach((textarea, i) => {
            console.log(`  Textarea #${i+1}: id="${textarea.id}", name="${textarea.name}"`);
            console.log(`    Visibility: ${textarea.style.display === 'none' ? 'Hidden' : 'Visible'}`);
            
            // Check if this textarea has a nearby Quill container
            const parent = textarea.parentNode;
            const nearbyContainers = parent.querySelectorAll('.ql-container');
            if (nearbyContainers.length > 0) {
                console.log(`    Has nearby editor container: Yes (${nearbyContainers.length} found)`);
            } else {
                console.log(`    Has nearby editor container: No`);
            }
        });
        
        return activeContainers;
    }
    
    /**
     * Check if the media selector modal is available
     */
    function checkMediaSelectorAvailability() {
        const mediaSelectorModal = document.getElementById('mediaSelectorModal');
        
        if (mediaSelectorModal) {
            console.log(`Media Selector: ✅ Found (#${mediaSelectorModal.id})`);
            
            // Check if the global function exists
            if (typeof window.openMediaSelector === 'function') {
                console.log("  openMediaSelector function: ✅ Available");
            } else {
                console.log("  openMediaSelector function: ❌ Not defined");
            }
            
            return true;
        } else {
            console.log("Media Selector: ❌ Not found in the document");
            return false;
        }
    }
    
    /**
     * Check if the AI assistance modal is available
     */
    function checkAIAssistAvailability() {
        const aiAssistModal = document.getElementById('aiAssistModal');
        
        if (aiAssistModal) {
            console.log(`AI Assist Modal: ✅ Found (#${aiAssistModal.id})`);
            return true;
        } else {
            console.log("AI Assist Modal: ❌ Not found in the document");
            return false;
        }
    }
    
    /**
     * Check form connections for editor content submission
     */
    function checkFormConnections() {
        const forms = document.querySelectorAll('form');
        console.log(`Found ${forms.length} forms in the document.`);
        
        const potentialEditorForms = [];
        
        forms.forEach((form, i) => {
            // Look for content textareas within the form
            const contentTextareas = form.querySelectorAll('textarea[name*="content"], textarea[id*="content"]');
            
            if (contentTextareas.length > 0) {
                console.log(`  Form #${i+1} (id="${form.id || 'none'}"): Contains ${contentTextareas.length} content textareas`);
                
                const formInfo = {
                    element: form,
                    id: form.id || null,
                    action: form.action,
                    method: form.method,
                    contentElements: []
                };
                
                contentTextareas.forEach((textarea, j) => {
                    formInfo.contentElements.push({
                        element: textarea,
                        id: textarea.id || null,
                        name: textarea.name
                    });
                    
                    console.log(`    Textarea #${j+1}: id="${textarea.id}", name="${textarea.name}"`);
                });
                
                potentialEditorForms.push(formInfo);
            }
        });
        
        return potentialEditorForms;
    }
    
    /**
     * Fix common issues with Quill editor
     */
    function fixCommonIssues() {
        // Run diagnostic first if not already run
        if (Object.keys(diagnosticResults).length === 0) {
            runDiagnostic();
        }
        
        const fixes = [];
        
        // Fix 1: Load Quill if missing
        if (!diagnosticResults.quillLoaded) {
            console.log("Attempting to load Quill...");
            
            const quillCSS = document.createElement('link');
            quillCSS.rel = 'stylesheet';
            quillCSS.href = 'https://cdn.quilljs.com/1.3.6/quill.snow.css';
            document.head.appendChild(quillCSS);
            
            const quillScript = document.createElement('script');
            quillScript.src = 'https://cdn.quilljs.com/1.3.6/quill.min.js';
            quillScript.onload = () => {
                console.log("✅ Quill loaded successfully");
                
                // After loading Quill, check if PyCommerceQuill needs to be loaded
                if (typeof window.PyCommerceQuill === 'undefined') {
                    loadPyCommerceQuill();
                } else {
                    initializeEditors();
                }
            };
            document.head.appendChild(quillScript);
            
            fixes.push("Loaded Quill from CDN");
        }
        
        // Fix 2: Load PyCommerceQuill if missing
        if (typeof window.PyCommerceQuill === 'undefined') {
            loadPyCommerceQuill();
            fixes.push("Loaded PyCommerceQuill");
        }
        
        // Fix 3: Initialize editors on content textareas
        if (diagnosticResults.quillLoaded) {
            initializeEditors();
            fixes.push("Initialized editors on content textareas");
        }
        
        console.log("Fix Summary:");
        if (fixes.length > 0) {
            fixes.forEach((fix, i) => {
                console.log(`  ${i+1}. ${fix}`);
            });
        } else {
            console.log("  No fixes applied - everything seems to be working correctly");
        }
        
        return fixes;
    }
    
    /**
     * Load the PyCommerceQuill integration script
     */
    function loadPyCommerceQuill() {
        console.log("Loading PyCommerceQuill integration...");
        
        const script = document.createElement('script');
        script.src = '/static/js/quill-integration.js';
        script.onload = () => {
            console.log("✅ PyCommerceQuill loaded successfully");
            if (typeof window.PyCommerceQuill !== 'undefined') {
                initializeEditors();
            }
        };
        document.head.appendChild(script);
    }
    
    /**
     * Initialize editors on content textareas
     */
    function initializeEditors() {
        if (typeof window.PyCommerceQuill === 'undefined' || !window.PyCommerceQuill.init) {
            console.error("❌ PyCommerceQuill not available or missing init function");
            return false;
        }
        
        const contentTextareas = document.querySelectorAll('textarea[name*="content"], textarea[id*="content"]');
        console.log(`Found ${contentTextareas.length} content textareas to initialize`);
        
        contentTextareas.forEach((textarea, i) => {
            // Skip if already hidden (might already have an editor)
            if (textarea.style.display === 'none') {
                console.log(`  Textarea #${i+1} (${textarea.id || 'unnamed'}): Already has an editor`);
                return;
            }
            
            console.log(`  Initializing editor for textarea #${i+1} (${textarea.id || 'unnamed'})`);
            
            // Get the form containing this textarea
            const form = textarea.closest('form');
            
            // Initialize the editor
            try {
                window.PyCommerceQuill.init({
                    targetSelector: `#${textarea.id}`,
                    containerId: `${textarea.id}-quill-container`,
                    formSelector: form ? `#${form.id}` : 'form',
                    height: '400px'
                });
                console.log(`  ✅ Initialized editor for ${textarea.id || 'unnamed textarea'}`);
            } catch (e) {
                console.error(`  ❌ Failed to initialize editor:`, e);
            }
        });
        
        return true;
    }
    
    // Public API
    return {
        diagnose: runDiagnostic,
        fix: fixCommonIssues,
        initializeEditor: function(config) {
            if (typeof window.PyCommerceQuill !== 'undefined' && window.PyCommerceQuill.init) {
                return window.PyCommerceQuill.init(config);
            }
            return null;
        }
    };
})();

// Add global access
window.PyCommerceQuillDebug = PyCommerceQuillDebug;

// Auto-run diagnostic when script is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Wait a short time to ensure other scripts have loaded
    setTimeout(function() {
        console.log("Running automatic Quill editor diagnostic...");
        PyCommerceQuillDebug.diagnose();
    }, 500);
});
