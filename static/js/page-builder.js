
/**
 * Enhanced Page Builder JavaScript
 * Handles the interactive functionality of the visual page builder
 * with modern UI, real-time preview, and enhanced drag-and-drop capabilities
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log("Enhanced Page Builder initializing...");
    
    // Detect mobile devices
    const isMobileDevice = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    // Set a global flag for mobile detection
    window.isMobileDevice = isMobileDevice;
    
    // Add mobile class to body if on a mobile device
    if (isMobileDevice) {
        document.body.classList.add('mobile-device');
        console.log("Mobile device detected, adding mobile optimizations");
    }
    
    // Add meta viewport tag if not present
    if (!document.querySelector('meta[name="viewport"]')) {
        const metaViewport = document.createElement('meta');
        metaViewport.name = 'viewport';
        metaViewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
        document.head.appendChild(metaViewport);
    }
    
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
    
    // Listen for orientation changes
    window.addEventListener('orientationchange', handleOrientationChange);
    
    // Also listen for resize which handles orientation changes on some devices
    window.addEventListener('resize', debounce(handleResizeEvent, 250));
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
    
    // Initialize AI block generator
    initAIBlockGenerator();
    
    // Initialize collaborative editing indicators
    initCollaborativeEditing();
    
    // Initialize block templates system
    initBlockTemplates();
    
    // Register change events for real-time updates
    registerChangeEvents();
    
    // Add improved drag-and-drop effects
    enhanceDragDropExperience();
    
    // Setup mobile-specific preview controls
    setupMobilePreviewControls();
    
    // Initialize split view functionality
    initSplitView();
    
    // Add window resize and orientation change listeners
    window.addEventListener('resize', debounce(handleResizeEvent, 250));
    window.addEventListener('orientationchange', handleOrientationChange);
    
    // Initial check for device size and orientation
    handleResizeEvent();
    
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
    const pageIdElement = document.getElementById('pageId');
    if (!pageIdElement) {
        console.error("Page ID element not found");
        showNotification('Error: Page ID not found', 'danger');
        return;
    }
    
    const pageId = pageIdElement.value;
    
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
/**
 * Setup the real-time preview panel
 */
function setupPreviewPanel() {
    console.log("Setting up preview panel");
    // Get the toggle preview button and attach event listener
    const togglePreviewBtn = document.getElementById('togglePreviewBtn');
    const livePreviewPanel = document.getElementById('livePreviewPanel');
    const closePreviewBtn = document.getElementById('closePreviewBtn');
    const splitViewToggle = document.getElementById('splitViewToggle');
    
    if (togglePreviewBtn && livePreviewPanel) {
        togglePreviewBtn.addEventListener('click', function() {
            // If in split view mode, use that instead
            const editorLayout = document.querySelector('.editor-layout');
            if (editorLayout && editorLayout.classList.contains('split-view')) {
                console.log("Already in split view mode, not toggling standard preview");
                return;
            }
            
            togglePreviewPanel();
        });
        
        // Close button handler
        if (closePreviewBtn) {
            closePreviewBtn.addEventListener('click', function() {
                // If in split view mode, exit it
                const editorLayout = document.querySelector('.editor-layout');
                if (editorLayout && editorLayout.classList.contains('split-view') && splitViewToggle) {
                    splitViewToggle.click();
                    return;
                }
                
                togglePreviewPanel(false);
            });
        }
        
        // Setup device switcher functionality
        setupDeviceSwitcher();
        
        // Load preview when panel is first shown
        updatePreview();
    } else {
        console.warn('Preview panel elements not found');
    }
}

/**
 * Toggle the preview panel visibility
 * @param {boolean|undefined} show - Force show or hide. If undefined, toggles current state.
 */
function togglePreviewPanel(show) {
    const panel = document.getElementById('livePreviewPanel');
    const editorCanvas = document.querySelector('.editor-canvas');
    const toggleBtn = document.getElementById('togglePreviewBtn');
    
    if (!panel || !editorCanvas) return;
    
    if (typeof show === 'undefined') {
        // Toggle current state
        const isVisible = panel.style.display !== 'none';
        show = !isVisible;
    }
    
    // Check if device is mobile
    const isMobile = window.innerWidth < 992;
    const isSmallMobile = window.innerWidth < 576;
    
    // Store the current state for analytics
    window.previewPanelVisible = show;
    
    // Add enhanced mobile behavior
    if (isMobile) {
        document.body.classList.toggle('preview-active', show);
        // On mobile, we might want different behavior - could slide in from bottom instead
        if (isSmallMobile && show) {
            // For very small screens, maybe show a fullscreen overlay preview
            panel.classList.add('mobile-fullscreen-preview');
            document.body.classList.add('no-scroll'); // Prevent body scrolling
        }
    }
    
    if (show) {
        // Show preview panel with smooth animation
        panel.style.display = 'flex';
        panel.classList.add('fade-in');
        
        // For touch devices, ensure the preview is scrollable with momentum scrolling
        if ('ontouchstart' in window) {
            const previewContent = panel.querySelector('.preview-content');
            if (previewContent) {
                previewContent.style.webkitOverflowScrolling = 'touch';
            }
        }
        
        // Adjust editor canvas layout for split view
        editorCanvas.classList.add('with-preview');
        
        // Update the preview content
        updateLivePreview();
        
        // Create flex layout container if it doesn't exist
        const editorWrapper = document.querySelector('.editor-layout');
        if (!editorWrapper) {
            // If .editor-layout doesn't exist, we need to wrap the canvas and preview panel
            const newWrapper = document.createElement('div');
            newWrapper.className = 'editor-layout';
            
            // On mobile, add specific class for vertical layout
            if (isMobile) {
                newWrapper.classList.add('mobile-vertical-layout');
            }
            newWrapper.style.display = 'flex';
            
            // On mobile, we'll want column direction
            if (isMobile) {
                newWrapper.style.flexDirection = 'column';
            }
            
            // Get the parent of the editor canvas
            const canvasParent = editorCanvas.parentNode;
            
            // Insert the wrapper before the canvas in the DOM
            canvasParent.insertBefore(newWrapper, editorCanvas);
            
            // Move the canvas and preview panel into the wrapper
            newWrapper.appendChild(editorCanvas);
            newWrapper.appendChild(panel);
        } else {
            // Update direction based on screen size
            editorWrapper.style.flexDirection = isMobile ? 'column' : 'row';
        }
        
        // Update toggle button appearance and text
        if (toggleBtn) {
            toggleBtn.classList.add('active');
            
            // Different text for mobile vs desktop
            if (isMobile) {
                toggleBtn.innerHTML = '<i class="fas fa-eye-slash me-1"></i>';
                // On really small screens just show icon
                if (window.innerWidth < 576) {
                    toggleBtn.setAttribute('data-tooltip', 'Hide preview');
                } else {
                    toggleBtn.innerHTML = '<i class="fas fa-eye-slash me-1"></i> Hide';
                    toggleBtn.setAttribute('data-tooltip', 'Hide preview');
                }
            } else {
                toggleBtn.innerHTML = '<i class="fas fa-eye-slash me-1"></i> Hide Preview';
                toggleBtn.setAttribute('data-tooltip', 'Hide live preview');
            }
        }
        
        // Update the preview content
        updatePreview();
        
        // Scroll to preview panel on mobile
        if (isMobile) {
            setTimeout(() => {
                // Smooth scroll to preview panel
                panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 300);
        }
        
        // Show notification to user
        showNotification('Live preview enabled. Changes will update in real-time.', 'info', 3000);
    } else {
        // Hide preview panel with smooth animation
        panel.classList.remove('fade-in');
        
        // Use setTimeout to allow animation to complete before hiding
        setTimeout(() => {
            panel.style.display = 'none';
        }, 200);
        
        // Restore editor canvas to full width
        editorCanvas.classList.remove('with-preview');
        
        // Update toggle button appearance and text
        if (toggleBtn) {
            toggleBtn.classList.remove('active');
            
            // Different text for mobile vs desktop
            if (isMobile) {
                if (window.innerWidth < 576) {
                    toggleBtn.innerHTML = '<i class="fas fa-eye me-1"></i>';
                    toggleBtn.setAttribute('data-tooltip', 'Show preview');
                } else {
                    toggleBtn.innerHTML = '<i class="fas fa-eye me-1"></i> View';
                    toggleBtn.setAttribute('data-tooltip', 'Show preview');
                }
            } else {
                toggleBtn.innerHTML = '<i class="fas fa-eye me-1"></i> Live Preview';
                toggleBtn.setAttribute('data-tooltip', 'Show live preview');
            }
        }
        
        // Scroll back to editor on mobile
        if (isMobile) {
            setTimeout(() => {
                // Smooth scroll to editor
                editorCanvas.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);
        }
    }
    
    // Add event listener for window resize to adjust layout
    if (!window.previewResizeHandlerAdded) {
        window.addEventListener('resize', function() {
            const wrapper = document.querySelector('.editor-layout');
            if (wrapper) {
                const isMobileNow = window.innerWidth < 992;
                wrapper.style.flexDirection = isMobileNow ? 'column' : 'row';
            }
        });
        window.previewResizeHandlerAdded = true;
    }
}

/**
 * Setup device switcher in preview panel
 */
function setupDeviceSwitcher() {
    const deviceButtons = document.querySelectorAll('.preview-device-options button[data-device]');
    const previewViewport = document.querySelector('.preview-viewport');
    const previewPanel = document.getElementById('livePreviewPanel');
    
    if (!deviceButtons.length || !previewViewport) return;
    
    // Device dimensions for reference (width x height)
    const deviceSizes = {
        desktop: { width: '100%', height: '100%', name: 'Desktop' },
        tablet: { width: '768px', height: '1024px', name: 'Tablet' },
        mobile: { width: '375px', height: '667px', name: 'Mobile' }
    };
    
    // Check if we're on a mobile device
    const isMobile = window.innerWidth < 992;
    const isSmallMobile = window.innerWidth < 576;
    
    // Create a more compact device switcher for mobile if needed
    if (isMobile && !document.querySelector('.mobile-device-switcher')) {
        const deviceOptions = document.querySelector('.preview-device-options');
        
        if (deviceOptions) {
            // Make the device switcher more compact for mobile
            deviceOptions.classList.add('mobile-friendly');
            
            // Change button styles for better mobile display
            deviceButtons.forEach(btn => {
                // For very small screens, just use icons
                if (isSmallMobile) {
                    const deviceType = btn.dataset.device;
                    let icon = '';
                    
                    switch(deviceType) {
                        case 'desktop':
                            icon = '<i class="fas fa-desktop"></i>';
                            break;
                        case 'tablet':
                            icon = '<i class="fas fa-tablet-alt"></i>';
                            break;
                        case 'mobile':
                            icon = '<i class="fas fa-mobile-alt"></i>';
                            break;
                    }
                    
                    btn.innerHTML = icon;
                    btn.classList.add('btn-sm');
                }
            });
            
            // Add touch-friendly styling
            const style = document.createElement('style');
            style.textContent = `
                .preview-device-options.mobile-friendly {
                    display: flex;
                    justify-content: center;
                    padding: 8px 0;
                    background: rgba(255,255,255,0.9);
                    border-radius: 50px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    position: sticky;
                    bottom: 10px;
                    z-index: 100;
                    margin-top: 10px;
                }
                
                .preview-device-options.mobile-friendly button {
                    min-width: ${isSmallMobile ? '40px' : '80px'};
                    margin: 0 5px;
                }
                
                /* Make active state more visible on mobile */
                .preview-device-options.mobile-friendly button.active {
                    transform: scale(1.05);
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                }
                
                @media (prefers-color-scheme: dark) {
                    .preview-device-options.mobile-friendly {
                        background: rgba(40,40,40,0.9);
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    deviceButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            // Get the device type
            const deviceType = this.dataset.device;
            
            // Skip if already active
            if (this.classList.contains('active')) return;
            
            // Remove active class from all buttons
            deviceButtons.forEach(b => b.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Update viewport class based on device
            previewViewport.className = 'preview-viewport ' + deviceType;
            
            // Show notification about device change
            const deviceInfo = deviceSizes[deviceType];
            if (deviceInfo) {
                showNotification(`Switched to ${deviceInfo.name} preview`, 'info', 2000);
            }
            
            // Add smooth transition
            previewViewport.style.transition = 'all 0.3s ease';
            
            // Create a quick animation effect to show the change
            previewViewport.classList.add('device-changing');
            setTimeout(() => {
                previewViewport.classList.remove('device-changing');
            }, 300);
            
            // Set a data attribute for CSS to use
            if (previewPanel) {
                previewPanel.setAttribute('data-device-mode', deviceType);
            }
            
            // On mobile, adjust content positioning
            if (isMobile && deviceType !== 'desktop') {
                // Center the preview content on mobile views
                const previewContent = document.querySelector('.preview-content');
                if (previewContent) {
                    previewContent.style.margin = '0 auto';
                }
                
                // Make sure the viewport height is sufficient
                previewViewport.style.minHeight = 
                    deviceType === 'tablet' ? '1050px' : '700px';
            }
            
            // Update preview after device change with a delay to allow animations to complete
            setTimeout(() => {
                // Force preview refresh to adjust to new dimensions
                updatePreview();
            }, 400);
        });
        
        // Add tooltips to device buttons
        const deviceType = btn.dataset.device;
        if (deviceSizes[deviceType]) {
            const info = deviceSizes[deviceType];
            btn.setAttribute('title', `${info.name} view (${info.width !== '100%' ? info.width : 'Full width'})`);
            
            // Add aria-label for accessibility
            btn.setAttribute('aria-label', `${info.name} view`);
        }
    });
    
    // Add a small badge to show current device mode
    const viewport = document.querySelector('.preview-viewport');
    if (viewport) {
        // Create the badge only if it doesn't exist
        if (!document.querySelector('.device-badge')) {
            const deviceBadge = document.createElement('div');
            deviceBadge.className = 'device-badge';
            deviceBadge.style.position = 'absolute';
            deviceBadge.style.top = '5px';
            deviceBadge.style.right = '10px';
            deviceBadge.style.fontSize = '12px';
            deviceBadge.style.color = '#666';
            deviceBadge.style.background = 'rgba(255,255,255,0.7)';
            deviceBadge.style.padding = '2px 8px';
            deviceBadge.style.borderRadius = '4px';
            deviceBadge.style.zIndex = '10';
            deviceBadge.textContent = 'Desktop';
            
            viewport.appendChild(deviceBadge);
        }
        
        const deviceBadge = document.querySelector('.device-badge');
        
        // Update badge when device changes
        deviceButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const deviceType = this.dataset.device;
                if (deviceSizes[deviceType] && deviceBadge) {
                    deviceBadge.textContent = deviceSizes[deviceType].name;
                    
                    // Add appropriate icon for the device badge
                    let icon = '';
                    switch(deviceType) {
                        case 'desktop':
                            icon = '🖥️ ';
                            break;
                        case 'tablet':
                            icon = '📱 ';
                            break;
                        case 'mobile':
                            icon = '📱 ';
                            break;
                    }
                    
                    // Only add icons on larger screens to save space on mobile
                    if (!isSmallMobile) {
                        deviceBadge.textContent = icon + deviceSizes[deviceType].name;
                    }
                }
            });
        });
    }
    
    // Set the default device based on screen size
    if (isMobile) {
        // On mobile devices, start with mobile preview
        const mobileButton = document.querySelector('button[data-device="mobile"]');
        if (mobileButton && !mobileButton.classList.contains('active')) {
            mobileButton.click();
        }
    }
    
    // Listen for orientation changes on mobile
    window.addEventListener('orientationchange', function() {
        // Allow time for the orientation change to complete
        setTimeout(() => {
            // Readjust preview based on new orientation
            const activeDevice = document.querySelector('.preview-device-options button.active');
            if (activeDevice) {
                activeDevice.click();
            }
        }, 300);
    });
}

/**
 * Update the preview content
 */
/**
 * Update the live preview with smooth transitions
 * Enhanced with loading animation and error handling
 */
function updatePreview() {
    const previewFrame = document.getElementById('previewFrame');
    if (!previewFrame) return;
    
    // Show loading indicator with PyCommerce branding and improved animation
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
                    color: #212b36;
                    transition: opacity 0.3s ease;
                }
                .loading {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    text-align: center;
                    animation: fadeIn 0.5s ease;
                }
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .logo {
                    margin-bottom: 20px;
                    color: #5c6ac4;
                    font-size: 24px;
                    font-weight: bold;
                    position: relative;
                }
                .logo::after {
                    content: '';
                    position: absolute;
                    bottom: -5px;
                    left: 0;
                    width: 100%;
                    height: 2px;
                    background: linear-gradient(90deg, #5c6ac4, #8e9fef);
                    transform: scaleX(0);
                    transform-origin: left;
                    animation: lineGrow 1.5s ease-out forwards;
                }
                @keyframes lineGrow {
                    to { transform: scaleX(1); }
                }
                .spinner {
                    border: 4px solid rgba(92, 106, 196, 0.1);
                    border-radius: 50%;
                    border-top: 4px solid #5c6ac4;
                    width: 40px;
                    height: 40px;
                    margin-bottom: 20px;
                    animation: spin 1s linear infinite;
                }
                .message {
                    font-size: 16px;
                    margin-bottom: 10px;
                }
                .sub-message {
                    font-size: 14px;
                    color: #637381;
                    max-width: 400px;
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                /* Dark mode support */
                @media (prefers-color-scheme: dark) {
                    body {
                        background-color: #1e2233;
                        color: #e6e9f0;
                    }
                    .sub-message {
                        color: #919eab;
                    }
                }
            </style>
        </head>
        <body>
            <div class="loading">
                <div class="logo">PyCommerce</div>
                <div class="spinner"></div>
                <p class="message">Generating Real-Time Preview</p>
                <p class="sub-message">Changes you make in the editor will appear here immediately</p>
            </div>
        </body>
        </html>
    `;
    
    // Get page ID
    const pageId = document.getElementById('pageId').value;
    if (!pageId) {
        console.error('Page ID not found');
        showPreviewError('Page ID not found', 'Make sure you are editing a saved page.');
        return;
    }
    
    // Fetch preview URL
    const previewUrl = `/admin/pages/preview/${pageId}`;
    
    // Add timestamp to bust cache
    const timestamp = new Date().getTime();
    const cacheUrl = `${previewUrl}?t=${timestamp}`;
    
    // Load preview in iframe with error handling
    setTimeout(() => {
        // Set up error handler for the iframe
        previewFrame.onerror = function() {
            showPreviewError('Failed to load preview', 'There was an error generating the preview. Please try again.');
        };
        
        // Handle iframe load event
        previewFrame.onload = function() {
            // Check if the iframe loaded successfully
            try {
                // Access iframe content to see if it loaded properly
                const iframeContent = previewFrame.contentWindow.document.body.innerHTML;
                
                // If the content contains an error message (this is application specific)
                if (iframeContent.includes('Error:') || iframeContent.includes('Server Error')) {
                    showPreviewError('Preview Error', 'The page encountered an error during rendering.');
                }
            } catch (e) {
                // If we can't access the iframe content, it might be due to CORS or other issues
                console.warn('Cannot access iframe content:', e);
            }
        };
        
        // Set the source to load the preview
        previewFrame.src = cacheUrl;
    }, 300);
}

/**
 * Show an error message in the preview frame
 */
function showPreviewError(title, message) {
    const previewFrame = document.getElementById('previewFrame');
    if (!previewFrame) return;
    
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
                    background-color: #fff;
                    color: #212b36;
                }
                .error-container {
                    text-align: center;
                    max-width: 500px;
                    padding: 40px 20px;
                }
                .error-icon {
                    font-size: 48px;
                    color: #de3618;
                    margin-bottom: 20px;
                }
                .error-title {
                    font-size: 24px;
                    font-weight: 600;
                    margin-bottom: 10px;
                    color: #212b36;
                }
                .error-message {
                    font-size: 16px;
                    line-height: 1.5;
                    color: #637381;
                    margin-bottom: 30px;
                }
                .retry-button {
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #5c6ac4;
                    color: white;
                    border-radius: 4px;
                    font-weight: 500;
                    cursor: pointer;
                    text-decoration: none;
                }
                .retry-button:hover {
                    background-color: #4959bd;
                }
                /* Dark mode support */
                @media (prefers-color-scheme: dark) {
                    body {
                        background-color: #1e2233;
                        color: #e6e9f0;
                    }
                    .error-title {
                        color: #e6e9f0;
                    }
                    .error-message {
                        color: #919eab;
                    }
                }
            </style>
        </head>
        <body>
            <div class="error-container">
                <div class="error-icon">⚠️</div>
                <h1 class="error-title">${title}</h1>
                <p class="error-message">${message}</p>
                <a class="retry-button" onclick="window.parent.updatePreview()">Retry</a>
            </div>
        </body>
        </html>
    `;
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
    
    // Listen for text editor changes
    document.addEventListener('textEditorChanged', function(e) {
        console.log('Text editor content changed, updating preview...');
        updatePreview();
    });
    
    // Listen for section settings changes
    document.addEventListener('sectionSettingsChanged', function(e) {
        console.log('Section settings changed, updating preview...');
        updatePreview();
    });
    
    // Listen for block settings changes
    document.addEventListener('blockSettingsChanged', function(e) {
        console.log('Block settings changed, updating preview...');
        updatePreview();
    });
    
    // Add debounced input listeners to form fields
    const pageSettingsForm = document.getElementById('pageSettingsForm');
    if (pageSettingsForm) {
        const formInputs = pageSettingsForm.querySelectorAll('input, textarea, select');
        
        let debounceTimer;
        formInputs.forEach(input => {
            input.addEventListener('input', function() {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(function() {
                    console.log('Page settings changed, updating preview...');
                    // Only update preview if it's visible
                    const previewPanel = document.getElementById('livePreviewPanel');
                    if (previewPanel && previewPanel.style.display !== 'none') {
                        updatePreview();
                    }
                }, 1000); // 1 second debounce
            });
        });
    }
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
/**
 * Debounce function to limit the rate at which a function can fire
 * @param {Function} func The function to debounce
 * @param {number} wait Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

/**
 * Handle device orientation changes
 */
function handleOrientationChange() {
    console.log("Orientation changed");
    
    // Get current orientation
    const isLandscape = window.matchMedia("(orientation: landscape)").matches;
    const isPortrait = window.matchMedia("(orientation: portrait)").matches;
    
    // Update the body class to reflect orientation
    document.body.classList.toggle('landscape', isLandscape);
    document.body.classList.toggle('portrait', isPortrait);
    
    // Update layout for preview panel
    adjustLayoutForOrientation(isLandscape);
    
    // Show a notification about orientation change
    if (isLandscape) {
        showNotification("Switched to landscape view", "info", 2000);
    } else {
        showNotification("Switched to portrait view", "info", 2000);
    }
}

/**
 * Handle resize events (including orientation changes on some devices)
 */
function handleResizeEvent() {
    const width = window.innerWidth;
    const height = window.innerHeight;
    const isLandscape = width > height;
    
    // Update layout for the new dimensions
    adjustLayoutForOrientation(isLandscape);
    
    // Update device class on body
    document.body.classList.toggle('small-device', width < 576);
    document.body.classList.toggle('medium-device', width >= 576 && width < 992);
    document.body.classList.toggle('large-device', width >= 992);
}

/**
 * Adjust UI layout based on orientation
 * @param {boolean} isLandscape Whether device is in landscape orientation
 */
function adjustLayoutForOrientation(isLandscape) {
    const isMobile = window.innerWidth < 992;
    
    if (!isMobile) return; // Only adjust for mobile devices
    
    const editorLayout = document.querySelector('.editor-layout');
    const previewPanel = document.getElementById('livePreviewPanel');
    
    if (editorLayout) {
        editorLayout.style.flexDirection = isLandscape ? 'row' : 'column';
    }
    
    if (previewPanel && previewPanel.style.display !== 'none') {
        // For landscape on mobile, we might want side-by-side
        if (isLandscape) {
            previewPanel.classList.add('landscape-view');
            previewPanel.classList.remove('portrait-view');
        } else {
            previewPanel.classList.add('portrait-view');
            previewPanel.classList.remove('landscape-view');
        }
    }
}

/**
 * Toggle fullscreen preview mode for mobile devices
 */
function toggleFullscreenPreview() {
    const panel = document.getElementById('livePreviewPanel');
    const fullscreenBtn = document.querySelector('.toggle-fullscreen-btn');
    
    if (!panel || !fullscreenBtn) return;
    
    const isFullscreen = panel.classList.contains('fullscreen');
    
    if (isFullscreen) {
        // Exit fullscreen
        panel.classList.remove('fullscreen');
        document.documentElement.classList.remove('preview-fullscreen');
        fullscreenBtn.innerHTML = '<i class="fas fa-expand-alt"></i>';
        fullscreenBtn.setAttribute('aria-label', 'Enter fullscreen preview');
        
        // Restore normal view
        setTimeout(() => {
            if (window.storedScrollPosition) {
                window.scrollTo({
                    top: window.storedScrollPosition,
                    behavior: 'instant'
                });
                window.storedScrollPosition = null;
            }
        }, 50);
    } else {
        // Enter fullscreen
        // Store current scroll position
        window.storedScrollPosition = window.scrollY;
        
        panel.classList.add('fullscreen');
        document.documentElement.classList.add('preview-fullscreen');
        fullscreenBtn.innerHTML = '<i class="fas fa-compress-alt"></i>';
        fullscreenBtn.setAttribute('aria-label', 'Exit fullscreen preview');
        
        // Scroll to top when in fullscreen
        window.scrollTo({
            top: 0,
            behavior: 'instant'
        });
    }
    
    // Update device preview on transition end
    panel.addEventListener('transitionend', function updateAfterTransition() {
        updatePreview();
        panel.removeEventListener('transitionend', updateAfterTransition);
    });
}

/**
 * Set up mobile-specific preview controls
 */
function setupMobilePreviewControls() {
    const fullscreenBtn = document.querySelector('.toggle-fullscreen-btn');
    if (!fullscreenBtn) return;
    
    // Clear any existing event listeners
    fullscreenBtn.replaceWith(fullscreenBtn.cloneNode(true));
    
    // Get fresh reference after replace
    const newFullscreenBtn = document.querySelector('.toggle-fullscreen-btn');
    
    // Add event listener
    newFullscreenBtn.addEventListener('click', toggleFullscreenPreview);
    
    console.log("Mobile preview controls initialized");
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

/**
 * Initialize AI block generator functionality
 */
function initAIBlockGenerator() {
    // Add AI generate button to each section
    document.querySelectorAll('.section-controls').forEach(controls => {
        const sectionId = controls.closest('.page-section').getAttribute('data-section-id');
        
        // Only add if it doesn't already exist
        if (!controls.querySelector('.ai-generate-btn')) {
            const aiButton = document.createElement('button');
            aiButton.className = 'btn btn-sm btn-outline-primary me-2 ai-generate-btn';
            aiButton.setAttribute('type', 'button');
            aiButton.setAttribute('data-section-id', sectionId);
            aiButton.innerHTML = '<i class="fas fa-magic me-1"></i> AI Generate';
            aiButton.title = 'Generate content with AI';
            
            // Insert before other buttons
            const firstButton = controls.querySelector('button');
            if (firstButton) {
                controls.insertBefore(aiButton, firstButton);
            } else {
                controls.appendChild(aiButton);
            }
            
            // Add click event listener
            aiButton.addEventListener('click', function() {
                showAIGeneratorDialog(sectionId);
            });
        }
    });
}

/**
 * Show AI content generator dialog
 */
function showAIGeneratorDialog(sectionId) {
    // Make sure any existing dialog is removed
    const existingDialog = document.getElementById('aiGeneratorDialog');
    if (existingDialog) {
        existingDialog.remove();
    }
    
    // Create dialog
    const dialog = document.createElement('div');
    dialog.id = 'aiGeneratorDialog';
    dialog.className = 'modal fade';
    dialog.setAttribute('tabindex', '-1');
    dialog.setAttribute('aria-labelledby', 'aiGeneratorDialogLabel');
    dialog.setAttribute('aria-hidden', 'true');
    
    dialog.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="aiGeneratorDialogLabel">
                        <i class="fas fa-magic me-2"></i> AI Content Generator
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <label for="aiPrompt" class="form-label">Describe what content you'd like to generate:</label>
                        <textarea class="form-control" id="aiPrompt" rows="3" 
                            placeholder="Example: 'Write a product description for a premium coffee maker'" autofocus></textarea>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Content type:</label>
                        <div class="btn-group w-100" role="group">
                            <input type="radio" class="btn-check" name="contentType" id="contentTypeText" value="text" checked>
                            <label class="btn btn-outline-secondary" for="contentTypeText">Text</label>
                            
                            <input type="radio" class="btn-check" name="contentType" id="contentTypeHeading" value="heading">
                            <label class="btn btn-outline-secondary" for="contentTypeHeading">Heading</label>
                            
                            <input type="radio" class="btn-check" name="contentType" id="contentTypeImage" value="image">
                            <label class="btn btn-outline-secondary" for="contentTypeImage">Image</label>
                            
                            <input type="radio" class="btn-check" name="contentType" id="contentTypeButton" value="button">
                            <label class="btn btn-outline-secondary" for="contentTypeButton">Button</label>
                        </div>
                    </div>
                    
                    <div id="aiGeneratorOptions" class="mb-3">
                        <!-- Options will be dynamically filled based on content type -->
                    </div>
                    
                    <div id="aiGeneratorResult" class="d-none">
                        <div class="alert alert-success">
                            <h6 class="mb-3"><i class="fas fa-check-circle me-2"></i> Generated Content:</h6>
                            <div id="generatedPreview" class="border p-3 rounded bg-light"></div>
                        </div>
                    </div>
                    
                    <div id="aiGeneratorLoading" class="text-center d-none">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <p class="mt-2">Generating content with AI...</p>
                    </div>
                    
                    <div id="aiGeneratorError" class="alert alert-danger d-none">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        <span id="aiGeneratorErrorMessage">An error occurred</span>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" id="generateBtn" class="btn btn-primary">
                        <i class="fas fa-magic me-1"></i> Generate
                    </button>
                    <button type="button" id="insertContentBtn" class="btn btn-success d-none">
                        <i class="fas fa-plus me-1"></i> Insert Content
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Add to document
    document.body.appendChild(dialog);
    
    // Initialize the Bootstrap modal
    const modalElement = document.getElementById('aiGeneratorDialog');
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
    
    // Handle content type change
    const contentTypeRadios = document.getElementsByName('contentType');
    contentTypeRadios.forEach(radio => {
        radio.addEventListener('change', updateAIGeneratorOptions);
    });
    
    // Initial options setup
    updateAIGeneratorOptions();
    
    // Generate button click handler
    const generateBtn = document.getElementById('generateBtn');
    generateBtn.addEventListener('click', function() {
        generateAIContent(sectionId);
    });
    
    // Insert content button click handler
    const insertContentBtn = document.getElementById('insertContentBtn');
    insertContentBtn.addEventListener('click', function() {
        insertAIGeneratedContent(sectionId);
        modal.hide();
    });
}

/**
 * Update AI generator options based on selected content type
 */
function updateAIGeneratorOptions() {
    const contentType = document.querySelector('input[name="contentType"]:checked').value;
    const optionsContainer = document.getElementById('aiGeneratorOptions');
    
    // Clear current options
    optionsContainer.innerHTML = '';
    
    // Add relevant options based on content type
    switch (contentType) {
        case 'text':
            optionsContainer.innerHTML = `
                <div class="mb-3">
                    <label class="form-label">Text style:</label>
                    <select class="form-select" id="textStyle">
                        <option value="paragraph">Paragraph</option>
                        <option value="features">Feature list</option>
                        <option value="steps">Step-by-step guide</option>
                        <option value="quote">Testimonial quote</option>
                    </select>
                </div>
                <div class="mb-3">
                    <label class="form-label">Tone:</label>
                    <select class="form-select" id="textTone">
                        <option value="professional">Professional</option>
                        <option value="friendly">Friendly</option>
                        <option value="enthusiastic">Enthusiastic</option>
                        <option value="informative">Informative</option>
                    </select>
                </div>
            `;
            break;
            
        case 'heading':
            optionsContainer.innerHTML = `
                <div class="mb-3">
                    <label class="form-label">Heading type:</label>
                    <select class="form-select" id="headingType">
                        <option value="h1">Heading 1 (Main title)</option>
                        <option value="h2">Heading 2 (Section title)</option>
                        <option value="h3">Heading 3 (Subsection title)</option>
                    </select>
                </div>
            `;
            break;
            
        case 'image':
            optionsContainer.innerHTML = `
                <div class="mb-3">
                    <label class="form-label">Image style:</label>
                    <select class="form-select" id="imageStyle">
                        <option value="realistic">Realistic</option>
                        <option value="illustration">Illustration</option>
                        <option value="abstract">Abstract</option>
                    </select>
                </div>
                <div class="form-text text-muted mb-3">
                    <i class="fas fa-info-circle me-1"></i>
                    Images will be generated using AI and stored in your media library.
                </div>
            `;
            break;
            
        case 'button':
            optionsContainer.innerHTML = `
                <div class="mb-3">
                    <label class="form-label">Button purpose:</label>
                    <select class="form-select" id="buttonPurpose">
                        <option value="cta">Call to Action</option>
                        <option value="learn">Learn More</option>
                        <option value="shop">Shop Now</option>
                        <option value="signup">Sign Up</option>
                    </select>
                </div>
            `;
            break;
    }
}

/**
 * Generate content using AI
 */
function generateAIContent(sectionId) {
    const prompt = document.getElementById('aiPrompt').value.trim();
    if (!prompt) {
        showNotification('Please enter a description of the content you want to generate', 'warning');
        return;
    }
    
    // Show loading state
    document.getElementById('aiGeneratorLoading').classList.remove('d-none');
    document.getElementById('aiGeneratorResult').classList.add('d-none');
    document.getElementById('aiGeneratorError').classList.add('d-none');
    document.getElementById('generateBtn').disabled = true;
    
    // Get content type and options
    const contentType = document.querySelector('input[name="contentType"]:checked').value;
    
    // Prepare request data
    const requestData = {
        prompt: prompt,
        content_type: contentType,
        section_id: sectionId,
        options: {}
    };
    
    // Add options based on content type
    switch (contentType) {
        case 'text':
            requestData.options.style = document.getElementById('textStyle').value;
            requestData.options.tone = document.getElementById('textTone').value;
            break;
        case 'heading':
            requestData.options.type = document.getElementById('headingType').value;
            break;
        case 'image':
            requestData.options.style = document.getElementById('imageStyle').value;
            break;
        case 'button':
            requestData.options.purpose = document.getElementById('buttonPurpose').value;
            break;
    }
    
    // Call API to generate content
    fetch('/admin/api/pages/ai/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Hide loading state
        document.getElementById('aiGeneratorLoading').classList.add('d-none');
        document.getElementById('generateBtn').disabled = false;
        
        if (data.error) {
            // Show error
            document.getElementById('aiGeneratorError').classList.remove('d-none');
            document.getElementById('aiGeneratorErrorMessage').textContent = data.error;
        } else {
            // Show result
            document.getElementById('aiGeneratorResult').classList.remove('d-none');
            document.getElementById('insertContentBtn').classList.remove('d-none');
            
            // Store generated content for later use
            window.aiGeneratedContent = data.content;
            
            // Display preview of generated content
            const previewContainer = document.getElementById('generatedPreview');
            
            switch (contentType) {
                case 'text':
                    previewContainer.innerHTML = data.content.html;
                    break;
                case 'heading':
                    previewContainer.innerHTML = `<${data.content.tag} class="preview-heading">${data.content.text}</${data.content.tag}>`;
                    break;
                case 'image':
                    previewContainer.innerHTML = `
                        <img src="${data.content.url}" alt="${data.content.alt}" 
                            class="img-fluid rounded preview-image" style="max-height: 200px;">
                        <p class="mt-2 text-muted small">${data.content.alt}</p>
                    `;
                    break;
                case 'button':
                    previewContainer.innerHTML = `
                        <button type="button" class="btn btn-${data.content.style} preview-button">
                            ${data.content.text}
                        </button>
                        <p class="mt-2 text-muted small">Links to: ${data.content.url}</p>
                    `;
                    break;
            }
        }
    })
    .catch(error => {
        // Handle error
        document.getElementById('aiGeneratorLoading').classList.add('d-none');
        document.getElementById('aiGeneratorError').classList.remove('d-none');
        document.getElementById('aiGeneratorErrorMessage').textContent = error.message;
        document.getElementById('generateBtn').disabled = false;
        console.error('Error generating AI content:', error);
    });
}

/**
 * Insert AI generated content into section
 */
function insertAIGeneratedContent(sectionId) {
    if (!window.aiGeneratedContent) {
        showNotification('No content has been generated yet', 'warning');
        return;
    }
    
    const contentType = document.querySelector('input[name="contentType"]:checked').value;
    
    // Create a block based on the generated content
    let blockType;
    let blockContent;
    let blockSettings;
    
    switch (contentType) {
        case 'text':
            blockType = 'text';
            blockContent = {
                html: window.aiGeneratedContent.html
            };
            blockSettings = {
                width: 'full',
                alignment: 'left'
            };
            break;
        case 'heading':
            blockType = 'text';
            blockContent = {
                html: `<${window.aiGeneratedContent.tag}>${window.aiGeneratedContent.text}</${window.aiGeneratedContent.tag}>`
            };
            blockSettings = {
                width: 'full',
                alignment: 'center'
            };
            break;
        case 'image':
            blockType = 'image';
            blockContent = {
                url: window.aiGeneratedContent.url,
                alt: window.aiGeneratedContent.alt
            };
            blockSettings = {
                width: 'full',
                alignment: 'center'
            };
            break;
        case 'button':
            blockType = 'button';
            blockContent = {
                text: window.aiGeneratedContent.text,
                url: window.aiGeneratedContent.url,
                style: window.aiGeneratedContent.style
            };
            blockSettings = {
                alignment: 'center',
                size: 'medium'
            };
            break;
    }
    
    // Create block data
    const blockData = {
        section_id: sectionId,
        block_type: blockType,
        position: getNextBlockPosition(sectionId),
        content: blockContent,
        settings: blockSettings,
        source: 'ai-generated'
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
            showNotification('AI-generated content added successfully', 'success');
            // Refresh the page to show the new block
            location.reload();
        } else {
            showNotification('Error adding AI-generated content', 'danger');
        }
    })
    .catch(error => {
        console.error('Error adding AI-generated content:', error);
        showNotification('Error: ' + error.message, 'danger');
    });
}

/**
 * Initialize collaborative editing indicators
 */
function initCollaborativeEditing() {
    // Create collaborative editing status indicator
    const statusContainer = document.createElement('div');
    statusContainer.id = 'collaborativeStatusContainer';
    statusContainer.className = 'collaborative-status-container position-fixed bottom-0 start-0 m-3 d-flex align-items-center p-2 rounded shadow-sm bg-white';
    statusContainer.innerHTML = `
        <div class="status-indicator online me-2" title="Connected"></div>
        <div class="status-text">
            <small class="d-block">Collaborative editing</small>
            <span class="editor-status">Just you editing</span>
        </div>
    `;
    document.body.appendChild(statusContainer);
    
    // Add some CSS for the indicators
    const style = document.createElement('style');
    style.textContent = `
        .collaborative-status-container {
            z-index: 1040;
            font-size: 0.85rem;
        }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }
        .status-indicator.online {
            background-color: #28a745;
            box-shadow: 0 0 0 2px rgba(40, 167, 69, 0.2);
        }
        .status-indicator.offline {
            background-color: #dc3545;
            box-shadow: 0 0 0 2px rgba(220, 53, 69, 0.2);
        }
        .status-indicator.busy {
            background-color: #fd7e14;
            box-shadow: 0 0 0 2px rgba(253, 126, 20, 0.2);
        }
    `;
    document.head.appendChild(style);
    
    // Poll for other active editors every 30 seconds
    pollForActiveEditors();
    setInterval(pollForActiveEditors, 30000);
    
    // Send heartbeat every 15 seconds to show we're actively editing
    sendEditorHeartbeat();
    setInterval(sendEditorHeartbeat, 15000);
    
    // Track changes for collaborative editing
    trackPageChanges();
}

/**
 * Poll server for other active editors on this page
 */
function pollForActiveEditors() {
    const pageIdElement = document.getElementById('pageId');
    if (!pageIdElement) {
        console.warn("Page ID element not found for collaborative editing");
        return;
    }
    const pageId = pageIdElement.value;
    if (!pageId) return;
    
    fetch(`/admin/api/pages/${pageId}/active-editors`)
        .then(response => response.json())
        .then(data => {
            updateEditorStatus(data);
        })
        .catch(error => {
            console.warn('Failed to check for active editors:', error);
            // Show offline status
            const statusIndicator = document.querySelector('.status-indicator');
            if (statusIndicator) {
                statusIndicator.className = 'status-indicator offline me-2';
                statusIndicator.title = 'Disconnected';
            }
            
            const editorStatus = document.querySelector('.editor-status');
            if (editorStatus) {
                editorStatus.textContent = 'Disconnected';
            }
        });
}

/**
 * Send heartbeat to show we're actively editing
 */
function sendEditorHeartbeat() {
    const pageIdElement = document.getElementById('pageId');
    if (!pageIdElement) {
        console.warn("Page ID element not found for editor heartbeat");
        return;
    }
    const pageId = pageIdElement.value;
    if (!pageId) return;
    
    fetch(`/admin/api/pages/${pageId}/heartbeat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            page_id: pageId,
            timestamp: new Date().toISOString()
        })
    })
    .catch(error => {
        console.warn('Failed to send editor heartbeat:', error);
    });
}

/**
 * Update editor status display based on server response
 */
function updateEditorStatus(data) {
    const statusIndicator = document.querySelector('.status-indicator');
    const editorStatus = document.querySelector('.editor-status');
    
    if (!statusIndicator || !editorStatus) return;
    
    if (data.online) {
        statusIndicator.className = 'status-indicator online me-2';
        statusIndicator.title = 'Connected';
        
        if (data.active_editors && data.active_editors.length > 1) {
            // Multiple editors active
            if (data.active_editors.length === 2) {
                // Show the other person's name
                const otherEditor = data.active_editors.find(editor => editor.id !== data.current_user_id);
                editorStatus.textContent = `You and ${otherEditor ? otherEditor.name : 'another user'} editing`;
            } else {
                // Show count of other editors
                editorStatus.textContent = `You and ${data.active_editors.length - 1} others editing`;
            }
            
            // Change indicator to "busy" state
            statusIndicator.className = 'status-indicator busy me-2';
        } else {
            // Just us editing
            editorStatus.textContent = 'Just you editing';
        }
    } else {
        // Offline status
        statusIndicator.className = 'status-indicator offline me-2';
        statusIndicator.title = 'Disconnected';
        editorStatus.textContent = 'Disconnected';
    }
}

/**
 * Track page changes for collaborative editing
 */
function trackPageChanges() {
    let lastChange = Date.now();
    
    // Update last change time when content is modified
    document.addEventListener('contentChanged', () => { lastChange = Date.now(); });
    document.addEventListener('sectionsReordered', () => { lastChange = Date.now(); });
    document.addEventListener('blocksReordered', () => { lastChange = Date.now(); });
    document.addEventListener('textEditorChanged', () => { lastChange = Date.now(); });
    document.addEventListener('sectionSettingsChanged', () => { lastChange = Date.now(); });
    document.addEventListener('blockSettingsChanged', () => { lastChange = Date.now(); });
    
    // On form inputs
    document.querySelectorAll('input, textarea, select').forEach(el => {
        el.addEventListener('change', () => { lastChange = Date.now(); });
        el.addEventListener('input', () => { lastChange = Date.now(); });
    });
    
    // Include last change time with heartbeats
    const originalSendHeartbeat = window.sendEditorHeartbeat;
    window.sendEditorHeartbeat = function() {
        const pageIdElement = document.getElementById('pageId');
        if (!pageIdElement) {
            console.warn("Page ID element not found for trackPageChanges");
            return;
        }
        const pageId = pageIdElement.value;
        if (!pageId) return;
        
        fetch(`/admin/api/pages/${pageId}/heartbeat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                page_id: pageId,
                timestamp: new Date().toISOString(),
                last_change: lastChange
            })
        })
        .catch(error => {
            console.warn('Failed to send editor heartbeat:', error);
        });
    };
}

/**
 * Initialize block templates system
 */
function initBlockTemplates() {
    // Add template button to all block type selectors
    document.querySelectorAll('.block-actions').forEach(container => {
        const sectionId = container.closest('.page-section').getAttribute('data-section-id');
        
        // Find the add block button
        const addBlockBtn = container.querySelector('.add-block-btn');
        if (!addBlockBtn) return;
        
        // Add template button next to it
        if (!container.querySelector('.use-template-btn')) {
            const templateBtn = document.createElement('button');
            templateBtn.className = 'btn btn-secondary use-template-btn ms-2';
            templateBtn.setAttribute('type', 'button');
            templateBtn.setAttribute('data-section-id', sectionId);
            templateBtn.innerHTML = '<i class="fas fa-copy me-1"></i> Use Template';
            
            // Add after add block button
            addBlockBtn.insertAdjacentElement('afterend', templateBtn);
            
            // Add click event
            templateBtn.addEventListener('click', function() {
                showBlockTemplatesDialog(sectionId);
            });
        }
    });
    
    // Add "Save as Template" button to all content blocks
    document.querySelectorAll('.block-controls').forEach(controls => {
        if (!controls.querySelector('.save-template-btn')) {
            const blockId = controls.closest('.content-block').getAttribute('data-block-id');
            
            // Create save template button
            const saveBtn = document.createElement('button');
            saveBtn.className = 'btn btn-sm btn-outline-secondary save-template-btn';
            saveBtn.setAttribute('type', 'button');
            saveBtn.setAttribute('data-block-id', blockId);
            saveBtn.setAttribute('title', 'Save as reusable block template');
            saveBtn.innerHTML = '<i class="fas fa-save"></i>';
            
            // Add to controls
            controls.appendChild(saveBtn);
            
            // Add click event
            saveBtn.addEventListener('click', function(e) {
                e.stopPropagation(); // Prevent block selection
                saveBlockAsTemplate(blockId);
            });
        }
    });
}

/**
 * Show block templates dialog
 */
function showBlockTemplatesDialog(sectionId) {
    // Create the modal if it doesn't exist
    if (!document.getElementById('blockTemplatesDialog')) {
        const dialog = document.createElement('div');
        dialog.id = 'blockTemplatesDialog';
        dialog.className = 'modal fade';
        dialog.setAttribute('tabindex', '-1');
        dialog.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-copy me-2"></i> Block Templates
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row mb-3">
                            <div class="col-md-4">
                                <div class="list-group" id="templatesList">
                                    <div class="text-center p-5">
                                        <div class="spinner-border text-primary" role="status">
                                            <span class="visually-hidden">Loading...</span>
                                        </div>
                                        <p class="mt-3">Loading templates...</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-8">
                                <div id="templatePreview" class="border rounded p-3 bg-light">
                                    <p class="text-muted text-center p-5">
                                        <i class="fas fa-mouse-pointer mb-3 d-block" style="font-size: 24px;"></i>
                                        Select a template to preview it
                                    </p>
                                </div>
                            </div>
                        </div>
                        <div id="templatesError" class="alert alert-danger d-none">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            <span id="templatesErrorMessage">An error occurred</span>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" id="useTemplateBtn" class="btn btn-primary" disabled>
                            <i class="fas fa-plus me-1"></i> Use Template
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(dialog);
    }
    
    // Initialize modal
    const modal = new bootstrap.Modal(document.getElementById('blockTemplatesDialog'));
    modal.show();
    
    // Load templates
    loadBlockTemplates(sectionId);
    
    // Use template button handler
    const useTemplateBtn = document.getElementById('useTemplateBtn');
    useTemplateBtn.onclick = function() {
        useSelectedTemplate(sectionId);
        modal.hide();
    };
}

/**
 * Load block templates from the server
 */
function loadBlockTemplates(sectionId) {
    const templatesList = document.getElementById('templatesList');
    
    // Call API to get templates
    fetch('/admin/api/pages/block-templates')
        .then(response => response.json())
        .then(data => {
            if (data.templates && data.templates.length > 0) {
                // Clear loading state
                templatesList.innerHTML = '';
                
                // Add templates to list
                data.templates.forEach((template, index) => {
                    const templateItem = document.createElement('a');
                    templateItem.className = 'list-group-item list-group-item-action';
                    templateItem.setAttribute('href', '#');
                    templateItem.setAttribute('data-template-id', template.id);
                    
                    let icon = 'puzzle-piece';
                    if (template.block_type === 'text') icon = 'align-left';
                    if (template.block_type === 'image') icon = 'image';
                    if (template.block_type === 'button') icon = 'link';
                    
                    templateItem.innerHTML = `
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">
                                <i class="fas fa-${icon} me-2"></i>
                                ${template.name}
                            </h6>
                            <small class="text-muted">${template.block_type}</small>
                        </div>
                        <small class="text-truncate d-block">${template.description || 'No description'}</small>
                    `;
                    
                    // Handle click
                    templateItem.addEventListener('click', function(e) {
                        e.preventDefault();
                        
                        // Update active selection
                        document.querySelectorAll('.list-group-item').forEach(item => {
                            item.classList.remove('active');
                        });
                        templateItem.classList.add('active');
                        
                        // Update preview
                        previewTemplate(template);
                        
                        // Enable use button
                        document.getElementById('useTemplateBtn').disabled = false;
                        
                        // Store selected template
                        window.selectedTemplate = template;
                    });
                    
                    templatesList.appendChild(templateItem);
                    
                    // Select first template by default
                    if (index === 0) {
                        templateItem.click();
                    }
                });
            } else {
                // No templates
                templatesList.innerHTML = `
                    <div class="text-center p-4">
                        <i class="fas fa-info-circle mb-3 d-block" style="font-size: 24px;"></i>
                        <p>No templates found.</p>
                        <p class="text-muted small">Save a block as a template to reuse it across your site.</p>
                    </div>
                `;
                
                // Disable use button
                document.getElementById('useTemplateBtn').disabled = true;
            }
        })
        .catch(error => {
            // Show error
            templatesList.innerHTML = `
                <div class="text-center p-4">
                    <i class="fas fa-exclamation-triangle mb-3 d-block" style="font-size: 24px;"></i>
                    <p>Failed to load templates.</p>
                    <button class="btn btn-sm btn-outline-primary" onclick="loadBlockTemplates('${sectionId}')">
                        <i class="fas fa-sync me-1"></i> Retry
                    </button>
                </div>
            `;
            
            // Log error
            console.error('Error loading block templates:', error);
            
            // Disable use button
            document.getElementById('useTemplateBtn').disabled = true;
        });
}

/**
 * Preview template in the dialog
 */
function previewTemplate(template) {
    const previewContainer = document.getElementById('templatePreview');
    
    // Simple preview based on block type
    switch (template.block_type) {
        case 'text':
            previewContainer.innerHTML = template.content.html || '<p>No content</p>';
            break;
        case 'image':
            previewContainer.innerHTML = `
                <img src="${template.content.url || ''}" alt="${template.content.alt || 'Template image'}" 
                    class="img-fluid rounded">
            `;
            break;
        case 'button':
            previewContainer.innerHTML = `
                <div class="text-center">
                    <button type="button" class="btn btn-${template.content.style || 'primary'}">
                        ${template.content.text || 'Button'}
                    </button>
                </div>
            `;
            break;
        default:
            previewContainer.innerHTML = `
                <div class="text-center p-4">
                    <i class="fas fa-puzzle-piece mb-3 d-block" style="font-size: 24px;"></i>
                    <p>Preview not available for this template type.</p>
                </div>
            `;
    }
}

/**
 * Use the selected template
 */
function useSelectedTemplate(sectionId) {
    if (!window.selectedTemplate) {
        showNotification('No template selected', 'warning');
        return;
    }
    
    // Create block from template
    const blockData = {
        section_id: sectionId,
        block_type: window.selectedTemplate.block_type,
        position: getNextBlockPosition(sectionId),
        content: window.selectedTemplate.content,
        settings: window.selectedTemplate.settings,
        template_id: window.selectedTemplate.id
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
            showNotification('Block template added successfully', 'success');
            // Refresh the page to show the new block
            location.reload();
        } else {
            showNotification('Error adding block template', 'danger');
        }
    })
    .catch(error => {
        console.error('Error adding block template:', error);
        showNotification('Error: ' + error.message, 'danger');
    });
}

/**
 * Save block as a template
 */
function saveBlockAsTemplate(blockId) {
    // Create the modal if it doesn't exist
    if (!document.getElementById('saveTemplateDialog')) {
        const dialog = document.createElement('div');
        dialog.id = 'saveTemplateDialog';
        dialog.className = 'modal fade';
        dialog.setAttribute('tabindex', '-1');
        dialog.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-save me-2"></i> Save as Template
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label for="templateName" class="form-label">Template Name</label>
                            <input type="text" class="form-control" id="templateName" required
                                placeholder="e.g., Feature Card, Product Highlight, etc.">
                        </div>
                        <div class="mb-3">
                            <label for="templateDescription" class="form-label">Description (optional)</label>
                            <textarea class="form-control" id="templateDescription" rows="2"
                                placeholder="Describe this template"></textarea>
                        </div>
                        <div class="form-check mb-3">
                            <input class="form-check-input" type="checkbox" id="templateGlobal" checked>
                            <label class="form-check-label" for="templateGlobal">
                                Make available to all pages
                            </label>
                        </div>
                        <div id="saveTemplateError" class="alert alert-danger d-none">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            <span id="saveTemplateErrorMessage">An error occurred</span>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" id="saveTemplateBtn" class="btn btn-primary">
                            <i class="fas fa-save me-1"></i> Save Template
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(dialog);
    }
    
    // Store block ID for later use
    window.templateBlockId = blockId;
    
    // Initialize modal
    const modal = new bootstrap.Modal(document.getElementById('saveTemplateDialog'));
    modal.show();
    
    // Save button handler
    const saveTemplateBtn = document.getElementById('saveTemplateBtn');
    saveTemplateBtn.onclick = function() {
        // Get template details
        const name = document.getElementById('templateName').value.trim();
        if (!name) {
            showNotification('Please enter a template name', 'warning');
            return;
        }
        
        const description = document.getElementById('templateDescription').value.trim();
        const isGlobal = document.getElementById('templateGlobal').checked;
        
        // Show loading state
        saveTemplateBtn.disabled = true;
        saveTemplateBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Saving...';
        
        // Call API to save template
        fetch('/admin/api/pages/block-templates', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                block_id: blockId,
                name: name,
                description: description,
                is_global: isGlobal
            })
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading state
            saveTemplateBtn.disabled = false;
            saveTemplateBtn.innerHTML = '<i class="fas fa-save me-1"></i> Save Template';
            
            if (data.success) {
                // Show success and close modal
                showNotification('Block saved as a template successfully', 'success');
                modal.hide();
            } else {
                // Show error
                document.getElementById('saveTemplateError').classList.remove('d-none');
                document.getElementById('saveTemplateErrorMessage').textContent = data.error || 'Failed to save template';
            }
        })
        .catch(error => {
            // Show error
            saveTemplateBtn.disabled = false;
            saveTemplateBtn.innerHTML = '<i class="fas fa-save me-1"></i> Save Template';
            
            document.getElementById('saveTemplateError').classList.remove('d-none');
            document.getElementById('saveTemplateErrorMessage').textContent = error.message;
            
            console.error('Error saving block template:', error);
        });
    };
}

/**
 * Initialize split view functionality for the page builder
 * Allows for side-by-side editing and preview with resizable panels
 */
function initSplitView() {
    console.log("Initializing split view functionality");
    
    const splitViewToggle = document.getElementById('splitViewToggle');
    const editorLayout = document.querySelector('.editor-layout');
    const livePreviewPanel = document.getElementById('livePreviewPanel');
    const splitViewResizer = document.getElementById('splitViewResizer');
    
    // Log all elements to see what's missing
    console.log("Split view toggle element:", splitViewToggle);
    console.log("Editor layout element:", editorLayout);
    console.log("Live preview panel element:", livePreviewPanel);
    console.log("Split view resizer element:", splitViewResizer);
    
    // Check if we have all required elements
    if (!splitViewToggle || !editorLayout || !livePreviewPanel || !splitViewResizer) {
        console.warn("Split view elements not found, skipping initialization");
        return;
    }
    
    // Toggle split view mode
    splitViewToggle.addEventListener('click', function() {
        const isInSplitView = editorLayout.classList.contains('split-view');
        
        if (isInSplitView) {
            // Exit split view
            editorLayout.classList.remove('split-view');
            livePreviewPanel.style.display = 'none';
            splitViewResizer.style.display = 'none';
            
            // Update button text
            splitViewToggle.querySelector('.split-text').textContent = 'Split View';
            splitViewToggle.title = 'Enable split view mode';
            
            // Save preference
            localStorage.setItem('pageBuilderSplitView', 'false');
        } else {
            // Enter split view
            editorLayout.classList.add('split-view');
            livePreviewPanel.style.display = 'flex';
            splitViewResizer.style.display = 'block';
            
            // Update button text
            splitViewToggle.querySelector('.split-text').textContent = 'Exit Split View';
            splitViewToggle.title = 'Exit split view mode';
            
            // Save preference
            localStorage.setItem('pageBuilderSplitView', 'true');
            
            // Force preview update
            updateLivePreview();
        }
    });
    
    // Set up the resizer functionality
    let isResizing = false;
    let startX, startWidth, previewStartWidth;
    
    splitViewResizer.addEventListener('mousedown', function(e) {
        isResizing = true;
        startX = e.clientX;
        
        // Get the current width of panels
        const canvasArea = document.querySelector('.editor-canvas');
        startWidth = canvasArea.offsetWidth;
        previewStartWidth = livePreviewPanel.offsetWidth;
        
        // Add resizing class
        splitViewResizer.classList.add('dragging');
        
        // Add event listeners
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
        
        // Prevent text selection during resize
        e.preventDefault();
    });
    
    function handleMouseMove(e) {
        if (!isResizing) return;
        
        // Calculate how far the mouse has moved
        const movementX = e.clientX - startX;
        
        // Calculate new widths
        const containerWidth = editorLayout.offsetWidth;
        let newCanvasWidth = startWidth + movementX;
        let newPreviewWidth = previewStartWidth - movementX;
        
        // Enforce minimum widths (20% of container)
        const minWidth = containerWidth * 0.2;
        if (newCanvasWidth < minWidth) newCanvasWidth = minWidth;
        if (newPreviewWidth < minWidth) newPreviewWidth = minWidth;
        
        // Calculate percentages
        const canvasPercent = (newCanvasWidth / containerWidth) * 100;
        const previewPercent = (newPreviewWidth / containerWidth) * 100;
        
        // Apply new widths
        document.querySelector('.editor-canvas').style.width = `${canvasPercent}%`;
        livePreviewPanel.style.width = `${previewPercent}%`;
    }
    
    function handleMouseUp() {
        isResizing = false;
        splitViewResizer.classList.remove('dragging');
        
        // Remove event listeners
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
    }
    
    // Initialize based on saved preference
    const savedPreference = localStorage.getItem('pageBuilderSplitView');
    if (savedPreference === 'true') {
        // Simulate click to enable split view
        splitViewToggle.click();
    }
}

/**
 * Updates the preview panel with current content
 */
function updateLivePreview() {
    console.log("Updating live preview");
    const previewFrame = document.getElementById('previewFrame');
    if (!previewFrame) {
        console.error("Preview frame not found");
        return;
    }
    
    // Show loading indicator
    const loadingIndicator = document.querySelector('.preview-loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.style.display = 'block';
    }
    
    // Get the current preview URL
    const pageIdElement = document.getElementById('pageId');
    if (!pageIdElement) {
        console.error("Page ID element not found");
        return;
    }
    
    const pageId = pageIdElement.value;
    const previewUrl = `/admin/pages/${pageId}/preview?timestamp=${Date.now()}`;
    
    console.log("Loading preview from:", previewUrl);
    
    // Update the iframe source
    previewFrame.src = previewUrl;
    
    // Check if live preview panel is visible and in split view mode
    const livePreviewPanel = document.getElementById('livePreviewPanel');
    const editorLayout = document.querySelector('.editor-layout');
    
    if (livePreviewPanel && editorLayout && editorLayout.classList.contains('split-view')) {
        livePreviewPanel.style.display = 'flex';
    }
    
    // Hide loading indicator when iframe loads
    previewFrame.onload = function() {
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
        console.log("Preview loaded successfully");
    };
    
    // Handle errors
    previewFrame.onerror = function() {
        console.error("Error loading preview");
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
        
        const errorContainer = document.querySelector('.preview-error-container');
        if (errorContainer) {
            errorContainer.style.display = 'block';
        }
    };
}
