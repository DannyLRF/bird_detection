# config.py
import os

AWS_CONFIG = {
    'region': 'ap-southeast-2',
    'cognito': {
        'user_pool_id': 'ap-southeast-2_3O9qdhhLL',
        'app_client_id': '2lio1ipeg3tabimmqlmtuii1um',
        'domain': 'ap-southeast-23o9qdhhll.auth.ap-southeast-2.amazoncognito.com'
    },
    's3': {
        'bucket_name': 'team99-uploaded-files'
    }
}

REDIRECT_URI = "https://99-birddetection.streamlit.app/"

# REDIRECT_URI = "http://localhost:8501/"

API_BASE_URL = "https://d2u7y2aieb.execute-api.ap-southeast-2.amazonaws.com/dev/api"