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
                
                // Show the modal
                modal.style.display = 'block';
                
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
                        
                        // Close modal
                        modal.style.display = 'none';
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
                    modal.style.display = 'none';
                    promptInput.value = '';
                    generateBtn.onclick = oldClickHandler;
                };
                
                // Close modal when user clicks cancel or X
                modal.querySelector('.btn-secondary').onclick = closeModal;
                modal.querySelector('.btn-close').onclick = closeModal;
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
                    padding: 5px 10px;
                    margin-left: 5px;
                    font-size: 12px;
                    cursor: pointer;
                }
                .ql-ai-generate:hover, .ql-ai-enhance:hover {
                    background-color: #5649c9;
                }
            `;
            document.head.appendChild(style);
        }
    });
});