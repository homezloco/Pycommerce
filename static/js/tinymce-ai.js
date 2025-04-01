/**
 * TinyMCE AI Integration for PyCommerce
 *
 * This file provides integration between TinyMCE editor and our OpenAI-powered 
 * content generation API.
 */

// Initialize AI features for TinyMCE
function initTinyMCEWithAI(selector, options = {}) {
  const apiKey = document.querySelector('meta[name="tinymce-api-key"]')?.content || '';
  if (!apiKey) {
    console.error('TinyMCE API key not found.');
    return;
  }

  // Merge default options with user options
  const defaultOptions = {
    height: 400,
    menubar: true,
    plugins: [
      'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview',
      'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
      'insertdatetime', 'media', 'table', 'help', 'wordcount'
    ],
    toolbar: 'undo redo | formatselect | ' +
      'bold italic backcolor | alignleft aligncenter ' +
      'alignright alignjustify | bullist numlist outdent indent | ' +
      'removeformat | help | ai_generate ai_enhance',
    content_style: 'body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 14px; }',
    setup: function (editor) {
      // Add AI Generate button
      editor.ui.registry.addButton('ai_generate', {
        text: 'AI Generate',
        icon: 'comment',
        tooltip: 'Generate content with AI',
        onAction: function () {
          // Open dialog for AI content generation
          editor.windowManager.open({
            title: 'Generate Content with AI',
            body: {
              type: 'panel',
              items: [
                {
                  type: 'textarea',
                  name: 'prompt',
                  label: 'Describe what you want to generate',
                  placeholder: 'e.g., Write a product description for a premium wireless headphones with noise cancellation'
                }
              ]
            },
            buttons: [
              {
                type: 'cancel',
                text: 'Cancel'
              },
              {
                type: 'submit',
                text: 'Generate',
                primary: true
              }
            ],
            onSubmit: function (api) {
              const data = api.getData();
              
              // Show loading indicator
              editor.setProgressState(true);
              
              // Call our API to generate content
              fetch('/api/ai/generate', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify({ prompt: data.prompt })
              })
              .then(response => {
                if (!response.ok) {
                  throw new Error('Error generating content: ' + response.statusText);
                }
                return response.json();
              })
              .then(data => {
                editor.setProgressState(false);
                if (data && data.content) {
                  // Insert the generated content at the cursor position
                  editor.insertContent(data.content);
                  editor.notificationManager.open({
                    text: 'Content generated successfully!',
                    type: 'success',
                    timeout: 3000
                  });
                }
                api.close();
              })
              .catch(error => {
                editor.setProgressState(false);
                editor.notificationManager.open({
                  text: error.message || 'Error generating content',
                  type: 'error',
                  timeout: 3000
                });
                api.close();
              });
            }
          });
        }
      });
      
      // Add AI Enhance button
      editor.ui.registry.addButton('ai_enhance', {
        text: 'AI Enhance',
        icon: 'edit-block',
        tooltip: 'Enhance selected text with AI',
        onAction: function () {
          const selectedText = editor.selection.getContent({ format: 'text' });
          
          if (!selectedText) {
            editor.notificationManager.open({
              text: 'Please select some text to enhance',
              type: 'warning',
              timeout: 3000
            });
            return;
          }
          
          // Open dialog for AI content enhancement
          editor.windowManager.open({
            title: 'Enhance Content with AI',
            body: {
              type: 'panel',
              items: [
                {
                  type: 'textarea',
                  name: 'text',
                  label: 'Text to enhance',
                  placeholder: selectedText
                },
                {
                  type: 'input',
                  name: 'instructions',
                  label: 'Instructions (optional)',
                  placeholder: 'e.g., Make it more engaging or Add more details about features'
                }
              ]
            },
            buttons: [
              {
                type: 'cancel',
                text: 'Cancel'
              },
              {
                type: 'submit',
                text: 'Enhance',
                primary: true
              }
            ],
            initialData: {
              text: selectedText
            },
            onSubmit: function (api) {
              const data = api.getData();
              
              // Show loading indicator
              editor.setProgressState(true);
              
              // Call our API to enhance content
              fetch('/api/ai/enhance', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                  text: data.text,
                  instructions: data.instructions 
                })
              })
              .then(response => {
                if (!response.ok) {
                  throw new Error('Error enhancing content: ' + response.statusText);
                }
                return response.json();
              })
              .then(data => {
                editor.setProgressState(false);
                if (data && data.content) {
                  // Replace the selected content with the enhanced content
                  editor.selection.setContent(data.content);
                  editor.notificationManager.open({
                    text: 'Content enhanced successfully!',
                    type: 'success',
                    timeout: 3000
                  });
                }
                api.close();
              })
              .catch(error => {
                editor.setProgressState(false);
                editor.notificationManager.open({
                  text: error.message || 'Error enhancing content',
                  type: 'error',
                  timeout: 3000
                });
                api.close();
              });
            }
          });
        }
      });
    }
  };
  
  const mergedOptions = {...defaultOptions, ...options, api_key: apiKey};
  
  // Initialize TinyMCE
  tinymce.init({
    selector: selector,
    ...mergedOptions
  });
}