# Bird Tagging System

An AWS-based web application for automated bird species identification and file management.

## Features

- **User Authentication**: AWS Cognito integration with email verification
- **File Upload**: Support for images, videos, and audio files with drag-and-drop
- **AI Bird Detection**: Automated bird species identification using pre-trained models
- **Search Functionality**: Multiple search options (tags, species, URL, file-based)
- **Tag Management**: Bulk add/remove tags from files
- **Notifications**: Email alerts for new files with specific bird species

## Technology Stack

- **Frontend**: Python, streamlit
- **Backend**: AWS Lambda, API Gateway
- **Storage**: AWS S3
- **Database**: AWS DynamoDB
- **Authentication**: AWS Cognito
- **Notifications**: AWS SNS
- **ML Processing**: Pre-trained bird identification models

## Setup Instructions

### Prerequisites

- AWS Account with appropriate permissions
- Basic web development knowledge

### 1. AWS Infrastructure Setup

1. **Create Cognito User Pool**
   - Configure user attributes (email, given_name, family_name)
   - Set up email verification
   - Create app client

2. **Create Cognito Identity Pool**
   - Link to User Pool
   - Configure IAM roles

3. **Set up S3 Buckets**
   - Main files bucket
   - Thumbnails bucket

4. **Deploy Lambda Functions**
   - File processing functions
   - Search and query handlers
   - Tag management functions

5. **Configure API Gateway**
   - Create REST API
   - Set up Cognito authorizers
   - Configure CORS

### 2. Frontend Configuration

1. Clone this repository:
   ```bash
   git clone https://github.com/DannyLRF/bird_detection.git
   cd bird_detection
