"""
Simple Flask application for testing media integration.
"""
import logging
import os
from flask import Flask, request, jsonify, render_template_string

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "pycommerce-secret-key")

# Sample media data for testing
SAMPLE_MEDIA = [
    {
        "id": "1",
        "name": "Product Image 1",
        "url": "https://placehold.co/600x400?text=Product+1",
        "size": 24500,
        "mime_type": "image/jpeg",
        "tenant_id": "tech",
        "sharing_level": "tenant",
        "created_at": "2025-04-23T10:00:00Z",
        "updated_at": "2025-04-23T10:00:00Z"
    },
    {
        "id": "2",
        "name": "Product Image 2",
        "url": "https://placehold.co/600x400?text=Product+2",
        "size": 22800,
        "mime_type": "image/jpeg",
        "tenant_id": "tech",
        "sharing_level": "tenant",
        "created_at": "2025-04-23T10:01:00Z",
        "updated_at": "2025-04-23T10:01:00Z"
    },
    {
        "id": "3",
        "name": "Product Image 3",
        "url": "https://placehold.co/600x400?text=Product+3",
        "size": 30100,
        "mime_type": "image/jpeg",
        "tenant_id": "outdoor",
        "sharing_level": "tenant",
        "created_at": "2025-04-23T10:02:00Z",
        "updated_at": "2025-04-23T10:02:00Z"
    },
    {
        "id": "4",
        "name": "Shared Product Image",
        "url": "https://placehold.co/600x400?text=Shared+Product",
        "size": 28700,
        "mime_type": "image/jpeg",
        "tenant_id": None,
        "sharing_level": "global",
        "created_at": "2025-04-23T10:03:00Z",
        "updated_at": "2025-04-23T10:03:00Z"
    }
]

# API routes for media
@app.route('/api/media', methods=['GET'])
def get_media_list():
    """Get a list of media items."""
    tenant_id = request.args.get('tenant_id')
    sharing_level = request.args.get('sharing_level')
    
    # Filter by tenant_id and sharing_level if provided
    filtered_media = SAMPLE_MEDIA
    if tenant_id:
        filtered_media = [m for m in filtered_media if m['tenant_id'] == tenant_id or m['sharing_level'] == 'global']
    if sharing_level:
        filtered_media = [m for m in filtered_media if m['sharing_level'] == sharing_level]
    
    return jsonify({
        "items": filtered_media,
        "count": len(filtered_media),
        "page": 1,
        "limit": 100
    })

@app.route('/api/media/<id>', methods=['GET'])
def get_media_item(id):
    """Get a media item by ID."""
    for item in SAMPLE_MEDIA:
        if item['id'] == id:
            return jsonify(item)
    
    return jsonify({"error": f"Media item with ID {id} not found"}), 404

# HTML template for the test interface
@app.route('/')
def index():
    """Test page for media library integration."""
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Media Library Test</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .media-item {
                cursor: pointer;
                transition: transform 0.2s;
            }
            .media-item:hover {
                transform: scale(1.05);
            }
            #preview {
                max-height: 200px;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container py-4">
            <h1>Media Library Test</h1>
            
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="input-group">
                        <input type="text" class="form-control" id="imageUrlInput" placeholder="Selected image URL">
                        <button class="btn btn-primary" id="openMediaBtn">Open Media Library</button>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Selected Image Preview</div>
                        <div class="card-body text-center">
                            <img id="preview" src="" class="img-fluid d-none" alt="Preview">
                            <p id="noImageMessage">No image selected</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Media Library Modal -->
            <div class="modal fade" id="mediaModal" tabindex="-1" aria-labelledby="mediaModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="mediaModalLabel">Media Library</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div id="mediaLoading" class="text-center py-4">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <p class="mt-2">Loading media...</p>
                            </div>
                            <div id="mediaError" class="alert alert-danger d-none">
                                Error loading media. Please try again.
                            </div>
                            <div id="mediaItems" class="row"></div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const imageUrlInput = document.getElementById('imageUrlInput');
                const preview = document.getElementById('preview');
                const noImageMessage = document.getElementById('noImageMessage');
                const openMediaBtn = document.getElementById('openMediaBtn');
                const mediaModal = document.getElementById('mediaModal');
                const mediaLoading = document.getElementById('mediaLoading');
                const mediaError = document.getElementById('mediaError');
                const mediaItems = document.getElementById('mediaItems');
                
                // Create Bootstrap modal instance
                const modalInstance = new bootstrap.Modal(mediaModal);
                
                // Update preview when URL changes
                imageUrlInput.addEventListener('input', updatePreview);
                
                // Open modal when button is clicked
                openMediaBtn.addEventListener('click', function() {
                    loadMediaLibrary();
                    modalInstance.show();
                });
                
                // Function to update preview
                function updatePreview() {
                    const url = imageUrlInput.value.trim();
                    if (url) {
                        preview.src = url;
                        preview.classList.remove('d-none');
                        noImageMessage.classList.add('d-none');
                    } else {
                        preview.classList.add('d-none');
                        noImageMessage.classList.remove('d-none');
                    }
                }
                
                // Function to load media library
                function loadMediaLibrary() {
                    // Show loading state
                    mediaLoading.classList.remove('d-none');
                    mediaError.classList.add('d-none');
                    mediaItems.innerHTML = '';
                    
                    // Make API request to get media items
                    fetch('/api/media')
                        .then(response => {
                            if (!response.ok) {
                                throw new Error('Network response was not ok');
                            }
                            return response.json();
                        })
                        .then(data => {
                            mediaLoading.classList.add('d-none');
                            
                            if (data && data.items && data.items.length > 0) {
                                data.items.forEach(item => {
                                    const col = document.createElement('div');
                                    col.className = 'col-md-4 mb-3';
                                    col.innerHTML = `
                                        <div class="card h-100 media-item" data-url="${item.url}">
                                            <img src="${item.url}" class="card-img-top" alt="${item.name}" style="height: 150px; object-fit: cover;">
                                            <div class="card-body">
                                                <h6 class="card-title text-truncate">${item.name}</h6>
                                            </div>
                                        </div>
                                    `;
                                    mediaItems.appendChild(col);
                                    
                                    // Add click event to select the image
                                    col.querySelector('.media-item').addEventListener('click', function() {
                                        const url = this.getAttribute('data-url');
                                        imageUrlInput.value = url;
                                        updatePreview();
                                        modalInstance.hide();
                                    });
                                });
                            } else {
                                mediaItems.innerHTML = '<div class="col-12"><div class="alert alert-info">No media found</div></div>';
                            }
                        })
                        .catch(error => {
                            console.error('Error loading media:', error);
                            mediaLoading.classList.add('d-none');
                            mediaError.classList.remove('d-none');
                        });
                }
                
                // Initialize preview
                updatePreview();
            });
        </script>
    </body>
    </html>
    """)

# Run the application
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7000))  # Use port 7000 to avoid conflicts
    app.run(host='0.0.0.0', port=port, debug=True)