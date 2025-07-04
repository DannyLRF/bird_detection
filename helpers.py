# helpers.py 
import streamlit as st
from datetime import datetime
from PIL import Image
import io

def format_file_size(size_bytes):
    """Format file size for display."""
    if size_bytes == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def get_file_type_display(file_type):
    """Get a user-friendly display name for a file type."""
    if file_type.startswith('image/'):
        return 'Image'
    elif file_type.startswith('video/'):
        return 'Video'
    elif file_type.startswith('audio/'):
        return 'Audio'
    return 'Unknown'

# --- API调用函数 ---

def get_user_uploads():
    """get uploaded filelist"""
    # TODO: 
    # api_url = f"{API_BASE_URL}/user-uploads"
    # response = requests.get(api_url, headers=auth_headers)
    # return response.json()
    pass

def get_statistics_data():
    """get statistic"""
    # TODO: 
    # api_url = f"{API_BASE_URL}/statistics"
    # response = requests.get(api_url, headers=auth_headers)
    # return response.json()
    pass