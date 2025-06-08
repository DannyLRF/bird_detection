# config.py

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