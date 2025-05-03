
/**
 * Enhanced Page Builder JavaScript
 * Handles the interactive functionality of the visual page builder
 * with modern UI, real-time preview, and enhanced drag-and-drop capabilities
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log("Enhanced Page Builder initializing...");
    
    // Load required libraries
    loadDependencies([
        {
            name: 'Sortable',
            test: () => typeof Sortable !== 'undefined',
            src: 'https://cdn.jsdelivr.net/npm/sortablejs@1.14.0/Sortable.min.js'
        }
    ]).then(() => {
        console.log("All dependencies loaded successfully");
        initPageBuilder();
    }).catch(error => {
        console.error("Error loading dependencies:", error);
        showNotification("Error loading required libraries. Please refresh the page.", "danger", 10000);
    });
    
    // Add theme toggle button to the page
    addThemeToggle();
});

/**
 * Load required dependencies for the page builder
 */
function loadDependencies(dependencies) {
    return new Promise((resolve, reject) => {
        const loadingPromises = dependencies.map(dep => {
            return new Promise((resolveLib, rejectLib) => {
                // Check if the library is already loaded
                if (dep.test()) {
                    console.log(`${dep.name} is already loaded`);
                    resolveLib();
                    return;
                }
                
                console.log(`Loading ${dep.name} dynamically...`);
                const script = document.createElement('script');
                script.src = dep.src;
                
                script.onload = () => {
                    console.log(`${dep.name} loaded successfully`);
                    resolveLib();
                };
                
                script.onerror = () => {
                    rejectLib(`Failed to load ${dep.name}`);
                };
                
                document.head.appendChild(script);
            });
        });
        
        Promise.all(loadingPromises)
            .then(resolve)
            .catch(reject);
    });
}

/**
 * Add dark mode toggle functionality
 */
function addThemeToggle() {
    // Create the toggle button
    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'theme-toggle';
    toggleBtn.innerHTML = '<i class="fas fa-moon"></i>';
    toggleBtn.setAttribute('title', 'Toggle dark mode');
    
    // Add click event
    toggleBtn.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        const isDarkMode = document.body.classList.contains('dark-mode');
        
        // Update icon
        toggleBtn.innerHTML = isDarkMode ? 
            '<i class="fas fa-sun"></i>' : 
            '<i class="fas fa-moon"></i>';
        
        // Save preference to localStorage
        localStorage.setItem('pageBuilderDarkMode', isDarkMode);
        
        // Show notification
        showNotification(`${isDarkMode ? 'Dark' : 'Light'} mode activated`, 'info', 2000);
    });
    
    // Check for saved preference
    const savedPreference = localStorage.getItem('pageBuilderDarkMode');
    if (savedPreference === 'true') {
        document.body.classList.add('dark-mode');
        toggleBtn.innerHTML = '<i class="fas fa-sun"></i>';
    }
    
    // Add to document
    document.body.appendChild(toggleBtn);
}

/**
 * Initialize all page builder components
 */
function initPageBuilder() {
    console.log("Initializing page builder components...");
    
    // Initialize section management
    initSectionManager();
    
    // Initialize content block management
    initBlockManager();
    
    // Setup save functionality
    setupSaveHandler();
    
    // Setup real-time preview
    setupPreviewPanel();
    
    // Add hints and tooltips
    enhanceUIWithHints();
    
    // Register change events for real-time updates
    registerChangeEvents();
    
    // Add improved drag-and-drop effects
    enhanceDragDropExperience();
    
    console.log("Page builder initialization complete!");
    showNotification("Page Builder loaded successfully", "success", 3000);
}

/**
 * Enhanced UI with helpful hints and tooltips
 */
function enhanceUIWithHints() {
    // Add tooltips to buttons and controls
    document.querySelectorAll('[data-tooltip]').forEach(el => {
        el.classList.add('enhanced-tooltip');
    });
    
    // Add hints to empty sections
    document.querySelectorAll('.blocks-container').forEach(container => {
        if (!container.querySelector('.block-container') && !container.querySelector('.empty-section-hint')) {
            const hint = document.createElement('div');
            hint.className = 'empty-section-hint text-center p-4 text-muted';
            hint.innerHTML = '<i class="fas fa-arrow-down mb-2"></i><p>Add content blocks to this section by selecting a block type below and clicking "Add Block"</p>';
            container.appendChild(hint);
        }
    });
    
    // Add first-time user guide if no sections exist yet
    const pageContainer = document.getElementById('pageContainer');
    if (pageContainer && !pageContainer.querySelector('.section-container') && !document.getElementById('first-time-guide')) {
        const guide = document.createElement('div');
        guide.id = 'first-time-guide';
        guide.className = 'alert alert-info m-4 fade-in';
        guide.innerHTML = `
            <h5><i class="fas fa-info-circle me-2"></i> Getting Started</h5>
            <p>Welcome to the PyCommerce Page Builder! Here's how to create your page:</p>
            <ol>
                <li>Select a section type from the dropdown menu on the left</li>
                <li>Click "Add Section" to add it to your page</li>
                <li>Add content blocks to your sections</li>
                <li>Arrange and customize your content</li>
                <li>Save your changes when you're done</li>
            </ol>
            <button class="btn btn-sm btn-primary" onclick="this.parentNode.remove()">Got it!</button>
        `;
        pageContainer.appendChild(guide);
    }
}

function initSectionManager() {
    // Get DOM elements
    const addSectionBtn = document.getElementById('addSectionBtn');
    const sectionTypeSelect = document.getElementById('sectionTypeSelect');
    const sectionsContainer = document.getElementById('sectionsContainer');
    
    if (!addSectionBtn || !sectionTypeSelect || !sectionsContainer) {
        console.warn("Section manager elements not found");
        return;
    }
    
    // Add a new section
    addSectionBtn.addEventListener('click', function() {
        const sectionType = sectionTypeSelect.value;
        if (!sectionType) {
            showNotification('Please select a section type', 'warning');
            return;
        }
        
        // Create a new section via API
        createSection(sectionType);
    });
    
    // Make sections sortable
    initSortable();
}

function createSection(sectionType) {
    // Get page ID from the page
    const pageId = document.getElementById('pageId').value;
    
    // Create section data
    const sectionData = {
        page_id: pageId,
        section_type: sectionType,
        position: getNextPosition(),
        settings: getDefaultSettings(sectionType)
    };
    
    // Call API to create section
    fetch('/admin/api/pages/sections', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(sectionData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.id) {
            // Refresh the page to show the new section
            // In a production app, we would append the new section dynamically
            location.reload();
        } else {
            showNotification('Error creating section', 'danger');
        }
    })
    .catch(error => {
        console.error('Error creating section:', error);
        showNotification('Error: ' + error.message, 'danger');
    });
}

function getNextPosition() {
    // Get the count of existing sections
    const sections = document.querySelectorAll('.page-section');
    return sections.length;
}

function getDefaultSettings(sectionType) {
    // Default settings based on section type
    const defaults = {
        'hero': {
            background: 'light',
            text_color: 'dark',
            padding: 'large',
            alignment: 'center'
        },
        'text': {
            background: 'white',
            padding: 'medium',
            width: 'container'
        },
        'content': {
            background: 'white',
            padding: 'medium',
            width: 'container'
        },
        'media': {
            background: 'light',
            padding: 'medium',
            layout: 'side-by-side'
        },
        'products': {
            background: 'white',
            padding: 'medium',
            columns: 3,
            show_price: true
        },
        'cta': {
            background: 'primary',
            text_color: 'white',
            padding: 'large',
            alignment: 'center'
        }
    };
    
    return defaults[sectionType] || { padding: 'medium', background: 'white' };
}

function initBlockManager() {
    // Setup event delegation for add block buttons
    document.addEventListener('click', function(e) {
        if (e.target && e.target.classList.contains('add-block-btn')) {
            const sectionId = e.target.getAttribute('data-section-id');
            const blockType = document.querySelector(`#blockTypeSelect-${sectionId}`).value;
            
            if (!blockType) {
                showNotification('Please select a block type', 'warning');
                return;
            }
            
            // Create a new block
            createBlock(sectionId, blockType);
        }
    });
}

function createBlock(sectionId, blockType) {
    // Create block data
    const blockData = {
        section_id: sectionId,
        block_type: blockType,
        position: getNextBlockPosition(sectionId),
        content: getDefaultContent(blockType),
        settings: getDefaultBlockSettings(blockType)
    };
    
    // Call API to create block
    fetch('/admin/api/pages/blocks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(blockData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.id) {
            // Refresh the page to show the new block
            location.reload();
        } else {
            showNotification('Error creating block', 'danger');
        }
    })
    .catch(error => {
        console.error('Error creating block:', error);
        showNotification('Error: ' + error.message, 'danger');
    });
}

function getNextBlockPosition(sectionId) {
    // Get the count of existing blocks in the section
    const blocks = document.querySelectorAll(`.block-container[data-section-id="${sectionId}"] .content-block`);
    return blocks.length;
}

function getDefaultContent(blockType) {
    // Default content based on block type
    const defaults = {
        'text': {
            html: '<p>Enter your content here...</p>'
        },
        'image': {
            url: '',
            alt: 'Image description'
        },
        'button': {
            text: 'Click Me',
            url: '#',
            style: 'primary'
        },
        'video': {
            url: '',
            embed_code: ''
        },
        'product': {
            product_id: '',
            show_price: true,
            show_button: true
        }
    };
    
    return defaults[blockType] || {};
}

function getDefaultBlockSettings(blockType) {
    // Default settings based on block type
    const defaults = {
        'text': {
            width: 'full',
            alignment: 'left'
        },
        'image': {
            width: 'full',
            alignment: 'center'
        },
        'button': {
            alignment: 'center',
            size: 'medium'
        },
        'video': {
            width: 'full',
            autoplay: false
        },
        'product': {
            width: 'full',
            layout: 'card'
        }
    };
    
    return defaults[blockType] || { width: 'full' };
}

function initSortable() {
    // If Sortable library is available
    if (typeof Sortable !== 'undefined') {
        // Make sections sortable
        const sectionsList = document.getElementById('sectionsContainer');
        if (sectionsList) {
            Sortable.create(sectionsList, {
                handle: '.section-drag-handle',
                animation: 150,
                onEnd: function(evt) {
                    updateSectionPositions();
                }
            });
        }
        
        // Make blocks sortable within each section
        document.querySelectorAll('.block-container').forEach(container => {
            Sortable.create(container, {
                handle: '.block-drag-handle',
                animation: 150,
                onEnd: function(evt) {
                    updateBlockPositions(container.getAttribute('data-section-id'));
                }
            });
        });
    }
}

function updateSectionPositions() {
    // Get all sections
    const sections = document.querySelectorAll('.page-section');
    
    // Update positions
    const positions = Array.from(sections).map((section, index) => {
        return {
            id: section.getAttribute('data-section-id'),
            position: index
        };
    });
    
    // Call API to update positions
    fetch('/admin/api/pages/sections/positions', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ positions: positions })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Sections reordered', 'success');
        }
    })
    .catch(error => {
        console.error('Error updating section positions:', error);
    });
}

function updateBlockPositions(sectionId) {
    // Get all blocks in the section
    const blocks = document.querySelectorAll(`.block-container[data-section-id="${sectionId}"] .content-block`);
    
    // Update positions
    const positions = Array.from(blocks).map((block, index) => {
        return {
            id: block.getAttribute('data-block-id'),
            position: index
        };
    });
    
    // Call API to update positions
    fetch('/admin/api/pages/blocks/positions', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ positions: positions })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Blocks reordered', 'success');
        }
    })
    .catch(error => {
        console.error('Error updating block positions:', error);
    });
}

function setupSaveHandler() {
    const savePageBtn = document.getElementById('savePageBtn');
    
    if (!savePageBtn) {
        console.warn("Save button not found");
        return;
    }
    
    savePageBtn.addEventListener('click', function() {
        savePage();
    });
}

function savePage() {
    // Get page ID
    const pageId = document.getElementById('pageId').value;
    const pageTitle = document.getElementById('pageTitle').value;
    const pageSlug = document.getElementById('pageSlug').value;
    const isPublished = document.getElementById('isPublished').checked;
    
    // Validate inputs
    if (!pageTitle || !pageSlug) {
        showNotification('Title and slug are required', 'warning');
        return;
    }
    
    // Gather page data
    const pageData = {
        title: pageTitle,
        slug: pageSlug,
        is_published: isPublished,
        meta_title: document.getElementById('metaTitle')?.value || '',
        meta_description: document.getElementById('metaDescription')?.value || ''
    };
    
    // Call API to update page
    fetch(`/admin/api/pages/${pageId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(pageData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.id) {
            showNotification('Page saved successfully', 'success');
        } else {
            showNotification('Error saving page', 'danger');
        }
    })
    .catch(error => {
        console.error('Error saving page:', error);
        showNotification('Error: ' + error.message, 'danger');
    });
}

/**
 * Setup the real-time preview panel
 */
function setupPreviewPanel() {
    // Create preview toggle button
    const previewToggleBtn = document.createElement('button');
    previewToggleBtn.className = 'preview-toggle-btn';
    previewToggleBtn.innerHTML = '<i class="fas fa-eye"></i> Live Preview';
    previewToggleBtn.addEventListener('click', togglePreviewPanel);
    document.body.appendChild(previewToggleBtn);
    
    // Create the preview panel
    const previewPanel = document.createElement('div');
    previewPanel.className = 'preview-panel';
    previewPanel.innerHTML = `
        <div class="preview-header">
            <div class="preview-title">
                <i class="fas fa-eye"></i> Live Preview
            </div>
            <div class="preview-actions">
                <button class="btn btn-sm btn-outline-secondary close-preview-btn">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
        <div class="preview-device-selector">
            <button class="preview-device-btn active" data-device="desktop" title="Desktop view">
                <i class="fas fa-desktop"></i>
            </button>
            <button class="preview-device-btn" data-device="tablet" title="Tablet view">
                <i class="fas fa-tablet-alt"></i>
            </button>
            <button class="preview-device-btn" data-device="mobile" title="Mobile view">
                <i class="fas fa-mobile-alt"></i>
            </button>
        </div>
        <div class="preview-content">
            <iframe id="previewFrame" class="preview-iframe"></iframe>
        </div>
    `;
    
    document.body.appendChild(previewPanel);
    
    // Setup event handlers
    document.querySelector('.close-preview-btn').addEventListener('click', togglePreviewPanel);
    document.querySelectorAll('.preview-device-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from all buttons
            document.querySelectorAll('.preview-device-btn').forEach(b => b.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');
            // Change iframe width based on device
            const iframe = document.getElementById('previewFrame');
            const device = this.getAttribute('data-device');
            
            switch(device) {
                case 'desktop':
                    iframe.style.width = '100%';
                    break;
                case 'tablet':
                    iframe.style.width = '768px';
                    break;
                case 'mobile':
                    iframe.style.width = '375px';
                    break;
            }
        });
    });
    
    // Initial load of preview
    updatePreview();
}

/**
 * Toggle the preview panel visibility
 */
function togglePreviewPanel() {
    const panel = document.querySelector('.preview-panel');
    panel.classList.toggle('active');
    
    if (panel.classList.contains('active')) {
        updatePreview();
    }
}

/**
 * Update the preview content
 */
function updatePreview() {
    const previewFrame = document.getElementById('previewFrame');
    if (!previewFrame) return;
    
    // Show loading indicator
    previewFrame.srcdoc = `
        <html>
        <head>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background-color: #f8f9fa;
                }
                .loading {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    color: #5c6ac4;
                }
                .spinner {
                    border: 4px solid rgba(0, 0, 0, 0.1);
                    border-radius: 50%;
                    border-top: 4px solid #5c6ac4;
                    width: 40px;
                    height: 40px;
                    margin-bottom: 20px;
                    animation: spin 1s linear infinite;
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
        </head>
        <body>
            <div class="loading">
                <div class="spinner"></div>
                <p>Loading preview...</p>
            </div>
        </body>
        </html>
    `;
    
    // Get page ID
    const pageId = document.getElementById('pageId').value;
    
    // Fetch preview URL
    const previewUrl = `/admin/pages/preview/${pageId}`;
    
    // Add timestamp to bust cache
    const timestamp = new Date().getTime();
    const cacheUrl = `${previewUrl}?t=${timestamp}`;
    
    // Load preview in iframe
    setTimeout(() => {
        previewFrame.src = cacheUrl;
    }, 500);
}

/**
 * Register change events for real-time updates
 */
function registerChangeEvents() {
    // Listen for content changes
    document.addEventListener('contentChanged', function() {
        console.log('Content changed, updating preview...');
        updatePreview();
    });
    
    // Listen for section position changes
    document.addEventListener('sectionsReordered', function() {
        console.log('Sections reordered, updating preview...');
        updatePreview();
    });
    
    // Listen for block position changes
    document.addEventListener('blocksReordered', function() {
        console.log('Blocks reordered, updating preview...');
        updatePreview();
    });
}

/**
 * Enhance drag and drop experience
 */
function enhanceDragDropExperience() {
    // Add effects to sortable sections
    if (typeof Sortable !== 'undefined') {
        const sections = document.querySelectorAll('.section-container');
        sections.forEach(section => {
            // Add drag handle if not exists
            if (!section.querySelector('.section-drag-handle')) {
                const sectionHeader = section.querySelector('.section-header');
                if (sectionHeader) {
                    const dragHandle = document.createElement('div');
                    dragHandle.className = 'section-drag-handle';
                    dragHandle.innerHTML = '<i class="fas fa-grip-vertical"></i>';
                    dragHandle.style.cursor = 'grab';
                    dragHandle.style.marginRight = '10px';
                    sectionHeader.prepend(dragHandle);
                }
            }
            
            // Add click event to select section
            section.addEventListener('click', function(e) {
                // Don't select if clicking on controls or drag handle
                if (e.target.closest('.section-controls') || 
                    e.target.closest('.section-drag-handle') ||
                    e.target.closest('.block-container')) {
                    return;
                }
                
                // Remove active class from all sections
                document.querySelectorAll('.section-container').forEach(s => {
                    s.classList.remove('active');
                });
                
                // Add active class to this section
                this.classList.add('active');
            });
        });
        
        // Enhanced block dragging
        const blockContainers = document.querySelectorAll('.block-container');
        blockContainers.forEach(container => {
            const blocks = container.querySelectorAll('.content-block');
            blocks.forEach(block => {
                // Add drag handle if not exists
                if (!block.querySelector('.block-drag-handle')) {
                    const blockHeader = block.querySelector('.block-header');
                    if (blockHeader) {
                        const dragHandle = document.createElement('div');
                        dragHandle.className = 'block-drag-handle';
                        dragHandle.innerHTML = '<i class="fas fa-grip-horizontal"></i>';
                        dragHandle.style.cursor = 'grab';
                        dragHandle.style.marginRight = '10px';
                        blockHeader.prepend(dragHandle);
                    }
                }
            });
        });
    }
}

/**
 * Show a notification message
 */
function showNotification(message, type = 'info', duration = 5000) {
    // Check if the notification container exists
    let container = document.getElementById('notificationContainer');
    
    // Create container if it doesn't exist
    if (!container) {
        container = document.createElement('div');
        container.id = 'notificationContainer';
        container.style.position = 'fixed';
        container.style.top = '20px';
        container.style.right = '20px';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    
    // Create notification element with icons based on type
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show slide-in-right`;
    notification.role = 'alert';
    
    // Add icon based on notification type
    let icon = 'info-circle';
    switch(type) {
        case 'success': icon = 'check-circle'; break;
        case 'danger': icon = 'exclamation-circle'; break;
        case 'warning': icon = 'exclamation-triangle'; break;
    }
    
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-${icon} me-2"></i>
            <div>${message}</div>
        </div>
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to container
    container.appendChild(notification);
    
    // Remove after specified duration
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, duration);
}
