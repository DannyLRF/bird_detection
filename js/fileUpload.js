// File upload related functionality

// Initialize upload area
document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    // Drag and drop functionality
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    
    // File selection
    fileInput.addEventListener('change', handleFileSelect);
});

function handleDragOver(e) {
    e.preventDefault();
    document.getElementById('uploadArea').classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    document.getElementById('uploadArea').classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    document.getElementById('uploadArea').classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    handleFiles(files);
}

function handleFileSelect(e) {
    const files = e.target.files;
    handleFiles(files);
}

function handleFiles(files) {
    if (files.length === 0) return;
    
    // Validate files
    const validFiles = Array.from(files).filter(validateFile);
    
    if (validFiles.length === 0) {
        showToast(MESSAGES.upload.noValidFiles, 'warning');
        return;
    }
    
    // Upload files
    uploadFiles(validFiles);
}

function validateFile(file) {
    // Check file size
    if (file.size > MAX_FILE_SIZE) {
        showToast(MESSAGES.upload.fileSizeExceeded.replace('{fileName}', file.name), 'error');
        return false;
    }
    
    // Check file type
    const allSupportedTypes = [
        ...SUPPORTED_FILE_TYPES.images,
        ...SUPPORTED_FILE_TYPES.videos,
        ...SUPPORTED_FILE_TYPES.audio
    ];
    
    if (!allSupportedTypes.includes(file.type)) {
        showToast(MESSAGES.upload.unsupportedFileType.replace('{fileName}', file.name), 'error');
        return false;
    }
    
    return true;
}

async function uploadFiles(files) {
    showUploadProgress();
    
    const results = [];
    let completedUploads = 0;
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        try {
            updateProgress((i / files.length) * 50, `Uploading ${file.name}...`);
            
            // Upload to S3
            const uploadResult = await uploadToS3(file);
            
            updateProgress(50 + ((i + 1) / files.length) * 50, `Processing ${file.name}...`);
            
            // Trigger Lambda processing
            const processResult = await triggerFileProcessing(uploadResult.url, file.type);
            
            results.push({
                file: file,
                url: uploadResult.url,
                thumbnailUrl: processResult.thumbnailUrl,
                tags: processResult.tags
            });
            
            completedUploads++;
            
        } catch (error) {
            console.error('Upload error:', error);
            showToast(MESSAGES.upload.uploadFailed
                .replace('{fileName}', file.name)
                .replace('{error}', error.message), 'error');
        }
    }
    
    hideUploadProgress();
    displayUploadResults(results);
    
    if (completedUploads > 0) {
        showToast(MESSAGES.upload.uploadSuccess.replace('{count}', completedUploads), 'success');
    }
}

async function uploadToS3(file) {
    return new Promise((resolve, reject) => {
        // Ensure AWS credentials are set
        if (!AWS.config.credentials) {
            reject(new Error('AWS credentials not set'));
            return;
        }
        
        const s3 = new AWS.S3({
            region: AWS_CONFIG.s3.region
        });
        
        const fileName = `${Date.now()}-${file.name}`;
        const uploadParams = {
            Bucket: AWS_CONFIG.s3.bucketName,
            Key: fileName,
            Body: file,
            ContentType: file.type,
            Metadata: {
                'uploaded-by': 'bird-tagging-app',
                'upload-timestamp': new Date().toISOString()
            }
        };
        
        s3.upload(uploadParams)
            .on('httpUploadProgress', function(evt) {
                const progress = Math.round((evt.loaded / evt.total) * 100);
                console.log(`Upload progress: ${progress}%`);
            })
            .send(function(err, data) {
                if (err) {
                    reject(err);
                } else {
                    resolve({
                        url: data.Location,
                        key: data.Key
                    });
                }
            });
    });
}

async function triggerFileProcessing(fileUrl, fileType) {
    try {
        const token = await getCurrentUserToken();
        
        const response = await fetch(`${AWS_CONFIG.apiGateway.baseUrl}${API_ENDPOINTS.upload}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                fileUrl: fileUrl,
                fileType: fileType
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        return result;
        
    } catch (error) {
        console.error('File processing error:', error);
        throw error;
    }
}

function showUploadProgress() {
    document.getElementById('uploadProgress').style.display = 'block';
}

function hideUploadProgress() {
    document.getElementById('uploadProgress').style.display = 'none';
}

function updateProgress(percentage, text) {
    document.getElementById('progressFill').style.width = `${percentage}%`;
    document.getElementById('progressText').textContent = `${Math.round(percentage)}% - ${text}`;
}

function displayUploadResults(results) {
    const resultsContainer = document.getElementById('uploadResults');
    resultsContainer.innerHTML = '';
    
    if (results.length === 0) {
        resultsContainer.innerHTML = '<p>No files uploaded successfully</p>';
        return;
    }
    
    results.forEach(result => {
        const resultItem = createUploadResultItem(result);
        resultsContainer.appendChild(resultItem);
    });
}

function createUploadResultItem(result) {
    const item = document.createElement('div');
    item.className = 'upload-result-item';
    
    const isImage = SUPPORTED_FILE_TYPES.images.includes(result.file.type);
    const displayUrl = isImage ? (result.thumbnailUrl || result.url) : result.url;
    
    item.innerHTML = `
        ${isImage ? `<img src="${displayUrl}" alt="Uploaded file">` : 
          `<div class="file-icon"><i class="fas fa-file"></i></div>`}
        <div class="upload-result-info">
            <h4>${result.file.name}</h4>
            <p>File size: ${formatFileSize(result.file.size)}</p>
            <p>Upload time: ${new Date().toLocaleString()}</p>
            <div class="upload-result-tags">
                ${result.tags ? result.tags.map(tag => 
                    `<span class="tag">${tag.species}: ${tag.count}</span>`
                ).join('') : '<span class="tag">Processing...</span>'}
            </div>
            <div class="upload-result-actions">
                <button onclick="copyToClipboard('${result.url}')" class="btn btn-small">
                    <i class="fas fa-copy"></i> Copy Link
                </button>
                ${isImage ? 
                    `<button onclick="viewFullImage('${result.url}')" class="btn btn-small">
                        <i class="fas fa-eye"></i> View Full Image
                    </button>` : ''
                }
            </div>
        </div>
    `;
    
    return item;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast(MESSAGES.upload.linkCopied, 'success');
    }).catch(err => {
        console.error('Copy failed:', err);
        showToast(MESSAGES.upload.copyFailed, 'error');
    });
}

function viewFullImage(url) {
    window.open(url, '_blank');
}