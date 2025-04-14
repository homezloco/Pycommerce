
/**
 * Page Editor JavaScript
 * Handles the interactive functionality of the visual page editor
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log("Page Editor JS initialized");
    
    // Initialize WYSIWYG editors
    initEditors();
    
    // Initialize page controls
    initPageControls();
    
    // Initialize section management
    initSectionManager();
    
    // Initialize drag and drop
    initDragDrop();
});

// Store all Quill editor instances
const editors = {};

function initEditors() {
    // Check if Quill is loaded
    if (typeof Quill === 'undefined') {
        console.error("Quill is not loaded - attempting to load it");
        loadQuillDynamically();
        return;
    }
    
    // Initialize all Quill editors in content blocks
    document.querySelectorAll('.quill-editor').forEach(function(editorElement) {
        const blockId = editorElement.getAttribute('data-block-id');
        
        if (blockId) {
            try {
                // Create Quill editor with toolbar
                const quill = new Quill(editorElement, {
                    modules: {
                        toolbar: [
                            ['bold', 'italic', 'underline', 'strike'],
                            [{ 'header': 1 }, { 'header': 2 }],
                            [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                            ['link', 'image'],
                            [{ 'align': [] }],
                            ['clean']
                        ]
                    },
                    theme: 'snow'
                });
                
                // Store editor instance
                editors[blockId] = quill;
                
                // Add AI assist button
                addAIAssistButton(blockId, quill);
            } catch (e) {
                console.error(`Error initializing Quill editor for block ${blockId}:`, e);
            }
        }
    });
    
    // Also handle TinyMCE if it's being used
    if (typeof tinymce !== 'undefined') {
        tinymce.init({
            selector: '.tinymce-editor',
            height: 300,
            menubar: true,
            plugins: [
                'advlist autolink lists link image charmap print preview anchor',
                'searchreplace visualblocks code fullscreen',
                'insertdatetime media table paste code help wordcount'
            ],
            toolbar: 'undo redo | formatselect | ' +
                'bold italic backcolor | alignleft aligncenter ' +
                'alignright alignjustify | bullist numlist outdent indent | ' +
                'removeformat | help',
            setup: function(editor) {
                // Add AI assist button
                editor.ui.registry.addButton('aiassist', {
                    text: 'AI Assist',
                    tooltip: 'Generate content with AI',
                    onAction: function() {
                        showAIPromptDialog(editor.id, function(content) {
                            editor.insertContent(content);
                        });
                    }
                });
            }
        });
    }
}

function loadQuillDynamically() {
    // Load Quill CSS
    const quillCSS = document.createElement('link');
    quillCSS.rel = 'stylesheet';
    quillCSS.href = 'https://cdn.quilljs.com/1.3.6/quill.snow.css';
    document.head.appendChild(quillCSS);
    
    // Load Quill JS
    const quillScript = document.createElement('script');
    quillScript.src = 'https://cdn.quilljs.com/1.3.6/quill.min.js';
    quillScript.onload = function() {
        console.log("Quill loaded dynamically");
        // Try to initialize editors again
        setTimeout(initEditors, 500);
    };
    document.head.appendChild(quillScript);
}

function addAIAssistButton(blockId, quill) {
    // Get the toolbar element
    const toolbar = quill.root.parentElement.querySelector('.ql-toolbar');
    
    if (toolbar) {
        // Create AI assist button
        const aiButton = document.createElement('button');
        aiButton.className = 'btn btn-primary btn-sm ms-2';
        aiButton.innerHTML = '<i class="fas fa-robot"></i> AI Assist';
        aiButton.onclick = function(e) {
            e.preventDefault();
            showAIPromptDialog(blockId, function(content) {
                // Insert content at cursor position
                const range = quill.getSelection();
                if (range) {
                    quill.insertText(range.index, content);
                } else {
                    quill.insertText(quill.getLength(), content);
                }
            });
        };
        
        // Add button to toolbar
        toolbar.appendChild(aiButton);
    }
}

function showAIPromptDialog(blockId, callback) {
    // Create modal element
    const modalId = `aiPromptModal-${blockId}`;
    
    // Check if modal already exists
    let modal = document.getElementById(modalId);
    
    if (!modal) {
        // Create modal
        const modalHTML = `
            <div class="modal fade" id="${modalId}" tabindex="-1" aria-labelledby="${modalId}-label" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="${modalId}-label">Generate Content with AI</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <form id="aiPromptForm-${blockId}">
                                <div class="mb-3">
                                    <label for="aiPrompt-${blockId}" class="form-label">What would you like the AI to write about?</label>
                                    <textarea class="form-control" id="aiPrompt-${blockId}" rows="3" placeholder="E.g., Write a paragraph about sustainable products"></textarea>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Content style</label>
                                    <select class="form-select" id="aiStyle-${blockId}">
                                        <option value="informative">Informative</option>
                                        <option value="persuasive">Persuasive</option>
                                        <option value="casual">Casual</option>
                                        <option value="formal">Formal</option>
                                        <option value="enthusiastic">Enthusiastic</option>
                                    </select>
                                </div>
                            </form>
                            <div id="aiResult-${blockId}" class="d-none">
                                <div class="alert alert-primary">
                                    <div id="aiContent-${blockId}"></div>
                                </div>
                            </div>
                            <div id="aiLoading-${blockId}" class="d-none text-center py-3">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <p class="mt-2">Generating content...</p>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="generateBtn-${blockId}">Generate</button>
                            <button type="button" class="btn btn-success d-none" id="insertBtn-${blockId}">Insert Content</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Get the new modal
        modal = document.getElementById(modalId);
        
        // Add event listeners
        document.getElementById(`generateBtn-${blockId}`).addEventListener('click', function() {
            generateAIContent(blockId);
        });
        
        document.getElementById(`insertBtn-${blockId}`).addEventListener('click', function() {
            const content = document.getElementById(`aiContent-${blockId}`).innerHTML;
            callback(content);
            
            // Close modal
            const bsModal = bootstrap.Modal.getInstance(modal);
            bsModal.hide();
        });
    }
    
    // Reset form
    document.getElementById(`aiPrompt-${blockId}`).value = '';
    document.getElementById(`aiResult-${blockId}`).classList.add('d-none');
    document.getElementById(`aiLoading-${blockId}`).classList.add('d-none');
    document.getElementById(`generateBtn-${blockId}`).classList.remove('d-none');
    document.getElementById(`insertBtn-${blockId}`).classList.add('d-none');
    
    // Show modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

function generateAIContent(blockId) {
    // Get prompt and style
    const prompt = document.getElementById(`aiPrompt-${blockId}`).value;
    const style = document.getElementById(`aiStyle-${blockId}`).value;
    
    if (!prompt) {
        alert('Please enter a prompt for the AI');
        return;
    }
    
    // Show loading, hide generate button
    document.getElementById(`aiLoading-${blockId}`).classList.remove('d-none');
    document.getElementById(`generateBtn-${blockId}`).classList.add('d-none');
    document.getElementById(`aiResult-${blockId}`).classList.add('d-none');
    
    // Get tenant ID for API call
    const tenantId = document.getElementById('tenantId')?.value || '';
    
    // Call API to generate content
    fetch('/admin/api/ai/generate-content', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            prompt: prompt,
            style: style,
            tenant_id: tenantId
        })
    })
    .then(response => response.json())
    .then(data => {
        // Hide loading
        document.getElementById(`aiLoading-${blockId}`).classList.add('d-none');
        
        if (data.success) {
            // Show result and insert button
            document.getElementById(`aiContent-${blockId}`).innerHTML = data.content;
            document.getElementById(`aiResult-${blockId}`).classList.remove('d-none');
            document.getElementById(`insertBtn-${blockId}`).classList.remove('d-none');
        } else {
            // Show error and generate button
            alert('Error generating content: ' + (data.error || 'Unknown error'));
            document.getElementById(`generateBtn-${blockId}`).classList.remove('d-none');
        }
    })
    .catch(error => {
        // Hide loading, show generate button
        document.getElementById(`aiLoading-${blockId}`).classList.add('d-none');
        document.getElementById(`generateBtn-${blockId}`).classList.remove('d-none');
        
        // Show error
        alert('Error: ' + error.message);
        console.error('Error generating AI content:', error);
    });
}

function initPageControls() {
    // Page save button
    const saveBtn = document.getElementById('savePageBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', savePage);
    }
    
    // Page settings button
    const settingsBtn = document.getElementById('pageSettingsBtn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', function() {
            const settingsPanel = document.getElementById('pageSettingsPanel');
            if (settingsPanel) {
                settingsPanel.classList.toggle('show');
            }
        });
    }
    
    // Preview button
    const previewBtn = document.getElementById('previewPageBtn');
    if (previewBtn) {
        previewBtn.addEventListener('click', previewPage);
    }
}

function savePage() {
    // Get page data
    const pageId = document.getElementById('pageId').value;
    const title = document.getElementById('pageTitle').value;
    const slug = document.getElementById('pageSlug').value;
    const metaTitle = document.getElementById('metaTitle')?.value || '';
    const metaDescription = document.getElementById('metaDescription')?.value || '';
    const isPublished = document.getElementById('isPublished')?.checked || false;
    
    // Validate
    if (!title || !slug) {
        showNotification('Please enter a title and slug for the page', 'warning');
        return;
    }
    
    // Show loading
    showNotification('Saving page...', 'info');
    
    // Save all editor content to hidden fields
    for (const blockId in editors) {
        const editor = editors[blockId];
        const contentField = document.getElementById(`blockContent-${blockId}`);
        if (contentField && editor) {
            contentField.value = editor.root.innerHTML;
        }
    }
    
    // Get layout data from form
    const layoutData = getSectionsData();
    
    // Submit form
    document.getElementById('pageForm').submit();
}

function getSectionsData() {
    // Build layout data from sections
    const sections = document.querySelectorAll('.page-section');
    const layoutData = {
        sections: []
    };
    
    sections.forEach((section, sectionIndex) => {
        const sectionId = section.getAttribute('data-section-id');
        const sectionType = section.getAttribute('data-section-type');
        
        const sectionData = {
            id: sectionId,
            type: sectionType,
            position: sectionIndex,
            settings: getSectionSettings(sectionId),
            blocks: []
        };
        
        // Get blocks for this section
        const blocks = section.querySelectorAll('.content-block');
        blocks.forEach((block, blockIndex) => {
            const blockId = block.getAttribute('data-block-id');
            const blockType = block.getAttribute('data-block-type');
            
            const blockData = {
                id: blockId,
                type: blockType,
                position: blockIndex,
                content: getBlockContent(blockId),
                settings: getBlockSettings(blockId)
            };
            
            sectionData.blocks.push(blockData);
        });
        
        layoutData.sections.push(sectionData);
    });
    
    return layoutData;
}

function getSectionSettings(sectionId) {
    // Get settings from form fields
    const settingsForm = document.getElementById(`sectionSettings-${sectionId}`);
    if (!settingsForm) return {};
    
    const settings = {};
    const formData = new FormData(settingsForm);
    for (const [key, value] of formData.entries()) {
        settings[key] = value;
    }
    
    return settings;
}

function getBlockContent(blockId) {
    // Get content from editor or form field
    if (editors[blockId]) {
        return {
            html: editors[blockId].root.innerHTML
        };
    }
    
    // Try to get from form field
    const contentField = document.getElementById(`blockContent-${blockId}`);
    if (contentField) {
        return {
            html: contentField.value
        };
    }
    
    return {};
}

function getBlockSettings(blockId) {
    // Get settings from form fields
    const settingsForm = document.getElementById(`blockSettings-${blockId}`);
    if (!settingsForm) return {};
    
    const settings = {};
    const formData = new FormData(settingsForm);
    for (const [key, value] of formData.entries()) {
        settings[key] = value;
    }
    
    return settings;
}

function previewPage() {
    // Save all editor content to hidden fields before preview
    for (const blockId in editors) {
        const editor = editors[blockId];
        const contentField = document.getElementById(`blockContent-${blockId}`);
        if (contentField && editor) {
            contentField.value = editor.root.innerHTML;
        }
    }
    
    // Get page ID for preview URL
    const pageId = document.getElementById('pageId').value;
    
    // Open preview in new tab
    window.open(`/admin/pages/preview/${pageId}`, '_blank');
}

function initSectionManager() {
    // Add section button
    const addSectionBtn = document.getElementById('addSectionBtn');
    if (addSectionBtn) {
        addSectionBtn.addEventListener('click', function() {
            const sectionTypeSelect = document.getElementById('sectionTypeSelect');
            if (sectionTypeSelect) {
                const sectionType = sectionTypeSelect.value;
                if (sectionType) {
                    addSection(sectionType);
                } else {
                    showNotification('Please select a section type', 'warning');
                }
            }
        });
    }
    
    // Section actions (via event delegation)
    document.addEventListener('click', function(e) {
        // Delete section button
        if (e.target.matches('.delete-section-btn')) {
            const sectionId = e.target.getAttribute('data-section-id');
            if (confirm('Are you sure you want to delete this section?')) {
                deleteSection(sectionId);
            }
        }
        
        // Add block button
        if (e.target.matches('.add-block-btn')) {
            const sectionId = e.target.getAttribute('data-section-id');
            const blockTypeSelect = document.getElementById(`blockTypeSelect-${sectionId}`);
            if (blockTypeSelect) {
                const blockType = blockTypeSelect.value;
                if (blockType) {
                    addBlock(sectionId, blockType);
                } else {
                    showNotification('Please select a block type', 'warning');
                }
            }
        }
        
        // Delete block button
        if (e.target.matches('.delete-block-btn')) {
            const blockId = e.target.getAttribute('data-block-id');
            if (confirm('Are you sure you want to delete this block?')) {
                deleteBlock(blockId);
            }
        }
    });
}

function addSection(sectionType) {
    // Get page ID
    const pageId = document.getElementById('pageId').value;
    
    // Show loading
    showNotification('Adding section...', 'info');
    
    // Call API to add section
    fetch('/admin/api/pages/sections', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            page_id: pageId,
            section_type: sectionType,
            position: document.querySelectorAll('.page-section').length,
            settings: getDefaultSectionSettings(sectionType)
        })
    })
    .then(response => response.json())
    .then(data => {
        // Reload page to show new section
        location.reload();
    })
    .catch(error => {
        console.error('Error adding section:', error);
        showNotification('Error adding section: ' + error.message, 'danger');
    });
}

function getDefaultSectionSettings(sectionType) {
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
    
    return defaults[sectionType] || { background: 'white', padding: 'medium' };
}

function deleteSection(sectionId) {
    // Show loading
    showNotification('Deleting section...', 'info');
    
    // Call API to delete section
    fetch(`/admin/api/pages/sections/${sectionId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove section from DOM
            const section = document.querySelector(`.page-section[data-section-id="${sectionId}"]`);
            if (section) {
                section.remove();
                showNotification('Section deleted', 'success');
            } else {
                location.reload();
            }
        } else {
            showNotification('Error deleting section: ' + (data.message || 'Unknown error'), 'danger');
        }
    })
    .catch(error => {
        console.error('Error deleting section:', error);
        showNotification('Error deleting section: ' + error.message, 'danger');
    });
}

function addBlock(sectionId, blockType) {
    // Show loading
    showNotification('Adding block...', 'info');
    
    // Call API to add block
    fetch('/admin/api/pages/blocks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            section_id: sectionId,
            block_type: blockType,
            position: document.querySelectorAll(`.content-block[data-section-id="${sectionId}"]`).length,
            content: getDefaultBlockContent(blockType),
            settings: getDefaultBlockSettings(blockType)
        })
    })
    .then(response => response.json())
    .then(data => {
        // Reload page to show new block
        location.reload();
    })
    .catch(error => {
        console.error('Error adding block:', error);
        showNotification('Error adding block: ' + error.message, 'danger');
    });
}

function getDefaultBlockContent(blockType) {
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

function deleteBlock(blockId) {
    // Show loading
    showNotification('Deleting block...', 'info');
    
    // Call API to delete block
    fetch(`/admin/api/pages/blocks/${blockId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove block from DOM
            const block = document.querySelector(`.content-block[data-block-id="${blockId}"]`);
            if (block) {
                block.remove();
                showNotification('Block deleted', 'success');
            } else {
                location.reload();
            }
        } else {
            showNotification('Error deleting block: ' + (data.message || 'Unknown error'), 'danger');
        }
    })
    .catch(error => {
        console.error('Error deleting block:', error);
        showNotification('Error deleting block: ' + error.message, 'danger');
    });
}

function initDragDrop() {
    // If Sortable library is available, use it
    if (typeof Sortable !== 'undefined') {
        // Make sections sortable
        const sectionsContainer = document.getElementById('sectionsContainer');
        if (sectionsContainer) {
            Sortable.create(sectionsContainer, {
                handle: '.section-drag-handle',
                animation: 150,
                onEnd: updateSectionPositions
            });
        }
        
        // Make blocks sortable within each section
        document.querySelectorAll('.blocks-container').forEach(container => {
            Sortable.create(container, {
                handle: '.block-drag-handle',
                animation: 150,
                onEnd: updateBlockPositions
            });
        });
    }
}

function updateSectionPositions() {
    const sections = document.querySelectorAll('.page-section');
    const positions = [];
    
    sections.forEach((section, index) => {
        positions.push({
            id: section.getAttribute('data-section-id'),
            position: index
        });
    });
    
    // TODO: Call API to update positions
    console.log('Section positions updated:', positions);
}

function updateBlockPositions() {
    // For each section, update block positions
    document.querySelectorAll('.blocks-container').forEach(container => {
        const sectionId = container.getAttribute('data-section-id');
        const blocks = container.querySelectorAll('.content-block');
        
        const positions = [];
        blocks.forEach((block, index) => {
            positions.push({
                id: block.getAttribute('data-block-id'),
                position: index
            });
        });
        
        // TODO: Call API to update positions
        console.log(`Block positions updated for section ${sectionId}:`, positions);
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
