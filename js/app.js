// js/app.js - Main Application Logic

// Show different sections
function showSection(sectionName) {
    // Hide all sections
    const sections = document.querySelectorAll('.section');
    sections.forEach(s => s.style.display = 'none');
    
    // Show specified section
    document.getElementById(sectionName + 'Section').style.display = 'block';
    
    // Update navigation state
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Find and activate the correct nav link
    const activeLink = document.querySelector(`[onclick="showSection('${sectionName}')"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
}

// File upload handling
document.getElementById('fileInput').addEventListener('change', function(e) {
    const files = e.target.files;
    if (files.length === 0) return;
    
    uploadFiles(files);
});

// Drag and drop functionality
const uploadArea = document.querySelector('.upload-area');

uploadArea.addEventListener('dragover', function(e) {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', function(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', function(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        uploadFiles(files);
    }
});

// Upload files function
async function uploadFiles(files) {
    const resultsDiv = document.getElementById('uploadResults');
    const progressDiv = document.getElementById('uploadProgress');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    
    // Show progress
    progressDiv.style.display = 'block';
    resultsDiv.innerHTML = '';
    
    try {
        let uploadedCount = 0;
        let html = '<h3>Upload Results:</h3>';
        
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            
            // Update progress
            const progress = (i / files.length) * 100;
            progressBar.style.width = progress + '%';
            progressText.textContent = `Processing ${file.name}...`;
            
            if (ALL_SUPPORTED_TYPES.includes(file.type)) {
                // Simulate upload and processing
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                const mockResult = await simulateFileProcessing(file);
                
                html += `
                    <div class="upload-result-item">
                        <div class="file-info">
                            <i class="fas ${getFileIcon(file.type)}"></i>
                            <div class="file-details">
                                <h4>${file.name}</h4>
                                <p>Size: ${formatFileSize(file.size)}</p>
                                <p>Type: ${file.type}</p>
                                <div class="upload-result-tags">
                                    ${mockResult.tags.map(tag => 
                                        `<span class="tag">${tag.species} (${(tag.confidence * 100).toFixed(1)}%)</span>`
                                    ).join('')}
                                </div>
                            </div>
                        </div>
                        <div class="upload-result-actions">
                            <button class="btn btn-small" onclick="viewFile('${mockResult.url}')">
                                <i class="fas fa-eye"></i> View
                            </button>
                            <button class="btn btn-small" onclick="shareFile('${mockResult.url}')">
                                <i class="fas fa-share"></i> Share
                            </button>
                        </div>
                    </div>
                `;
                uploadedCount++;
            } else {
                html += `
                    <div class="upload-result-item error">
                        <i class="fas fa-exclamation-triangle"></i>
                        <span>${file.name} - Unsupported file type</span>
                    </div>
                `;
            }
        }
        
        // Complete progress
        progressBar.style.width = '100%';
        progressText.textContent = 'Upload complete!';
        
        setTimeout(() => {
            progressDiv.style.display = 'none';
        }, 2000);
        
        resultsDiv.innerHTML = html;
        
        if (uploadedCount > 0) {
            showToast(`Successfully uploaded ${uploadedCount} file(s)!`, 'success');
        }
        
    } catch (error) {
        console.error('Upload error:', error);
        progressDiv.style.display = 'none';
        showToast('Upload failed: ' + error.message, 'error');
    }
}

// Simulate file processing (for demo purposes)
async function simulateFileProcessing(file) {
    // Mock AI detection results
    const mockSpecies = ['Crow', 'Pigeon', 'Sparrow', 'Robin', 'Eagle', 'Owl'];
    const randomSpecies = mockSpecies[Math.floor(Math.random() * mockSpecies.length)];
    
    return {
        url: URL.createObjectURL(file),
        thumbnailUrl: URL.createObjectURL(file),
        tags: [
            {
                species: randomSpecies,
                confidence: 0.85 + Math.random() * 0.15,
                count: Math.floor(Math.random() * 3) + 1
            }
        ]
    };
}

// Search functionality
async function searchFiles() {
    const query = document.getElementById('searchInput').value.trim();
    if (!query) {
        showToast('Please enter a search term', 'warning');
        return;
    }
    
    const resultsDiv = document.getElementById('searchResults');
    resultsDiv.innerHTML = '<div class="searching"><i class="fas fa-spinner fa-spin"></i> Searching...</div>';
    
    try {
        // Simulate search delay
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        // Mock search results
        const mockResults = generateMockSearchResults(query);
        
        displaySearchResults(mockResults, query);
        
    } catch (error) {
        console.error('Search error:', error);
        showToast('Search failed: ' + error.message, 'error');
    }
}

// Advanced search
async function advancedSearch() {
    const fileType = document.getElementById('fileTypeFilter').value;
    const confidence = document.getElementById('confidenceFilter').value;
    
    const resultsDiv = document.getElementById('searchResults');
    resultsDiv.innerHTML = '<div class="searching"><i class="fas fa-spinner fa-spin"></i> Filtering...</div>';
    
    try {
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const mockResults = generateMockSearchResults('', fileType, confidence);
        displaySearchResults(mockResults, 'Advanced Filter');
        
    } catch (error) {
        console.error('Search error:', error);
        showToast('Search failed: ' + error.message, 'error');
    }
}

// Generate mock search results
function generateMockSearchResults(query, fileType = '', confidence = '') {
    const mockFiles = [
        { name: 'crow_photo_1.jpg', species: 'Crow', confidence: 0.95, type: 'image' },
        { name: 'pigeon_video.mp4', species: 'Pigeon', confidence: 0.87, type: 'video' },
        { name: 'sparrow_audio.wav', species: 'Sparrow', confidence: 0.92, type: 'audio' },
        { name: 'robin_nest.jpg', species: 'Robin', confidence: 0.78, type: 'image' },
        { name: 'eagle_flight.mp4', species: 'Eagle', confidence: 0.89, type: 'video' },
        { name: 'owl_hoot.wav', species: 'Owl', confidence: 0.94, type: 'audio' }
    ];
    
    let results = mockFiles;
    
    // Filter by query
    if (query) {
        results = results.filter(item => 
            item.species.toLowerCase().includes(query.toLowerCase()) ||
            item.name.toLowerCase().includes(query.toLowerCase())
        );
    }
    
    // Filter by file type
    if (fileType) {
        results = results.filter(item => item.type === fileType);
    }
    
    // Filter by confidence
    if (confidence) {
        const minConfidence = parseFloat(confidence);
        results = results.filter(item => item.confidence >= minConfidence);
    }
    
    return results;
}

// Display search results
function displaySearchResults(results, searchTerm) {
    const resultsDiv = document.getElementById('searchResults');
    
    if (results.length === 0) {
        resultsDiv.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search"></i>
                <h3>No results found</h3>
                <p>No files found matching "${searchTerm}"</p>
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="results-header">
            <h3>Search Results</h3>
            <p>Found ${results.length} file(s) matching "${searchTerm}"</p>
        </div>
        <div class="results-grid">
    `;
    
    results.forEach(result => {
        html += `
            <div class="result-item">
                <div class="file-placeholder">
                    <i class="fas ${getFileIcon(result.type)}"></i>
                    <p>${result.name}</p>
                </div>
                <div class="result-item-info">
                    <h4>${result.species}</h4>
                    <p>Confidence: ${(result.confidence * 100).toFixed(1)}%</p>
                    <p>Type: ${result.type}</p>
                    <div class="result-actions">
                        <button class="btn btn-small" onclick="viewFile('${result.name}')">
                            <i class="fas fa-eye"></i> View
                        </button>
                        <button class="btn btn-small" onclick="downloadFile('${result.name}')">
                            <i class="fas fa-download"></i> Download
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    resultsDiv.innerHTML = html;
}

// Bulk tag management
async function manageBulkTags() {
    const urls = document.getElementById('bulkUrls').value.trim().split('\n').filter(url => url.trim());
    const tags = document.getElementById('bulkTags').value.trim().split(',').map(tag => tag.trim()).filter(tag => tag);
    const operation = document.getElementById('bulkOperation').value;
    
    if (urls.length === 0) {
        showToast('Please enter at least one file URL', 'warning');
        return;
    }
    
    if (tags.length === 0) {
        showToast('Please enter at least one tag', 'warning');
        return;
    }
    
    try {
        showToast('Processing bulk tag operation...', 'info');
        
        // Simulate processing
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        const operationText = operation === '1' ? 'added to' : 'removed from';
        showToast(`Tags successfully ${operationText} ${urls.length} file(s)!`, 'success');
        
        // Clear form
        document.getElementById('bulkUrls').value = '';
        document.getElementById('bulkTags').value = '';
        
    } catch (error) {
        console.error('Bulk tag error:', error);
        showToast('Bulk tag operation failed: ' + error.message, 'error');
    }
}

// Utility functions
function getFileIcon(fileType) {
    if (typeof fileType === 'string') {
        if (fileType.startsWith('image/') || fileType === 'image') return 'fa-image';
        if (fileType.startsWith('video/') || fileType === 'video') return 'fa-video';
        if (fileType.startsWith('audio/') || fileType === 'audio') return 'fa-music';
    }
    return 'fa-file';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function viewFile(url) {
    window.open(url, '_blank');
}

function shareFile(url) {
    if (navigator.share) {
        navigator.share({
            title: 'Bird Detection Result',
            url: url
        });
    } else {
        // Fallback - copy to clipboard
        navigator.clipboard.writeText(url).then(() => {
            showToast('Link copied to clipboard!', 'success');
        });
    }
}

function downloadFile(filename) {
    showToast(`Downloading ${filename}...`, 'info');
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Initialize drag and drop styling
document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.querySelector('.upload-area');
    
    if (uploadArea) {
        uploadArea.addEventListener('dragenter', function(e) {
            e.preventDefault();
            this.style.borderColor = '#667eea';
            this.style.backgroundColor = '#f0f4ff';
        });
        
        uploadArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.style.borderColor = '#ddd';
            this.style.backgroundColor = 'white';
        });
    }
});