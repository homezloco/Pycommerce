
/**
 * Page Builder JavaScript
 * Handles the interactive functionality of the visual page builder
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log("Page Builder JS initialized");
    
    // Check if Sortable.js is loaded, if not, load it
    if (typeof Sortable === 'undefined') {
        console.error("Sortable is not defined - attempting to load it");
        
        // Load Sortable.js dynamically
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/sortablejs@1.14.0/Sortable.min.js';
        script.onload = function() {
            console.log("Sortable.js loaded dynamically");
            
            // Continue with initialization once loaded
            initPageBuilder();
        };
        document.head.appendChild(script);
    } else {
        // Sortable is already loaded, proceed with initialization
        initPageBuilder();
    }
});

function initPageBuilder() {
    // Initialize section management
    initSectionManager();
    
    // Initialize content block management
    initBlockManager();
    
    // Setup save functionality
    setupSaveHandler();
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

function showNotification(message, type = 'info') {
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
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.role = 'alert';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to container
    container.appendChild(notification);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}
