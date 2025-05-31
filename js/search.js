// Search functionality

// Add new tag input for search
function addTagInput() {
    const tagInputsContainer = document.getElementById('tagInputs');
    const newTagInput = document.createElement('div');
    newTagInput.className = 'tag-input-group';
    
    newTagInput.innerHTML = `
        <input type="text" placeholder="Bird Species" class="tag-name">
        <input type="number" placeholder="Count" min="1" class="tag-count">
        <button type="button" onclick="removeTagInput(this)" class="btn btn-small btn-danger">
            <i class="fas fa-minus"></i>
        </button>
    `;
    
    tagInputsContainer.appendChild(newTagInput);
}

// Remove tag input
function removeTagInput(button) {
    const tagInputGroup = button.closest('.tag-input-group');
    tagInputGroup.remove();
}

// Search by tags with counts
async function searchByTags() {
    const tagInputs = document.querySelectorAll('#tagInputs .tag-input-group');
    const tags = {};
    
    let hasValidTag = false;
    
    tagInputs.forEach(group => {
        const speciesInput = group.querySelector('.tag-name');
        const countInput = group.querySelector('.tag-count');
        
        const species = speciesInput.value.trim();
        const count = parseInt(countInput.value) || 1;
        
        if (species) {
            tags[species] = count;
            hasValidTag = true;
        }
    });
    
    if (!hasValidTag) {
        showToast('Please enter at least one bird species', 'warning');
        return;
    }
    
    try {
        showLoading();
        
        const token = await getCurrentUserToken();
        const response = await fetch(`${AWS_CONFIG.apiGateway.baseUrl}${API_ENDPOINTS.search}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ tags })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const results = await response.json();
        displaySearchResults(results);
        
    } catch (error) {
        console.error('Search error:', error);
        showToast(MESSAGES.search.searchFailed.replace('{error}', error.message), 'error');
    } finally {
        hideLoading();
    }
}

// Search by species (without count requirement)
async function searchBySpecies() {
    const species = document.getElementById('speciesInput').value.trim();
    
    if (!species) {
        showToast('Please enter a bird species name', 'warning');
        return;
    }
    
    try {
        showLoading();
        
        const token = await getCurrentUserToken();
        const response = await fetch(`${AWS_CONFIG.apiGateway.baseUrl}${API_ENDPOINTS.searchBySpecies}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ species })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const results = await response.json();
        displaySearchResults(results);
        
    } catch (error) {
        console.error('Species search error:', error);
        showToast(MESSAGES.search.searchFailed.replace('{error}', error.message), 'error');
    } finally {
        hideLoading();
    }
}

// Search by thumbnail URL
async function searchByUrl() {
    const url = document.getElementById('urlInput').value.trim();
    
    if (!url) {
        showToast('Please enter a thumbnail URL', 'warning');
        return;
    }
    
    try {
        showLoading();
        
        const token = await getCurrentUserToken();
        const response = await fetch(`${AWS_CONFIG.apiGateway.baseUrl}${API_ENDPOINTS.searchByUrl}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ thumbnailUrl: url })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const results = await response.json();
        displaySearchResults(results);
        
    } catch (error) {
        console.error('URL search error:', error);
        showToast(MESSAGES.search.searchFailed.replace('{error}', error.message), 'error');
    } finally {
        hideLoading();
    }
}

// Search by uploading a file
async function searchByFile() {
    const fileInput = document.getElementById('searchFileInput');
    const file = fileInput.files[0];
    
    if (!file) {
        showToast('Please select a file', 'warning');
        return;
    }
    
    if (!validateFile(file)) {
        return;
    }
    
    try {
        showLoading();
        
        // Convert file to base64 for API transmission
        const base64File = await fileToBase64(file);
        
        const token = await getCurrentUserToken();
        const response = await fetch(`${AWS_CONFIG.apiGateway.baseUrl}${API_ENDPOINTS.searchByFile}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                fileData: base64File,
                fileName: file.name,
                fileType: file.type
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const results = await response.json();
        displaySearchResults(results);
        
    } catch (error) {
        console.error('File search error:', error);
        showToast(MESSAGES.search.searchFailed.replace('{error}', error.message), 'error');
    } finally {
        hideLoading();
    }
}

// Convert file to base64
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result.split(',')[1]); // Remove data:image/jpeg;base64, prefix
        reader.onerror = error => reject(error);
    });
}

// Display search results
function displaySearchResults(results) {
    const resultsContainer = document.getElementById('searchResults');
    
    if (!results || !results.links || results.links.length === 0) {
        resultsContainer.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search"></i>
                <h3>No Results Found</h3>
                <p>Try adjusting your search criteria</p>
            </div>
        `;
        return;
    }
    
    resultsContainer.innerHTML = `
        <div class="results-header">
            <h3><i class="fas fa-search"></i> Search Results</h3>
            <p>Found ${results.links.length} matching files</p>
        </div>
        <div class="results-grid" id="resultsGrid">
        </div>
    `;
    
    const resultsGrid = document.getElementById('resultsGrid');
    
    results.links.forEach((link, index) => {
        const resultItem = createSearchResultItem(link, index);
        resultsGrid.appendChild(resultItem);
    });
}

// Create search result item
function createSearchResultItem(link, index) {
    const item = document.createElement('div');
    item.className = 'result-item';
    item.onclick = () => viewFullImage(link);
    
    // Determine if it's an image or other file type
    const isImage = link.includes('-thumb.') || link.match(/\.(jpg|jpeg|png|gif)$/i);
    
    item.innerHTML = `
        ${isImage ? 
            `<img src="${link}" alt="Search result ${index + 1}" loading="lazy">` :
            `<div class="file-placeholder">
                <i class="fas fa-file"></i>
                <p>File</p>
            </div>`
        }
        <div class="result-item-info">
            <h4>Result ${index + 1}</h4>
            <div class="result-actions">
                <button onclick="event.stopPropagation(); copyToClipboard('${link}')" class="btn btn-small">
                    <i class="fas fa-copy"></i>
                </button>
                <button onclick="event.stopPropagation(); viewFullImage('${link}')" class="btn btn-small">
                    <i class="fas fa-external-link-alt"></i>
                </button>
            </div>
        </div>
    `;
    
    return item;
}

// Add search result actions CSS if not already defined
if (!document.querySelector('#searchResultsStyles')) {
    const style = document.createElement('style');
    style.id = 'searchResultsStyles';
    style.textContent = `
        .no-results {
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }
        
        .no-results i {
            font-size: 4rem;
            margin-bottom: 20px;
            opacity: 0.5;
        }
        
        .results-header {
            margin-bottom: 30px;
            text-align: center;
        }
        
        .results-header h3 {
            margin-bottom: 10px;
            color: #333;
        }
        
        .results-header p {
            color: #666;
        }
        
        .file-placeholder {
            height: 150px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: #f8f9fa;
            color: #666;
        }
        
        .file-placeholder i {
            font-size: 2rem;
            margin-bottom: 10px;
        }
        
        .result-actions {
            display: flex;
            gap: 5px;
            margin-top: 10px;
        }
        
        .result-actions .btn {
            padding: 5px 8px;
            font-size: 0.8rem;
        }
    `;
    document.head.appendChild(style);
}