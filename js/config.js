// js/config.js - Configuration File

const AWS_CONFIG = {
    region: 'us-east-1',
    
    cognito: {
        userPoolId: 'us-east-1_XXXXXXXXX',           // Replace with your User Pool ID
        userPoolWebClientId: 'xxxxxxxxxxxxxxxxxx',   // Replace with your App Client ID
        domain: 'your-app-name'                      // Replace with your Cognito Domain
    },
    
    apiGateway: {
        baseUrl: 'https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/dev'  // Replace with your API Gateway URL
    },
    
    s3: {
        bucketName: 'your-bird-bucket',              // Replace with your S3 bucket
        region: 'us-east-1'
    }
};

// API Endpoints
const API_ENDPOINTS = {
    upload: '/upload',
    search: '/search',
    searchSpecies: '/search/species',
    searchUrl: '/search/url',
    searchFile: '/search/file',
    tags: '/tags',
    files: '/files',
    notifications: '/notifications'
};

// Supported file types
const SUPPORTED_FILE_TYPES = {
    images: ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'],
    videos: ['video/mp4', 'video/avi', 'video/mov'],
    audio: ['audio/wav', 'audio/mp3', 'audio/ogg']
};

// Get all supported file types as array
const ALL_SUPPORTED_TYPES = [
    ...SUPPORTED_FILE_TYPES.images,
    ...SUPPORTED_FILE_TYPES.videos,
    ...SUPPORTED_FILE_TYPES.audio
];