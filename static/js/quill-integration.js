/**
 * Quill.js integration for PyCommerce
 * 
 * This script initializes Quill.js WYSIWYG editors for textareas with the 'quill-editor' class.
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
                toolbar: toolbarOptions
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
    });
});