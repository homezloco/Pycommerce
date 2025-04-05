/**
 * Quill.js integration for PyCommerce with AI capabilities
 * 
 * This script initializes Quill.js WYSIWYG editors for textareas with the 'quill-editor' class
 * and adds AI content generation and enhancement capabilities.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Find all elements with class 'quill-editor'
    const editorElements = document.querySelectorAll('.quill-editor');
    
    // Configure Quill toolbar
    const toolbarOptions = [
        ['bold', 'italic', 'underline', 'strike'],
        ['blockquote', 'code-block'],
        [{ 'header': 1 }, { 'header': 2 }],
        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
        [{ 'script': 'sub'}, { 'script': 'super' }],
        [{ 'indent': '-1'}, { 'indent': '+1' }],
        [{ 'direction': 'rtl' }],
        [{ 'size': ['small', false, 'large', 'huge'] }],
        [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
        [{ 'color': [] }, { 'background': [] }],
        [{ 'font': [] }],
        [{ 'align': [] }],
        ['clean'],
        ['link', 'image', 'video']
    ];
    
    // Initialize Quill for each editor element
    editorElements.forEach(function(editorElement) {
        // Create a container for the Quill editor
        const quillContainer = document.createElement('div');
        quillContainer.classList.add('quill-container');
        editorElement.parentNode.insertBefore(quillContainer, editorElement);
        
        // Hide the original textarea
        editorElement.style.display = 'none';
        
        // Get the form that contains this editor
        const form = editorElement.closest('form');
        
        // Initialize Quill
        const quill = new Quill(quillContainer, {
            modules: {
                toolbar: {
                    container: toolbarOptions,
                    handlers: {
                        // Custom handlers will be added after initialization
                    }
                }
            },
            theme: 'snow'
        });
        
        // Apply custom styling to the toolbar
        const toolbarElement = quillContainer.querySelector('.ql-toolbar');
        if (toolbarElement) {
            toolbarElement.style.display = 'flex';
            toolbarElement.style.flexWrap = 'wrap';
            toolbarElement.style.alignItems = 'center';
            toolbarElement.style.justifyContent = 'flex-start';
        }
        
        // If there's initial content in the textarea, load it into Quill
        quill.root.innerHTML = editorElement.value;
        
        // When the form is submitted, update the textarea with Quill content
        if (form) {
            form.addEventListener('submit', function() {
                editorElement.value = quill.root.innerHTML;
            });
        }
        
        // Add AI buttons to the toolbar
        const toolbar = quillContainer.querySelector('.ql-toolbar');
        if (toolbar) {
            // Add spacer between regular toolbar and AI buttons
            const spacer = document.createElement('span');
            spacer.className = 'ql-toolbar-spacer';
            spacer.style.flex = '1';
            toolbar.appendChild(spacer);
            
            // Create AI Generate button
            const aiGenerateBtn = document.createElement('button');
            aiGenerateBtn.className = 'ql-ai-generate';
            aiGenerateBtn.innerHTML = 'AI Generate';
            aiGenerateBtn.title = 'Generate content with AI';
            toolbar.appendChild(aiGenerateBtn);
            
            // Create AI Enhance button
            const aiEnhanceBtn = document.createElement('button');
            aiEnhanceBtn.className = 'ql-ai-enhance';
            aiEnhanceBtn.innerHTML = 'AI Enhance';
            aiEnhanceBtn.title = 'Enhance selected text with AI';
            toolbar.appendChild(aiEnhanceBtn);
            
            // Add click handler for AI Generate button
            aiGenerateBtn.addEventListener('click', function() {
                const modal = document.getElementById('aiModal');
                const promptInput = document.getElementById('aiPromptInput');
                const generateBtn = document.getElementById('aiGenerateBtn');
                
                // Show the modal using Bootstrap
                const bootstrapModal = bootstrap.Modal.getOrCreateInstance(modal);
                bootstrapModal.show();
                
                // Setup the generate button
                const oldClickHandler = generateBtn.onclick;
                generateBtn.onclick = function() {
                    const prompt = promptInput.value.trim();
                    if (!prompt) return;
                    
                    // Show loading
                    document.getElementById('aiModalLoading').style.display = 'block';
                    
                    // Call API to generate content
                    fetch('/api/ai/generate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ prompt: prompt })
                    })
                    .then(response => response.json())
                    .then(data => {
                        // Hide loading
                        document.getElementById('aiModalLoading').style.display = 'none';
                        
                        // Insert generated content at cursor position
                        const range = quill.getSelection();
                        if (range) {
                            quill.insertText(range.index, data.content);
                        } else {
                            quill.insertText(quill.getLength(), data.content);
                        }
                        
                        // Close modal using Bootstrap
                        const bootstrapModal = bootstrap.Modal.getInstance(modal);
                        if (bootstrapModal) {
                            bootstrapModal.hide();
                        }
                        promptInput.value = '';
                    })
                    .catch(error => {
                        console.error('Error generating content:', error);
                        document.getElementById('aiModalLoading').style.display = 'none';
                        alert('Error generating content. Please try again.');
                    });
                };
                
                // Reset input on modal close
                const closeModal = function() {
                    const bootstrapModal = bootstrap.Modal.getInstance(modal);
                    if (bootstrapModal) {
                        bootstrapModal.hide();
                    }
                    promptInput.value = '';
                    generateBtn.onclick = oldClickHandler;
                };
                
                // Close modal when user clicks cancel or X
                modal.querySelector('.btn-secondary').onclick = closeModal;
                modal.querySelector('.btn-close').onclick = closeModal;
                
                // Event listener for when the modal is hidden
                modal.addEventListener('hidden.bs.modal', function() {
                    promptInput.value = '';
                    generateBtn.onclick = oldClickHandler;
                });
            });
            
            // Add click handler for AI Enhance button
            aiEnhanceBtn.addEventListener('click', function() {
                const range = quill.getSelection();
                if (!range || range.length === 0) {
                    alert('Please select text to enhance.');
                    return;
                }
                
                const selectedText = quill.getText(range.index, range.length);
                if (!selectedText.trim()) {
                    alert('Selected text is empty. Please select text to enhance.');
                    return;
                }
                
                // Show a loading placeholder
                quill.deleteText(range.index, range.length);
                quill.insertText(range.index, 'Enhancing with AI...', {
                    'color': '#0dcaf0',
                    'background': '#212529',
                    'italic': true
                });
                
                // Call API to enhance content
                fetch('/api/ai/enhance', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        text: selectedText,
                        instructions: 'Improve this text by making it more engaging and professional.'
                    })
                })
                .then(response => response.json())
                .then(data => {
                    // Replace placeholder with enhanced content
                    quill.deleteText(range.index, 'Enhancing with AI...'.length);
                    quill.insertText(range.index, data.content);
                })
                .catch(error => {
                    console.error('Error enhancing content:', error);
                    // Restore original text
                    quill.deleteText(range.index, 'Enhancing with AI...'.length);
                    quill.insertText(range.index, selectedText);
                    alert('Error enhancing content. Please try again.');
                });
            });
            
            // Add some styling for the AI buttons
            const style = document.createElement('style');
            style.textContent = `
                .ql-ai-generate, .ql-ai-enhance {
                    background-color: #6c5ce7;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 12px;
                    margin-left: 8px;
                    font-size: 14px;
                    font-weight: bold;
                    cursor: pointer;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    min-width: 100px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                }
                .ql-ai-generate::before, .ql-ai-enhance::before {
                    content: "✨";
                    margin-right: 6px;
                    font-size: 16px;
                }
                .ql-ai-generate:hover, .ql-ai-enhance:hover {
                    background-color: #5649c9;
                    box-shadow: 0 3px 6px rgba(0,0,0,0.3);
                    transform: translateY(-1px);
                    transition: all 0.2s ease;
                }
            `;
            document.head.appendChild(style);
        }
    });
});