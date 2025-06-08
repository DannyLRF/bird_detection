# helpers.py
import streamlit as st
from datetime import datetime
from PIL import Image
import io

def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        'authenticated': False,
        'user_name': '',
        'upload_results': [],
        'search_results': [],
        'id_token': None,
        'access_token': None,
        'auth_error': None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

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

# --- Mock/Simulation Functions ---

def simulate_ai_detection(uploaded_file):
    """Simulate AI detection for a given file."""
    species_list = ['Crow', 'Pigeon', 'Sparrow', 'Robin', 'Eagle', 'Owl']
    detected_species = species_list[hash(uploaded_file.name) % len(species_list)]
    confidence = 0.75 + (hash(uploaded_file.name) % 25) / 100
    count = (hash(uploaded_file.name) % 3) + 1
    
    return {
        'file_name': uploaded_file.name,
        'file_type': uploaded_file.type,
        'file_size': uploaded_file.size,
        'species': detected_species,
        'confidence': confidence,
        'count': count,
        'timestamp': datetime.now(),
        'file_data': uploaded_file.read()
    }

def generate_mock_search_results(query):
    """Generate mock search results for a given query."""
    mock_db = [
        {'file_name': 'crow_flock.jpg', 'species': 'Crow', 'confidence': 0.95, 'count': 3, 'file_type': 'image/jpeg'},
        {'file_name': 'pigeon_park.mp4', 'species': 'Pigeon', 'confidence': 0.87, 'count': 2, 'file_type': 'video/mp4'},
        {'file_name': 'sparrow_song.wav', 'species': 'Sparrow', 'confidence': 0.92, 'count': 1, 'file_type': 'audio/wav'},
    ]
    results = [
        {**item, 'timestamp': datetime.now(), 'file_data': None}
        for item in mock_db if query.lower() in item['species'].lower()
    ]
    return results