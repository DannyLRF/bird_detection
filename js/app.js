// Main application functionality

// Show/hide loading overlay
function showLoading() {
    document.getElementById('loading').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

// Show specific section
function showSection(sectionName) {
    // Hide all sections
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => {
        section.style.display = 'none';
    });
    
    // Show selected section
    const targetSection = document.getElementById(sectionName + 'Section');
    if (targetSection) {
        targetSection.style.display = 'block';
    }
    
    // Update navigation active state
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.classList.remove('active');
    });
    
    // Find and activate the corresponding nav link
    const activeLink = document.querySelector(`[onclick="showSection('${sectionName}')"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
}

// Toast notification system
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, TOAST_DURATION);
}

// Bulk tag operations
function addBulkTagInput() {
    const container = document.getElementById('bulkTagInputs');
    const newInput = document.createElement('div');
    newInput.className = 'bulk-tag-input';
    
    newInput.innerHTML = `
        <input type="text" placeholder="crow,3" class="bulk-tag">
        <button type="button" onclick="removeBulkTagInput(this)" class="btn btn-small btn-danger">
            <i class="fas fa-minus"></i>
        </button>
    `;
    
    container.appendChild(newInput);
}

function removeBulkTagInput(button) {
    const inputGroup = button.closest('.bulk-tag-input');
    inputGroup.remove();
}

// Handle bulk tag operations
async function handleBulkTagOperation(event) {
    event.preventDefault();
    
    const urls = document.getElementById('bulkUrls').value
        .split('\n')
        .map(url => url.trim())
        .filter(url => url);
    
    const operation = document.getElementById('operation').value;
    
    const tagInputs = document.querySelectorAll('.bulk-tag');
    const tags = [];
    
    tagInputs.forEach(input => {
        const value = input.value.trim();
        if (value) {
            tags.push(value);
        }
    });
    
    if (urls.length === 0) {
        showToast('Please enter at least one URL', 'warning');
        return;
    }
    
    if (tags.length === 0) {
        showToast('Please enter at least one tag', 'warning');
        return;
    }
    
    try {
        showLoading();
        
        const token = await getCurrentUserToken();
        const response = await fetch(`${AWS_CONFIG.apiGateway.baseUrl}${API_ENDPOINTS.manageTags}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                url: urls,
                operation: parseInt(operation),
                tags: tags
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        showToast(MESSAGES.tags.operationSuccess, 'success');
        
        // Clear form
        document.getElementById('bulkUrls').value = '';
        document.querySelectorAll('.bulk-tag').forEach(input => input.value = '');
        
    } catch (error) {
        console.error('Bulk tag operation error:', error);
        showToast(MESSAGES.tags.operationFailed.replace('{error}', error.message), 'error');
    } finally {
        hideLoading();
    }
}

// Handle file deletion
async function handleDeleteFiles(event) {
    event.preventDefault();
    
    const urls = document.getElementById('deleteUrls').value
        .split('\n')
        .map(url => url.trim())
        .filter(url => url);
    
    if (urls.length === 0) {
        showToast('Please enter at least one URL to delete', 'warning');
        return;
    }
    
    if (!confirm(`Are you sure you want to delete ${urls.length} files? This action cannot be undone.`)) {
        return;
    }
    
    try {
        showLoading();
        
        const token = await getCurrentUserToken();
        const response = await fetch(`${AWS_CONFIG.apiGateway.baseUrl}${API_ENDPOINTS.deleteFiles}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                urls: urls
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        showToast(MESSAGES.tags.deleteSuccess, 'success');
        
        // Clear form
        document.getElementById('deleteUrls').value = '';
        
    } catch (error) {
        console.error('Delete files error:', error);
        showToast(MESSAGES.tags.deleteFailed.replace('{error}', error.message), 'error');
    } finally {
        hideLoading();
    }
}

// Notification management
function addNotificationTag() {
    const container = document.getElementById('notificationTags');
    const newInput = document.createElement('div');
    newInput.className = 'notification-tag-input';
    
    newInput.innerHTML = `
        <input type="text" placeholder="Bird Species" class="notification-tag">
        <button type="button" onclick="removeNotificationTag(this)" class="btn btn-small btn-danger">
            <i class="fas fa-minus"></i>
        </button>
    `;
    
    container.appendChild(newInput);
}

function removeNotificationTag(button) {
    const inputGroup = button.closest('.notification-tag-input');
    inputGroup.remove();
}

// Handle notification subscription
async function handleNotificationSubscription(event) {
    event.preventDefault();
    
    const email = document.getElementById('notificationEmail').value.trim();
    const tagInputs = document.querySelectorAll('.notification-tag');
    const tags = [];
    
    tagInputs.forEach(input => {
        const value = input.value.trim();
        if (value) {
            tags.push(value);
        }
    });
    
    if (!email) {
        showToast('Please enter an email address', 'warning');
        return;
    }
    
    if (tags.length === 0) {
        showToast('Please enter at least one bird species', 'warning');
        return;
    }
    
    try {
        showLoading();
        
        const token = await getCurrentUserToken();
        const response = await fetch(`${AWS_CONFIG.apiGateway.baseUrl}${API_ENDPOINTS.notifications}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                email: email,
                tags: tags
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        showToast(MESSAGES.notifications.subscribeSuccess, 'success');
        
        // Clear form
        document.getElementById('notificationEmail').value = '';
        document.querySelectorAll('.notification-tag').forEach(input => input.value = '');
        
        // Refresh subscription list
        loadSubscriptions();
        
    } catch (error) {
        console.error('Notification subscription error:', error);
        showToast(MESSAGES.notifications.subscribeFailed.replace('{error}', error.message), 'error');
    } finally {
        hideLoading();
    }
}

// Load user subscriptions
async function loadSubscriptions() {
    try {
        const token = await getCurrentUserToken();
        const response = await fetch(`${AWS_CONFIG.apiGateway.baseUrl}${API_ENDPOINTS.notifications}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const subscriptions = await response.json();
        displaySubscriptions(subscriptions);
        
    } catch (error) {
        console.error('Load subscriptions error:', error);
    }
}

// Display subscriptions
function displaySubscriptions(subscriptions) {
    const container = document.getElementById('subscriptionList');
    
    if (!subscriptions || subscriptions.length === 0) {
        container.innerHTML = '<p>No active subscriptions</p>';
        return;
    }
    
    container.innerHTML = subscriptions.map(subscription => `
        <div class="subscription-item">
            <div class="subscription-info">
                <strong>${subscription.email}</strong>
                <div class="subscription-tags">
                    ${subscription.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                </div>
            </div>
            <button onclick="unsubscribe('${subscription.id}')" class="btn btn-small btn-danger">
                <i class="fas fa-trash"></i> Unsubscribe
            </button>
        </div>
    `).join('');
}

// Unsubscribe from notifications
async function unsubscribe(subscriptionId) {
    if (!confirm('Are you sure you want to unsubscribe?')) {
        return;
    }
    
    try {
        showLoading();
        
        const token = await getCurrentUserToken();
        const response = await fetch(`${AWS_CONFIG.apiGateway.baseUrl}${API_ENDPOINTS.notifications}/${subscriptionId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        showToast(MESSAGES.notifications.unsubscribeSuccess, 'success');
        loadSubscriptions(); // Refresh the list
        
    } catch (error) {
        console.error('Unsubscribe error:', error);
        showToast(MESSAGES.notifications.unsubscribeFailed.replace('{error}', error.message), 'error');
    } finally {
        hideLoading();
    }
}

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    // Load subscriptions when notifications section is shown
    const notificationsLink = document.querySelector('[onclick="showSection(\'notifications\')"]');
    if (notificationsLink) {
        notificationsLink.addEventListener('click', function() {
            setTimeout(() => {
                loadSubscriptions();
            }, 100);
        });
    }
});

// Add active navigation style
const style = document.createElement('style');
style.textContent = `
    .nav-link.active {
        background: #667eea;
        color: white !important;
    }
`;
document.head.appendChild(style);