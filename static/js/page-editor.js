
/**
 * Page Builder Editor initialization
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Quill editors if needed
    const contentBlocks = document.querySelectorAll('.content-block-editor');
    if (contentBlocks.length > 0) {
        contentBlocks.forEach(function(block) {
            const quillEditor = new Quill(block, {
                theme: 'snow',
                modules: {
                    toolbar: [
                        [{ 'header': [1, 2, 3, false] }],
                        ['bold', 'italic', 'underline', 'strike'],
                        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                        [{ 'color': [] }, { 'background': [] }],
                        ['link', 'image'],
                        ['clean'],
                        ['ai-assist'] // Custom button for AI functionality
                    ]
                }
            });
            
            // Add AI assist button to toolbar
            const toolbar = block.querySelector('.ql-toolbar');
            if (toolbar) {
                const aiButton = document.createElement('button');
                aiButton.className = 'btn btn-primary btn-sm mx-1 ai-assist-btn';
                aiButton.innerHTML = '<i class="fas fa-magic"></i> AI Assist';
                aiButton.onclick = function(e) {
                    e.preventDefault();
                    openAIAssistModal(quillEditor);
                };
                toolbar.appendChild(aiButton);
            }
        });
    }

    // Initialize TinyMCE for other editors
    if (typeof tinymce !== 'undefined') {
        tinymce.init({
            selector: '.tinymce-editor',
            height: 300,
            menubar: true,
            plugins: [
                'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview',
                'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
                'insertdatetime', 'media', 'table', 'help', 'wordcount'
            ],
            toolbar: 'undo redo | formatselect | ' +
                'bold italic backcolor | alignleft aligncenter ' +
                'alignright alignjustify | bullist numlist outdent indent | ' +
                'removeformat | image media link | help'
        });
    }

    // Add Section button functionality
    const addSectionBtn = document.getElementById('addSectionBtn');
    if (!addSectionBtn) {
        console.error('Add Section button not found, creating it');
        const editorContainer = document.querySelector('.page-editor-container');
        if (editorContainer) {
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'editor-actions my-3';
            actionsDiv.innerHTML = `
                <button id="addSectionBtn" class="btn btn-primary">
                    <i class="fas fa-plus-circle"></i> Add Section
                </button>
                <button id="savePageBtn" class="btn btn-success ms-2">
                    <i class="fas fa-save"></i> Save Page
                </button>
            `;
            editorContainer.prepend(actionsDiv);
            
            // Re-get the buttons
            const newAddSectionBtn = document.getElementById('addSectionBtn');
            const newSavePageBtn = document.getElementById('savePageBtn');
            
            if (newAddSectionBtn) {
                newAddSectionBtn.addEventListener('click', addNewSection);
            }
            
            if (newSavePageBtn) {
                newSavePageBtn.addEventListener('click', savePage);
            }
        }
    } else {
        addSectionBtn.addEventListener('click', addNewSection);
    }
    
    // Save Page button functionality
    const savePageBtn = document.getElementById('savePageBtn');
    if (savePageBtn) {
        savePageBtn.addEventListener('click', savePage);
    }
});

/**
 * Add a new section to the page
 */
function addNewSection() {
    const sectionsContainer = document.querySelector('.page-sections-container');
    if (!sectionsContainer) {
        console.error('Sections container not found');
        return;
    }
    
    // Generate a unique ID for the new section
    const sectionId = 'section-' + Date.now();
    
    // Create the section HTML
    const sectionHtml = `
        <div class="card mb-4 page-section" data-section-id="${sectionId}">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0">New Section</h5>
                <div class="section-actions">
                    <button class="btn btn-sm btn-outline-secondary move-up-btn">
                        <i class="fas fa-arrow-up"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-secondary move-down-btn">
                        <i class="fas fa-arrow-down"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger delete-section-btn">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            <div class="card-body">
                <div class="mb-3">
                    <label class="form-label">Section Title</label>
                    <input type="text" class="form-control section-title" placeholder="Section Title">
                </div>
                <div class="mb-3">
                    <label class="form-label">Section Type</label>
                    <select class="form-select section-type">
                        <option value="text">Text</option>
                        <option value="banner">Banner</option>
                        <option value="featured-products">Featured Products</option>
                        <option value="image-gallery">Image Gallery</option>
                    </select>
                </div>
                <div class="section-content">
                    <div class="content-block mb-3">
                        <label class="form-label">Content</label>
                        <div class="content-block-editor" style="height: 200px;"></div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add the section to the container
    sectionsContainer.insertAdjacentHTML('beforeend', sectionHtml);
    
    // Initialize the newly added Quill editor
    const newEditor = document.querySelector(`[data-section-id="${sectionId}"] .content-block-editor`);
    if (newEditor) {
        const quillEditor = new Quill(newEditor, {
            theme: 'snow',
            modules: {
                toolbar: [
                    [{ 'header': [1, 2, 3, false] }],
                    ['bold', 'italic', 'underline', 'strike'],
                    [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                    [{ 'color': [] }, { 'background': [] }],
                    ['link', 'image'],
                    ['clean'],
                    ['ai-assist']
                ]
            }
        });
        
        // Add AI assist button to toolbar
        const toolbar = newEditor.querySelector('.ql-toolbar');
        if (toolbar) {
            const aiButton = document.createElement('button');
            aiButton.className = 'btn btn-primary btn-sm mx-1 ai-assist-btn';
            aiButton.innerHTML = '<i class="fas fa-magic"></i> AI Assist';
            aiButton.onclick = function(e) {
                e.preventDefault();
                openAIAssistModal(quillEditor);
            };
            toolbar.appendChild(aiButton);
        }
    }
    
    // Add event listeners for the new section
    const newSection = document.querySelector(`[data-section-id="${sectionId}"]`);
    if (newSection) {
        newSection.querySelector('.delete-section-btn').addEventListener('click', function() {
            newSection.remove();
        });
        
        newSection.querySelector('.move-up-btn').addEventListener('click', function() {
            const prev = newSection.previousElementSibling;
            if (prev) {
                prev.before(newSection);
            }
        });
        
        newSection.querySelector('.move-down-btn').addEventListener('click', function() {
            const next = newSection.nextElementSibling;
            if (next) {
                next.after(newSection);
            }
        });
    }
}

/**
 * Save the page content
 */
function savePage() {
    const pageId = document.getElementById('pageId')?.value;
    if (!pageId) {
        showAlert('Error: Page ID not found', 'danger');
        return;
    }
    
    // Collect data from all sections
    const sections = [];
    document.querySelectorAll('.page-section').forEach(function(sectionEl, index) {
        const sectionId = sectionEl.getAttribute('data-section-id');
        const title = sectionEl.querySelector('.section-title').value;
        const type = sectionEl.querySelector('.section-type').value;
        
        // Get content based on section type
        let content = {};
        const editorElement = sectionEl.querySelector('.content-block-editor');
        if (editorElement) {
            const quillEditor = Quill.find(editorElement);
            if (quillEditor) {
                content.html = quillEditor.root.innerHTML;
                content.text = quillEditor.getText();
            }
        }
        
        sections.push({
            id: sectionId,
            position: index,
            title: title,
            type: type,
            content: content
        });
    });
    
    // Prepare data for saving
    const pageData = {
        page_id: pageId,
        title: document.getElementById('pageTitle')?.value,
        slug: document.getElementById('pageSlug')?.value,
        sections: sections
    };
    
    // Show saving indicator
    const saveBtn = document.getElementById('savePageBtn');
    const originalText = saveBtn.innerHTML;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    saveBtn.disabled = true;
    
    // Send data to server
    fetch('/admin/api/pages/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(pageData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Server responded with an error');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showAlert('Page saved successfully', 'success');
        } else {
            showAlert('Error saving page: ' + (data.message || 'Unknown error'), 'danger');
        }
    })
    .catch(error => {
        console.error('Error saving page:', error);
        showAlert('Error saving page: ' + error.message, 'danger');
    })
    .finally(() => {
        // Restore button state
        saveBtn.innerHTML = originalText;
        saveBtn.disabled = false;
    });
}

/**
 * Open the AI assistant modal for content generation
 */
function openAIAssistModal(editor) {
    // Create modal if it doesn't exist
    let modal = document.getElementById('aiAssistModal');
    if (!modal) {
        const modalHtml = `
            <div class="modal fade" id="aiAssistModal" tabindex="-1" aria-labelledby="aiAssistModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="aiAssistModalLabel">AI Content Assistant</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <label for="aiPrompt" class="form-label">What would you like the AI to write about?</label>
                                <textarea id="aiPrompt" class="form-control" rows="3" placeholder="Describe what content you want to generate..."></textarea>
                            </div>
                            <div class="mb-3">
                                <label class="form-label d-flex justify-content-between">
                                    <span>Generated Content</span>
                                    <div>
                                        <button id="regenerateBtn" class="btn btn-sm btn-outline-secondary">
                                            <i class="fas fa-sync-alt"></i> Regenerate
                                        </button>
                                    </div>
                                </label>
                                <div id="aiGeneratedContent" class="form-control bg-light" style="height: 200px; overflow-y: auto;"></div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="insertAiContentBtn">Insert Content</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        modal = document.getElementById('aiAssistModal');
        
        // Add event listeners
        document.getElementById('regenerateBtn').addEventListener('click', function() {
            generateAIContent(editor);
        });
        
        document.getElementById('insertAiContentBtn').addEventListener('click', function() {
            const content = document.getElementById('aiGeneratedContent').innerHTML;
            if (content && editor) {
                // Insert at cursor position
                const range = editor.getSelection();
                if (range) {
                    editor.insertText(range.index, '\n');
                    editor.clipboard.dangerouslyPasteHTML(range.index + 1, content);
                } else {
                    editor.clipboard.dangerouslyPasteHTML(editor.getLength(), content);
                }
            }
            
            // Close modal
            const bsModal = bootstrap.Modal.getInstance(modal);
            bsModal.hide();
        });
    }
    
    // Clear previous content
    document.getElementById('aiPrompt').value = '';
    document.getElementById('aiGeneratedContent').innerHTML = '';
    
    // Show modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Focus on prompt input
    setTimeout(() => {
        document.getElementById('aiPrompt').focus();
    }, 500);
}

/**
 * Generate content using AI
 */
function generateAIContent() {
    const prompt = document.getElementById('aiPrompt').value;
    const outputElement = document.getElementById('aiGeneratedContent');
    
    if (!prompt) {
        outputElement.innerHTML = '<div class="text-danger">Please enter a prompt</div>';
        return;
    }
    
    // Show loading
    outputElement.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Generating content...</p>
        </div>
    `;
    
    // Call AI generation API
    fetch('/admin/api/ai/generate-content', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: prompt })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('AI service unavailable');
        }
        return response.json();
    })
    .then(data => {
        if (data.content) {
            outputElement.innerHTML = data.content;
        } else {
            outputElement.innerHTML = '<div class="text-danger">Failed to generate content</div>';
        }
    })
    .catch(error => {
        console.error('Error generating content:', error);
        outputElement.innerHTML = `<div class="text-danger">Error: ${error.message}</div>`;
    });
}

/**
 * Show an alert message
 */
function showAlert(message, type = 'info') {
    const alertsContainer = document.getElementById('alertsContainer');
    if (!alertsContainer) {
        // Create alerts container if it doesn't exist
        const container = document.createElement('div');
        container.id = 'alertsContainer';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '5000';
        document.body.appendChild(container);
    }
    
    const alertId = 'alert-' + Date.now();
    const alertHtml = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    document.getElementById('alertsContainer').insertAdjacentHTML('beforeend', alertHtml);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alertElement = document.getElementById(alertId);
        if (alertElement) {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alertElement);
            bsAlert.close();
        }
    }, 5000);
}
