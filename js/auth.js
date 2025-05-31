// js/auth.js - Simplified Authentication Logic

let currentUser = null;

// Check authentication status when page loads
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    handleCallback(); // Handle return from Cognito
});

// Check login status
function checkAuth() {
    const token = getStoredToken();
    
    if (token && isTokenValid(token)) {
        setupUser(token);
        showMainApp();
    } else {
        showLoginRequired();
    }
}

// Handle Cognito callback
function handleCallback() {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    
    if (code) {
        // Code received from Cognito - in real project, exchange for tokens
        showToast('Login successful!', 'success');
        
        // Clean URL
        window.history.replaceState({}, document.title, window.location.pathname);
        
        // Store mock token (in real project, get from token endpoint)
        const mockToken = 'mock_token_' + Date.now();
        localStorage.setItem('authToken', mockToken);
        
        checkAuth();
    }
}

// Login - redirect to Cognito Hosted UI
function login() {
    const loginUrl = `https://${AWS_CONFIG.cognito.domain}.auth.${AWS_CONFIG.region}.amazoncognito.com/login?` +
        `client_id=${AWS_CONFIG.cognito.userPoolWebClientId}&` +
        `response_type=code&` +
        `scope=email+openid+profile&` +
        `redirect_uri=${encodeURIComponent(window.location.origin)}`;
    
    window.location.href = loginUrl;
}

// Logout
function logout() {
    localStorage.removeItem('authToken');
    
    const logoutUrl = `https://${AWS_CONFIG.cognito.domain}.auth.${AWS_CONFIG.region}.amazoncognito.com/logout?` +
        `client_id=${AWS_CONFIG.cognito.userPoolWebClientId}&` +
        `logout_uri=${encodeURIComponent(window.location.origin)}`;
    
    window.location.href = logoutUrl;
}

// Get stored token
function getStoredToken() {
    return localStorage.getItem('authToken');
}

// Check if token is valid (simplified version)
function isTokenValid(token) {
    return token && token.startsWith('mock_token_');
}

// Setup user information
function setupUser(token) {
    currentUser = {
        token: token,
        name: 'Student User', // Simplified - in real project, parse from token
        email: 'student@example.com'
    };
    
    // Setup AWS credentials (simplified version)
    AWS.config.region = AWS_CONFIG.region;
    
    // Display user name
    document.getElementById('userName').textContent = currentUser.name;
}

// Get current user token (for API calls)
function getCurrentUserToken() {
    return Promise.resolve(currentUser ? currentUser.token : null);
}

// Show login screen
function showLoginRequired() {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('loginRequired').style.display = 'block';
    document.getElementById('mainApp').style.display = 'none';
}

// Show main application
function showMainApp() {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('loginRequired').style.display = 'none';
    document.getElementById('mainApp').style.display = 'block';
}