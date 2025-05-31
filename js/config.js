// AWS Configuration
const AWS_CONFIG = {
    region: 'us-east-1', // Replace with your actual region
    
    // Cognito configuration
    cognito: {
        userPoolId: 'us-east-1_xxxxxxxxx', // Replace with your User Pool ID
        userPoolWebClientId: 'xxxxxxxxxxxxxxxxxxxxxxxxxx', // Replace with your App Client ID
        identityPoolId: 'us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx' // Replace with your Identity Pool ID
    },
    
    // API Gateway configuration
    apiGateway: {
        baseUrl: 'https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/dev' // Replace with your API Gateway URL
    },
    
    // S3 configuration
    s3: {
        bucketName: 'your-bird-tagging-bucket', // Replace with your S3 bucket name
        region: 'us-east-1'
    }
};

// API endpoints
const API_ENDPOINTS = {
    upload: '/upload',
    search: '/search',
    searchBySpecies: '/search/species',
    searchByUrl: '/search/url', 
    searchByFile: '/search/file',
    manageTags: '/tags',
    deleteFiles: '/files',
    notifications: '/notifications'
};

// Supported file types
const SUPPORTED_FILE_TYPES = {
    images: ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'],
    videos: ['video/mp4', 'video/avi', 'video/mov', 'video/wmv'],
    audio: ['audio/mp3', 'audio/wav', 'audio/aac', 'audio/ogg']
};

// Maximum file size (50MB)
const MAX_FILE_SIZE = 50 * 1024 * 1024;

// Toast display duration
const TOAST_DURATION = 3000;

// Messages
const MESSAGES = {
    auth: {
        loginSuccess: 'Login successful!',
        loginFailed: 'Login failed: ',
        signupSuccess: 'Registration successful! Please check your email for verification code.',
        signupFailed: 'Registration failed: ',
        verificationSuccess: 'Email verification successful! Please login.',
        verificationFailed: 'Verification failed: ',
        logoutSuccess: 'Logged out successfully',
        passwordRequired: 'New password required'
    },
    upload: {
        noValidFiles: 'No valid files selected',
        fileSizeExceeded: 'File {fileName} exceeds maximum size limit (50MB)',
        unsupportedFileType: 'Unsupported file type: {fileName}',
        uploadSuccess: 'Successfully uploaded {count} files',
        uploadFailed: 'Upload failed for {fileName}: {error}',
        linkCopied: 'Link copied to clipboard',
        copyFailed: 'Failed to copy link'
    },
    search: {
        noResults: 'No results found',
        searchFailed: 'Search failed: {error}',
        invalidQuery: 'Invalid search query'
    },
    tags: {
        operationSuccess: 'Tag operation completed successfully',
        operationFailed: 'Tag operation failed: {error}',
        deleteSuccess: 'Files deleted successfully',
        deleteFailed: 'Delete operation failed: {error}'
    },
    notifications: {
        subscribeSuccess: 'Successfully subscribed to notifications',
        subscribeFailed: 'Subscription failed: {error}',
        unsubscribeSuccess: 'Successfully unsubscribed',
        unsubscribeFailed: 'Unsubscribe failed: {error}'
    },
    general: {
        processing: 'Processing...',
        error: 'An error occurred',
        success: 'Operation completed successfully'
    }
};