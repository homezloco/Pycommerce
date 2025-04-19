
/**
 * Quill Editor Integration
 * 
 * This script handles the integration of Quill WYSIWYG editor
 * with the PyCommerce admin interface, ensuring proper loading
 * and initialization of the editor.
 */

(function() {
    // Configuration
    const QUILL_VERSION = '1.3.6';
    const QUILL_CSS_URL = `https://cdn.quilljs.com/${QUILL_VERSION}/quill.snow.css`;
    const QUILL_JS_URL = `https://cdn.quilljs.com/${QUILL_VERSION}/quill.min.js`;
    
    // Track load state
    let isQuillLoaded = false;
    let isQuillCssLoaded = false;
    
    // Store editor instances
    const editorInstances = {};
    
    /**
     * Check if Quill is already loaded on the page
     */
    function checkQuillLoaded() {
        return typeof window.Quill !== 'undefined';
    }
    
    /**
     * Load Quill's CSS stylesheet if not already loaded
     */
    function loadQuillCss() {
        if (isQuillCssLoaded || document.querySelector(`link[href="${QUILL_CSS_URL}"]`)) {
            isQuillCssLoaded = true;
            return;
        }
        
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = QUILL_CSS_URL;
        link.onload = () => {
            console.log("✅ Quill CSS loaded");
            isQuillCssLoaded = true;
        };
        document.head.appendChild(link);
    }
    
    /**
     * Load Quill JavaScript if not already loaded
     * @param {Function} callback - Function to call when Quill is loaded
     */
    function loadQuillJs(callback) {
        if (checkQuillLoaded()) {
            isQuillLoaded = true;
            callback();
            return;
        }
        
        const script = document.createElement('script');
        script.src = QUILL_JS_URL;
        script.async = true;
        script.onload = () => {
            console.log("✅ Quill JS loaded");
            isQuillLoaded = true;
            callback();
        };
        script.onerror = (error) => {
            console.error("❌ Failed to load Quill:", error);
        };
        document.head.appendChild(script);
    }
    
    /**
     * Initialize Quill on the specified element
     * @param {string} selector - CSS selector for the container element
     * @param {Object} options - Quill initialization options
     * @returns {Object|null} - Quill instance or null if initialization failed
     */
    function initializeQuill(selector, options = {}) {
        // Set default options
        const defaultOptions = {
            modules: {
                toolbar: [
                    ['bold', 'italic', 'underline', 'strike'],
                    ['blockquote', 'code-block'],
                    [{ 'header': 1 }, { 'header': 2 }],
                    [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                    [{ 'script': 'sub'}, { 'script': 'super' }],
                    [{ 'indent': '-1'}, { 'indent': '+1' }],
                    [{ 'size': ['small', false, 'large', 'huge'] }],
                    [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
                    [{ 'color': [] }, { 'background': [] }],
                    [{ 'font': [] }],
                    [{ 'align': [] }],
                    ['clean'],
                    ['link', 'image', 'video']
                ]
            },
            theme: 'snow'
        };
        
        // Merge options
        const mergedOptions = { ...defaultOptions, ...options };
        
        try {
            const container = document.querySelector(selector);
            if (!container) {
                console.error(`❌ Element not found: ${selector}`);
                return null;
            }
            
            const quill = new Quill(selector, mergedOptions);
            console.log(`✅ Quill initialized on ${selector}`);
            
            // Store instance for later access
            const instanceId = selector.replace(/[^a-zA-Z0-9]/g, '_');
            editorInstances[instanceId] = quill;
            
            return quill;
        } catch (error) {
            console.error("❌ Failed to initialize Quill:", error);
            return null;
        }
    }
    
    /**
     * Create a container for Quill editor
     * @param {string} targetSelector - Selector for the target element (usually a textarea)
     * @param {string} containerId - ID to give the new container
     * @returns {Element|null} - The created container or null if creation failed
     */
    function createEditorContainer(targetSelector, containerId) {
        try {
            const targetElement = document.querySelector(targetSelector);
            if (!targetElement) {
                console.error(`❌ Target element not found: ${targetSelector}`);
                return null;
            }
            
            // Check if container already exists
            let container = document.getElementById(containerId);
            if (container) {
                console.log(`⚠️ Container already exists: ${containerId}`);
                return container;
            }
            
            // Create new container
            container = document.createElement('div');
            container.id = containerId;
            container.style.height = '400px';
            container.style.marginBottom = '20px';
            
            // Hide the target element (usually a textarea)
            targetElement.style.display = 'none';
            
            // Insert container before the target element
            targetElement.parentNode.insertBefore(container, targetElement);
            
            console.log(`✅ Created editor container: ${containerId}`);
            return container;
        } catch (error) {
            console.error("❌ Failed to create editor container:", error);
            return null;
        }
    }
    
    /**
     * Add AI Assist button to Quill toolbar
     * @param {Object} quill - Quill editor instance
     * @param {string} modalId - ID of the AI Assist modal
     */
    function addAIAssistButton(quill, modalId = 'aiAssistModal') {
        try {
            const toolbar = document.querySelector('.ql-toolbar');
            if (!toolbar) {
                console.warn("⚠️ Quill toolbar not found");
                return;
            }
            
            // Check if button already exists
            if (toolbar.querySelector('.ai-assist-btn')) {
                return;
            }
            
            const aiButton = document.createElement('button');
            aiButton.className = 'btn btn-primary btn-sm ms-2 ai-assist-btn';
            aiButton.innerHTML = '<i class="fas fa-robot"></i> AI Assist';
            aiButton.type = 'button';
            
            aiButton.onclick = function() {
                const modal = document.getElementById(modalId);
                if (modal) {
                    // Initialize Bootstrap modal if Bootstrap is available
                    if (typeof bootstrap !== 'undefined') {
                        const modalInstance = new bootstrap.Modal(modal);
                        modalInstance.show();
                    } else {
                        // Fallback for when Bootstrap is not available
                        modal.style.display = 'block';
                    }
                } else {
                    console.error(`❌ Modal not found: ${modalId}`);
                }
            };
            
            toolbar.appendChild(aiButton);
            console.log("✅ Added AI Assist button to toolbar");
        } catch (error) {
            console.error("❌ Failed to add AI Assist button:", error);
        }
    }
    
    /**
     * Set up the media selector for image insertion
     * @param {Object} quill - Quill editor instance
     */
    function setupMediaSelector(quill) {
        try {
            const imageButton = document.querySelector('.ql-image');
            if (!imageButton) {
                console.warn("⚠️ Image button not found in Quill toolbar");
                return;
            }
            
            // Remove existing event listeners by cloning
            const newImageButton = imageButton.cloneNode(true);
            imageButton.parentNode.replaceChild(newImageButton, imageButton);
            
            newImageButton.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // Use the global openMediaSelector function if available
                if (typeof window.openMediaSelector === 'function') {
                    window.openMediaSelector(function(id, url, name) {
                        const range = quill.getSelection() || { index: 0 };
                        quill.insertEmbed(range.index, 'image', url);
                    });
                } else {
                    console.error("❌ openMediaSelector function not found");
                    
                    // Try to find and show the media selector modal directly
                    const modal = document.getElementById('mediaSelectorModal');
                    if (modal && typeof bootstrap !== 'undefined') {
                        const modalInstance = new bootstrap.Modal(modal);
                        modalInstance.show();
                    } else {
                        console.error("❌ Cannot find media selector modal or Bootstrap is not available");
                    }
                }
            });
            
            console.log("✅ Set up media selector for Quill editor");
        } catch (error) {
            console.error("❌ Failed to set up media selector:", error);
        }
    }
    
    /**
     * Connect a Quill instance to a form for submission
     * @param {Object} quill - Quill editor instance
     * @param {string} formSelector - Selector for the form
     * @param {string} textareaSelector - Selector for the textarea to receive Quill content
     */
    function connectQuillToForm(quill, formSelector, textareaSelector) {
        try {
            const form = document.querySelector(formSelector);
            if (!form) {
                console.error(`❌ Form not found: ${formSelector}`);
                return;
            }
            
            const textarea = document.querySelector(textareaSelector);
            if (!textarea) {
                console.error(`❌ Textarea not found: ${textareaSelector}`);
                return;
            }
            
            // Clone and replace to remove existing handlers
            const newForm = form.cloneNode(true);
            form.parentNode.replaceChild(newForm, form);
            
            newForm.addEventListener('submit', function(e) {
                try {
                    textarea.value = quill.root.innerHTML;
                    console.log("✅ Updated form content with Quill editor content");
                } catch (err) {
                    console.error("❌ Error updating form content:", err);
                    e.preventDefault();
                }
            });
            
            console.log("✅ Connected Quill to form");
        } catch (error) {
            console.error("❌ Failed to connect Quill to form:", error);
        }
    }
    
    /**
     * Initialize a complete Quill editor setup
     * @param {Object} config - Configuration object
     */
    function initializeCompleteEditor(config) {
        const defaults = {
            targetSelector: '#content',
            containerId: 'quill-editor-container',
            formSelector: 'form',
            height: '500px',
            modalId: 'aiAssistModal',
            options: {}
        };
        
        const cfg = { ...defaults, ...config };
        
        // Ensure Quill is loaded
        if (!checkQuillLoaded()) {
            loadQuillCss();
            loadQuillJs(() => initializeCompleteEditorInternal(cfg));
        } else {
            initializeCompleteEditorInternal(cfg);
        }
    }
    
    /**
     * Internal function to initialize editor once Quill is loaded
     * @param {Object} cfg - Configuration object
     */
    function initializeCompleteEditorInternal(cfg) {
        // Create container
        const container = createEditorContainer(cfg.targetSelector, cfg.containerId);
        if (!container) return;
        
        // Set height if specified
        if (cfg.height) {
            container.style.height = cfg.height;
        }
        
        // Initialize Quill
        const quill = initializeQuill(`#${cfg.containerId}`, cfg.options);
        if (!quill) return;
        
        // Add AI button
        addAIAssistButton(quill, cfg.modalId);
        
        // Set up media selector
        setupMediaSelector(quill);
        
        // Connect to form
        connectQuillToForm(quill, cfg.formSelector, cfg.targetSelector);
        
        // Make globally accessible
        window.currentQuillEditor = quill;
        
        // Return the instance
        return quill;
    }
    
    // Expose public API
    window.PyCommerceQuill = {
        init: initializeCompleteEditor,
        loadQuill: function(callback) {
            loadQuillCss();
            loadQuillJs(callback);
        },
        getEditor: function(selector) {
            const instanceId = selector.replace(/[^a-zA-Z0-9]/g, '_');
            return editorInstances[instanceId] || null;
        }
    };
    
    // Auto-initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        // Auto-detect and initialize editors with data-quill-editor attribute
        const autoInitElements = document.querySelectorAll('[data-quill-editor]');
        if (autoInitElements.length > 0) {
            loadQuillCss();
            loadQuillJs(() => {
                autoInitElements.forEach(element => {
                    const targetId = element.id;
                    const containerId = `${targetId}-quill-container`;
                    
                    // Create a container next to the target element
                    const container = document.createElement('div');
                    container.id = containerId;
                    container.style.height = element.getAttribute('data-quill-height') || '300px';
                    element.style.display = 'none';
                    element.parentNode.insertBefore(container, element.nextSibling);
                    
                    // Initialize Quill on the container
                    const quill = initializeQuill(`#${containerId}`);
                    
                    // Set up form connection if in a form
                    const form = element.closest('form');
                    if (form && quill) {
                        form.addEventListener('submit', function() {
                            element.value = quill.root.innerHTML;
                        });
                    }
                });
            });
        }
    });
})();
/**
 * Quill Editor Integration
 * 
 * This script handles the integration of Quill WYSIWYG editor
 * with the PyCommerce admin interface, ensuring proper loading
 * and initialization of the editor.
 */

(function() {
    // Configuration
    const QUILL_VERSION = '1.3.6';
    const QUILL_CSS_URL = `https://cdn.quilljs.com/${QUILL_VERSION}/quill.snow.css`;
    const QUILL_JS_URL = `https://cdn.quilljs.com/${QUILL_VERSION}/quill.min.js`;
    
    // Track load state
    let isQuillLoaded = false;
    let isQuillCssLoaded = false;
    
    // Store editor instances
    const editorInstances = {};
    
    /**
     * Check if Quill is already loaded on the page
     */
    function checkQuillLoaded() {
        return typeof window.Quill !== 'undefined';
    }
    
    /**
     * Load Quill's CSS stylesheet if not already loaded
     */
    function loadQuillCss() {
        if (isQuillCssLoaded || document.querySelector(`link[href="${QUILL_CSS_URL}"]`)) {
            isQuillCssLoaded = true;
            return;
        }
        
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = QUILL_CSS_URL;
        link.onload = () => {
            console.log("✅ Quill CSS loaded");
            isQuillCssLoaded = true;
        };
        document.head.appendChild(link);
    }
    
    /**
     * Load Quill JavaScript if not already loaded
     * @param {Function} callback - Function to call when Quill is loaded
     */
    function loadQuillJs(callback) {
        if (checkQuillLoaded()) {
            isQuillLoaded = true;
            callback();
            return;
        }
        
        const script = document.createElement('script');
        script.src = QUILL_JS_URL;
        script.async = true;
        script.onload = () => {
            console.log("✅ Quill JS loaded");
            isQuillLoaded = true;
            callback();
        };
        script.onerror = (error) => {
            console.error("❌ Failed to load Quill:", error);
        };
        document.head.appendChild(script);
    }
    
    /**
     * Initialize Quill on the specified element
     * @param {string} selector - CSS selector for the container element
     * @param {Object} options - Quill initialization options
     * @returns {Object|null} - Quill instance or null if initialization failed
     */
    function initializeQuill(selector, options = {}) {
        // Set default options
        const defaultOptions = {
            modules: {
                toolbar: [
                    ['bold', 'italic', 'underline', 'strike'],
                    ['blockquote', 'code-block'],
                    [{ 'header': 1 }, { 'header': 2 }],
                    [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                    [{ 'script': 'sub'}, { 'script': 'super' }],
                    [{ 'indent': '-1'}, { 'indent': '+1' }],
                    [{ 'size': ['small', false, 'large', 'huge'] }],
                    [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
                    [{ 'color': [] }, { 'background': [] }],
                    [{ 'font': [] }],
                    [{ 'align': [] }],
                    ['clean'],
                    ['link', 'image', 'video']
                ]
            },
            theme: 'snow'
        };
        
        // Merge options
        const mergedOptions = { ...defaultOptions, ...options };
        
        try {
            const container = document.querySelector(selector);
            if (!container) {
                console.error(`❌ Element not found: ${selector}`);
                return null;
            }
            
            const quill = new Quill(selector, mergedOptions);
            console.log(`✅ Quill initialized on ${selector}`);
            
            // Store instance for later access
            const instanceId = selector.replace(/[^a-zA-Z0-9]/g, '_');
            editorInstances[instanceId] = quill;
            
            return quill;
        } catch (error) {
            console.error("❌ Failed to initialize Quill:", error);
            return null;
        }
    }
    
    /**
     * Create a container for Quill editor
     * @param {string} targetSelector - Selector for the target element (usually a textarea)
     * @param {string} containerId - ID to give the new container
     * @returns {Element|null} - The created container or null if creation failed
     */
    function createEditorContainer(targetSelector, containerId) {
        try {
            const targetElement = document.querySelector(targetSelector);
            if (!targetElement) {
                console.error(`❌ Target element not found: ${targetSelector}`);
                return null;
            }
            
            // Check if container already exists
            let container = document.getElementById(containerId);
            if (container) {
                console.log(`⚠️ Container already exists: ${containerId}`);
                return container;
            }
            
            // Create new container
            container = document.createElement('div');
            container.id = containerId;
            container.style.height = '400px';
            container.style.marginBottom = '20px';
            
            // Hide the target element (usually a textarea)
            targetElement.style.display = 'none';
            
            // Insert container before the target element
            targetElement.parentNode.insertBefore(container, targetElement);
            
            console.log(`✅ Created editor container: ${containerId}`);
            return container;
        } catch (error) {
            console.error("❌ Failed to create editor container:", error);
            return null;
        }
    }
    
    /**
     * Add AI Assist button to Quill toolbar
     * @param {Object} quill - Quill editor instance
     * @param {string} modalId - ID of the AI Assist modal
     */
    function addAIAssistButton(quill, modalId = 'aiAssistModal') {
        try {
            const toolbar = document.querySelector('.ql-toolbar');
            if (!toolbar) {
                console.warn("⚠️ Quill toolbar not found");
                return;
            }
            
            // Check if button already exists
            if (toolbar.querySelector('.ai-assist-btn')) {
                return;
            }
            
            const aiButton = document.createElement('button');
            aiButton.className = 'btn btn-primary btn-sm ms-2 ai-assist-btn';
            aiButton.innerHTML = '<i class="fas fa-robot"></i> AI Assist';
            aiButton.type = 'button';
            
            aiButton.onclick = function() {
                const modal = document.getElementById(modalId);
                if (modal) {
                    // Initialize Bootstrap modal if Bootstrap is available
                    if (typeof bootstrap !== 'undefined') {
                        const modalInstance = new bootstrap.Modal(modal);
                        modalInstance.show();
                    } else {
                        // Fallback for when Bootstrap is not available
                        modal.style.display = 'block';
                    }
                } else {
                    console.error(`❌ Modal not found: ${modalId}`);
                }
            };
            
            toolbar.appendChild(aiButton);
            console.log("✅ Added AI Assist button to toolbar");
        } catch (error) {
            console.error("❌ Failed to add AI Assist button:", error);
        }
    }
    
    /**
     * Set up the media selector for image insertion
     * @param {Object} quill - Quill editor instance
     */
    function setupMediaSelector(quill) {
        try {
            const imageButton = document.querySelector('.ql-image');
            if (!imageButton) {
                console.warn("⚠️ Image button not found in Quill toolbar");
                return;
            }
            
            // Remove existing event listeners by cloning
            const newImageButton = imageButton.cloneNode(true);
            imageButton.parentNode.replaceChild(newImageButton, imageButton);
            
            newImageButton.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // Use the global openMediaSelector function if available
                if (typeof window.openMediaSelector === 'function') {
                    window.openMediaSelector(function(id, url, name) {
                        const range = quill.getSelection() || { index: 0 };
                        quill.insertEmbed(range.index, 'image', url);
                    });
                } else {
                    console.error("❌ openMediaSelector function not found");
                    
                    // Try to find and show the media selector modal directly
                    const modal = document.getElementById('mediaSelectorModal');
                    if (modal && typeof bootstrap !== 'undefined') {
                        const modalInstance = new bootstrap.Modal(modal);
                        modalInstance.show();
                    } else {
                        console.error("❌ Cannot find media selector modal or Bootstrap is not available");
                    }
                }
            });
            
            console.log("✅ Set up media selector for Quill editor");
        } catch (error) {
            console.error("❌ Failed to set up media selector:", error);
        }
    }
    
    /**
     * Connect a Quill instance to a form for submission
     * @param {Object} quill - Quill editor instance
     * @param {string} formSelector - Selector for the form
     * @param {string} textareaSelector - Selector for the textarea to receive Quill content
     */
    function connectQuillToForm(quill, formSelector, textareaSelector) {
        try {
            const form = document.querySelector(formSelector);
            if (!form) {
                console.error(`❌ Form not found: ${formSelector}`);
                return;
            }
            
            const textarea = document.querySelector(textareaSelector);
            if (!textarea) {
                console.error(`❌ Textarea not found: ${textareaSelector}`);
                return;
            }
            
            // Clone and replace to remove existing handlers
            const newForm = form.cloneNode(true);
            form.parentNode.replaceChild(newForm, form);
            
            newForm.addEventListener('submit', function(e) {
                try {
                    textarea.value = quill.root.innerHTML;
                    console.log("✅ Updated form content with Quill editor content");
                } catch (err) {
                    console.error("❌ Error updating form content:", err);
                    e.preventDefault();
                }
            });
            
            console.log("✅ Connected Quill to form");
        } catch (error) {
            console.error("❌ Failed to connect Quill to form:", error);
        }
    }
    
    /**
     * Initialize a complete Quill editor setup
     * @param {Object} config - Configuration object
     */
    function initializeCompleteEditor(config) {
        const defaults = {
            targetSelector: '#content',
            containerId: 'quill-editor-container',
            formSelector: 'form',
            height: '500px',
            modalId: 'aiAssistModal',
            options: {}
        };
        
        const cfg = { ...defaults, ...config };
        
        // Ensure Quill is loaded
        if (!checkQuillLoaded()) {
            loadQuillCss();
            loadQuillJs(() => initializeCompleteEditorInternal(cfg));
        } else {
            initializeCompleteEditorInternal(cfg);
        }
    }
    
    /**
     * Internal function to initialize editor once Quill is loaded
     * @param {Object} cfg - Configuration object
     */
    function initializeCompleteEditorInternal(cfg) {
        // Create container
        const container = createEditorContainer(cfg.targetSelector, cfg.containerId);
        if (!container) return;
        
        // Set height if specified
        if (cfg.height) {
            container.style.height = cfg.height;
        }
        
        // Initialize Quill
        const quill = initializeQuill(`#${cfg.containerId}`, cfg.options);
        if (!quill) return;
        
        // Add AI button
        addAIAssistButton(quill, cfg.modalId);
        
        // Set up media selector
        setupMediaSelector(quill);
        
        // Connect to form
        connectQuillToForm(quill, cfg.formSelector, cfg.targetSelector);
        
        // Make globally accessible
        window.currentQuillEditor = quill;
        
        // Return the instance
        return quill;
    }
    
    // Expose public API
    window.PyCommerceQuill = {
        init: initializeCompleteEditor,
        loadQuill: function(callback) {
            loadQuillCss();
            loadQuillJs(callback);
        },
        getEditor: function(selector) {
            const instanceId = selector.replace(/[^a-zA-Z0-9]/g, '_');
            return editorInstances[instanceId] || null;
        }
    };
    
    // Auto-initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        // Auto-detect and initialize editors with data-quill-editor attribute
        const autoInitElements = document.querySelectorAll('[data-quill-editor]');
        if (autoInitElements.length > 0) {
            loadQuillCss();
            loadQuillJs(() => {
                autoInitElements.forEach(element => {
                    const targetId = element.id;
                    const containerId = `${targetId}-quill-container`;
                    
                    // Create a container next to the target element
                    const container = document.createElement('div');
                    container.id = containerId;
                    container.style.height = element.getAttribute('data-quill-height') || '300px';
                    element.style.display = 'none';
                    element.parentNode.insertBefore(container, element.nextSibling);
                    
                    // Initialize Quill on the container
                    const quill = initializeQuill(`#${containerId}`);
                    
                    // Set up form connection if in a form
                    const form = element.closest('form');
                    if (form && quill) {
                        form.addEventListener('submit', function() {
                            element.value = quill.root.innerHTML;
                        });
                    }
                });
            });
        }
    });
})();
