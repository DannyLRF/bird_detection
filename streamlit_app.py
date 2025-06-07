# app.py
import streamlit as st
import boto3
import json
import time
from PIL import Image
import pandas as pd
from datetime import datetime
import io
import base64
import requests
from urllib.parse import urlencode, urlparse, parse_qs
import webbrowser
import hashlib
import secrets
import urllib.parse
from datetime import datetime

# Add JWT import and error handling
try:
    import jwt
except ImportError:
    st.error("Missing required dependency: PyJWT. Please install it with: pip install PyJWT")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Bird Tagging System",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# AWS configuration
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

# IMPORTANT: Streamlit runs on localhost by default. 
# Make sure to set this to your actual deployed URL if deploying.
# Also, ensure this URL is added to your Cognito User Pool App Client's Callback URLs.
REDIRECT_URI = "https://99-birddetection.streamlit.app/"

# Initialize session state
def init_session_state():
    """Initialize session state variables"""
    defaults = {
        'authenticated': False,
        'user_name': '',
        'upload_results': [],
        'search_results': [],
        'id_token': None,
        'access_token': None,
        'auth_error': None,
        'logout_requested': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def show_login_page():
    """Display login page"""
    # Custom CSS
    st.markdown("""
        <style>
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            text-align: center;
        }
        .login-button {
            display: block;
            width: 100%;
            padding: 12px 24px;
            background-color: #0066cc;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            font-size: 16px;
            text-align: center;
            transition: background-color 0.3s;
        }
        .login-button:hover {
            background-color: #0052a3;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    st.title("🕊️ Bird Tagging System")
    st.markdown("### AI-powered bird identification")
    
    st.markdown("---")
    
    # Display error message if any
    if st.session_state.auth_error:
        st.error(st.session_state.auth_error)
        st.session_state.auth_error = None
    
    # Login button
    cognito_url = build_cognito_url()
    
    st.markdown(
        f'<a href="{cognito_url}" class="login-button">🔐 Sign in with AWS</a>',
        unsafe_allow_html=True
    )
    
    # Add force re-login option
    st.markdown("---")
    
    col_login1, col_login2 = st.columns(2)
    with col_login1:
        if st.button("🔄 Force Re-login", help="Force login even if you have an active session"):
            # Build URL with prompt=login to force re-authentication
            force_login_params = {
                'response_type': 'code',
                'client_id': AWS_CONFIG['cognito']['app_client_id'],
                'redirect_uri': REDIRECT_URI,
                'scope': 'openid profile email',
                'prompt': 'login'  # Force login screen
            }
            base_url = f"https://{AWS_CONFIG['cognito']['domain']}/oauth2/authorize"
            force_login_url = f"{base_url}?{urllib.parse.urlencode(force_login_params)}"
            st.markdown(f'<meta http-equiv="refresh" content="0; url={force_login_url}">', unsafe_allow_html=True)
            st.stop()
    
    with col_login2:
        if st.button("👥 Switch Account", help="Login with a different account"):
            # Logout first, then login
            logout_url = build_cognito_logout_url()
            st.markdown(f'<meta http-equiv="refresh" content="0; url={logout_url}">', unsafe_allow_html=True)
            st.stop()
    
    st.markdown("---")
    
    # Information message
    st.info("You'll be redirected to AWS Cognito for secure authentication")
    
    # Debug information (optional)
    with st.expander("🔧 Debug Information"):
        st.code(f"Redirect URI: {REDIRECT_URI}", language=None)
        st.code(f"Client ID: {AWS_CONFIG['cognito']['app_client_id']}", language=None)
        if st.button("Copy Login URL"):
            st.code(cognito_url, language=None)
    
    st.markdown('</div>', unsafe_allow_html=True)

def build_cognito_url():
    """Build Cognito authorization URL"""
    params = {
        'response_type': 'code',
        'client_id': AWS_CONFIG['cognito']['app_client_id'],
        'redirect_uri': REDIRECT_URI,
        'scope': 'openid profile email'
    }
    
    base_url = f"https://{AWS_CONFIG['cognito']['domain']}/oauth2/authorize"
    query_string = urllib.parse.urlencode(params)
    return f"{base_url}?{query_string}"

def build_cognito_logout_url():
    """Build Cognito logout URL"""
    params = {
        'client_id': AWS_CONFIG['cognito']['app_client_id'],
        'logout_uri': REDIRECT_URI
    }
    
    base_url = f"https://{AWS_CONFIG['cognito']['domain']}/logout"
    query_string = urllib.parse.urlencode(params)
    return f"{base_url}?{query_string}"

def handle_cognito_callback():
    """Handle Cognito callback"""
    query_params = st.query_params
    
    # Check if returning from logout
    if len(query_params) == 0 and st.session_state.get('logout_requested', False):
        st.session_state.logout_requested = False
        st.success("Successfully logged out!")
        return False
    
    # Check for errors
    if 'error' in query_params:
        st.session_state.auth_error = f"Authentication error: {query_params.get('error_description', 'Unknown error')}"
        st.query_params.clear()
        return False
    
    # Check for authorization code
    if 'code' in query_params:
        auth_code = query_params['code']
        
        try:
            # Exchange authorization code for tokens
            token_endpoint = f"https://{AWS_CONFIG['cognito']['domain']}/oauth2/token"
            
            data = {
                'grant_type': 'authorization_code',
                'client_id': AWS_CONFIG['cognito']['app_client_id'],
                'code': auth_code,
                'redirect_uri': REDIRECT_URI
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.post(
                token_endpoint,
                data=urllib.parse.urlencode(data),
                headers=headers
            )
            
            if response.status_code == 200:
                tokens = response.json()
                st.session_state.id_token = tokens.get('id_token')
                st.session_state.access_token = tokens.get('access_token')
                
                # Parse user information - add error handling
                try:
                    decoded = jwt.decode(
                        st.session_state.id_token,
                        options={"verify_signature": False}
                    )
                    
                    st.session_state.user_name = (
                        decoded.get('email') or 
                        decoded.get('cognito:username') or 
                        'User'
                    )
                    st.session_state.authenticated = True
                    
                    # Clear URL parameters
                    st.query_params.clear()
                    return True
                    
                except Exception as jwt_error:
                    st.session_state.auth_error = f"JWT decode error: {str(jwt_error)}"
                    st.query_params.clear()
                    return False
                    
            else:
                st.session_state.auth_error = f"Token exchange failed: {response.text}"
                st.query_params.clear()
                return False
                
        except Exception as e:
            st.session_state.auth_error = f"Authentication error: {str(e)}"
            st.query_params.clear()
            return False
    
    return None

# Main application
def show_main_app():
    # Top header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🕊️ Bird Tagging System")
        st.markdown(f"Welcome back, **{st.session_state.user_name}**!")
    
    with col2:
        if st.button("🚪 Logout", type="secondary"):
            # Clear local session state
            st.session_state.authenticated = False
            st.session_state.user_name = ''
            st.session_state.upload_results = []
            st.session_state.search_results = []
            st.session_state.id_token = None
            st.session_state.access_token = None
            st.session_state.logout_requested = True
            
            # Redirect to Cognito logout URL
            logout_url = build_cognito_logout_url()
            st.markdown(f'<meta http-equiv="refresh" content="0; url={logout_url}">', unsafe_allow_html=True)
            st.stop()
    
    st.markdown("---")
    
    # Create main layout
    col1, col2, col3 = st.columns([1, 1, 1])
    
    # Upload section
    with col1:
        st.header("📤 Upload Files")
        uploaded_files = st.file_uploader(
            "Choose bird files",
            type=['jpg', 'jpeg', 'png', 'mp4', 'wav', 'mp3'],
            accept_multiple_files=True,
            help="Upload images, videos, or audio files of birds"
        )
        
        if uploaded_files:
            if st.button("🔍 Process Files", type="primary"):
                process_uploaded_files(uploaded_files)
    
    # Search section
    with col2:
        st.header("🔍 Search Files")
        
        # Basic search
        search_query = st.text_input("Search by species name", placeholder="e.g., crow, pigeon")
        
        # Advanced filters
        with st.expander("🔧 Advanced Filters"):
            file_type_filter = st.selectbox("File Type", ["All", "Images", "Videos", "Audio"])
            confidence_filter = st.selectbox(
                "Confidence Level", 
                ["Any", "High (90%+)", "Medium (70%+)", "Low (50%+)"]
            )
        
        if st.button("🔍 Search", type="primary"):
            search_files(search_query, file_type_filter, confidence_filter)
        
        if st.button("🗑️ Clear Search"):
            st.session_state.search_results = []
            st.rerun()
    
    # Statistics section
    with col3:
        st.header("📊 Statistics")
        show_statistics()
        
        if st.button("📈 Detailed Stats"):
            show_detailed_statistics()
    
    st.markdown("---")
    
    # Results section
    st.header("📋 Results")
    
    # Tabs for results
    tab1, tab2 = st.tabs(["📤 Upload Results", "🔍 Search Results"])
    
    with tab1:
        show_upload_results()
    
    with tab2:
        show_search_results()

# Handle file uploads and processing
def process_uploaded_files(uploaded_files):
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    
    for i, uploaded_file in enumerate(uploaded_files):
        # Display file info
        progress = (i + 1) / len(uploaded_files)
        progress_bar.progress(progress)
        status_text.text(f"Processing {uploaded_file.name}...")

        file_name = uploaded_file.name
        file_type = uploaded_file.type

        try:
            # Request pre-signed URL
            api_url = "https://3dw1wpo1ra.execute-api.us-east-1.amazonaws.com/production/upload"
            response = requests.post(
                api_url,
                json={"fileName": file_name, "fileType": file_type}
            )

            if response.status_code != 200:
                st.error("Failed to get pre-signed URL")
            else:
                upload_url = response.json()["uploadUrl"]

                # Upload file to S3
                s3_response = requests.put(
                    upload_url,
                    data=uploaded_file.getvalue(),
                    headers={"Content-Type": file_type}
                )

                if s3_response.status_code == 200:
                    st.success("File upload successful!")
                else:
                    st.error(f"Upload failed with status: {s3_response.status_code}")

        except Exception as e:
            st.error(f"An error occurred: {e}")
        
        # Generate a mock result
        result = simulate_ai_detection(uploaded_file)
        results.append(result)
    
    # Store results in session state
    st.session_state.upload_results.extend(results)
    
    # Complete processing
    progress_bar.progress(1.0)
    status_text.text("✅ Processing complete!")
    
    st.success(f"Successfully processed {len(uploaded_files)} file(s)!")
    time.sleep(1)
    st.rerun()

# Simulate AI detection
def simulate_ai_detection(uploaded_file):
    # Simulate species detection
    species_list = ['Crow', 'Pigeon', 'Sparrow', 'Robin', 'Cardinal', 'Blue Jay', 'Eagle', 'Owl']
    detected_species = species_list[hash(uploaded_file.name) % len(species_list)]
    
    # Simulate confidence score
    confidence = 0.75 + (hash(uploaded_file.name) % 25) / 100
    
    # Simulate count of detected birds
    count = (hash(uploaded_file.name) % 3) + 1
    
    return {
        'file_name': uploaded_file.name,
        'file_type': uploaded_file.type,
        'file_size': uploaded_file.size,
        'species': detected_species,
        'confidence': confidence,
        'count': count,
        'timestamp': datetime.now(),
        'file_data': uploaded_file.read()  # Store file data for preview
    }

# Search files based on query and filters
def search_files(query, file_type_filter, confidence_filter):
    if not query.strip():
        st.warning("Please enter a search term")
        return
    
    with st.spinner("Searching..."):
        time.sleep(1)
        
        # Search in uploaded results
        search_results = []
        for result in st.session_state.upload_results:
            if query.lower() in result['species'].lower():
                search_results.append(result)
        
        # Mock search results
        mock_results = generate_mock_search_results(query)
        search_results.extend(mock_results)
        
        # Filter results based on file type and confidence
        if file_type_filter != "All":
            if file_type_filter == "Images":
                search_results = [r for r in search_results if r['file_type'].startswith('image/')]
            elif file_type_filter == "Videos":
                search_results = [r for r in search_results if r['file_type'].startswith('video/')]
            elif file_type_filter == "Audio":
                search_results = [r for r in search_results if r['file_type'].startswith('audio/')]
        
        if confidence_filter != "Any":
            confidence_map = {
                "High (90%+)": 0.9,
                "Medium (70%+)": 0.7,
                "Low (50%+)": 0.5
            }
            min_confidence = confidence_map[confidence_filter]
            search_results = [r for r in search_results if r['confidence'] >= min_confidence]
        
        st.session_state.search_results = search_results
        
    st.success(f"Found {len(search_results)} result(s) for '{query}'")

# Generate mock search results
def generate_mock_search_results(query):
    mock_database = [
        {'file_name': 'crow_flock.jpg', 'species': 'Crow', 'confidence': 0.95, 'count': 3, 'file_type': 'image/jpeg'},
        {'file_name': 'pigeon_park.mp4', 'species': 'Pigeon', 'confidence': 0.87, 'count': 2, 'file_type': 'video/mp4'},
        {'file_name': 'sparrow_song.wav', 'species': 'Sparrow', 'confidence': 0.92, 'count': 1, 'file_type': 'audio/wav'},
        {'file_name': 'robin_nest.jpg', 'species': 'Robin', 'confidence': 0.88, 'count': 1, 'file_type': 'image/jpeg'},
        {'file_name': 'eagle_soar.mp4', 'species': 'Eagle', 'confidence': 0.94, 'count': 1, 'file_type': 'video/mp4'}
    ]
    
    results = []
    for item in mock_database:
        if query.lower() in item['species'].lower():
            results.append({
                **item,
                'timestamp': datetime.now(),
                'file_data': None  # No file data for mock results
            })
    
    return results

# Display upload results
def show_upload_results():
    if not st.session_state.upload_results:
        st.info("📝 Upload files to see identification results here")
        return
    
    st.subheader(f"📤 {len(st.session_state.upload_results)} Upload Result(s)")
    
    for i, result in enumerate(st.session_state.upload_results):
        with st.expander(f"🔍 {result['file_name']} - {result['species']} ({result['confidence']:.1%})"):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Display file preview
                if result['file_type'].startswith('image/') and result.get('file_data'):
                    try:
                        image = Image.open(io.BytesIO(result['file_data']))
                        st.image(image, caption=result['file_name'], use_column_width=True)
                    except:
                        st.info("📷 Image preview not available")
                else:
                    st.info(f"📁 {get_file_type_emoji(result['file_type'])} {result['file_type']}")
            
            with col2:
                st.markdown(f"**Species:** {result['species']}")
                st.markdown(f"**Confidence:** {result['confidence']:.1%}")
                st.markdown(f"**Count:** {result['count']} detected")
                st.markdown(f"**File Size:** {format_file_size(result['file_size'])}")
                st.markdown(f"**Uploaded:** {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button(f"👁️ View", key=f"view_{i}"):
                        st.info("File preview feature")
                with col_btn2:
                    if st.button(f"📤 Share", key=f"share_{i}"):
                        st.info("Share feature coming soon!")

# Display search results
def show_search_results():
    if not st.session_state.search_results:
        st.info("🔍 Use the search function to find files")
        return
    
    st.subheader(f"🔍 {len(st.session_state.search_results)} Search Result(s)")
    
    # Create a DataFrame for search results
    df_data = []
    for result in st.session_state.search_results:
        df_data.append({
            'File Name': result['file_name'],
            'Species': result['species'],
            'Confidence': f"{result['confidence']:.1%}",
            'Count': result['count'],
            'Type': get_file_type_display(result['file_type']),
            'Timestamp': result['timestamp'].strftime('%Y-%m-%d %H:%M') if result.get('timestamp') else 'N/A'
        })
    
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True)
    
    # Detailed view
    st.subheader("📋 Detailed View")
    for i, result in enumerate(st.session_state.search_results):
        with st.expander(f"📁 {result['file_name']}"):
            col1, col2 = st.columns([1, 1])
            with col1:
                st.metric("Species", result['species'])
                st.metric("Confidence", f"{result['confidence']:.1%}")
            with col2:
                st.metric("Count", result['count'])
                st.metric("File Type", get_file_type_display(result['file_type']))

# Display statistics
def show_statistics():
    total_files = len(st.session_state.upload_results)
    
    if total_files == 0:
        st.info("📊 Upload files to see statistics")
        return
    
    # Basic statistics
    species_count = {}
    total_detections = 0
    high_confidence_count = 0
    
    for result in st.session_state.upload_results:
        species = result['species']
        species_count[species] = species_count.get(species, 0) + result['count']
        total_detections += result['count']
        
        if result['confidence'] >= 0.9:
            high_confidence_count += 1
    
    # Display summary statistics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Files", total_files)
        st.metric("Total Detections", total_detections)
    
    with col2:
        st.metric("Unique Species", len(species_count))
        st.metric("High Confidence", f"{high_confidence_count}/{total_files}")
    
    # Most common species
    if species_count:
        most_common = max(species_count.items(), key=lambda x: x[1])
        st.metric("Most Common", f"{most_common[0]} ({most_common[1]})")

# Display detailed statistics
def show_detailed_statistics():
    st.subheader("📊 Detailed Statistics")
    
    if not st.session_state.upload_results:
        st.warning("No data available for statistics")
        return
    
    # Species distribution, confidence distribution, and file type statistics
    species_data = {}
    confidence_data = []
    file_type_data = {}
    
    for result in st.session_state.upload_results:
        # Species statistics
        species = result['species']
        species_data[species] = species_data.get(species, 0) + result['count']
        
        # Confidence distribution
        confidence_data.append(result['confidence'])
        
        # File type statistics
        file_type = get_file_type_display(result['file_type'])
        file_type_data[file_type] = file_type_data.get(file_type, 0) + 1
    
    # Create bar charts for species and file types
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🦅 Species Distribution")
        if species_data:
            species_df = pd.DataFrame(list(species_data.items()), columns=['Species', 'Count'])
            st.bar_chart(species_df.set_index('Species'))
    
    with col2:
        st.subheader("📁 File Types")
        if file_type_data:
            file_type_df = pd.DataFrame(list(file_type_data.items()), columns=['Type', 'Count'])
            st.bar_chart(file_type_df.set_index('Type'))
    
    # Confidence distribution
    st.subheader("🎯 Confidence Distribution")
    if confidence_data:
        confidence_df = pd.DataFrame({'Confidence': confidence_data})
        st.histogram(confidence_df['Confidence'], bins=20)
    
    # Generate report
    if st.button("📥 Download Report"):
        report_data = {
            'summary': {
                'total_files': len(st.session_state.upload_results),
                'total_detections': sum(r['count'] for r in st.session_state.upload_results),
                'unique_species': len(species_data),
                'generation_time': datetime.now().isoformat()
            },
            'species_distribution': species_data,
            'file_types': file_type_data,
            'detailed_results': [
                {
                    'file_name': r['file_name'],
                    'species': r['species'],
                    'confidence': r['confidence'],
                    'count': r['count'],
                    'timestamp': r['timestamp'].isoformat()
                }
                for r in st.session_state.upload_results
            ]
        }
        
        st.download_button(
            label="📥 Download JSON Report",
            data=json.dumps(report_data, indent=2),
            file_name=f"bird_tagging_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

# Utility functions for file type handling
def get_file_type_emoji(file_type):
    if file_type.startswith('image/'):
        return '🖼️'
    elif file_type.startswith('video/'):
        return '🎥'
    elif file_type.startswith('audio/'):
        return '🎵'
    else:
        return '📁'

def get_file_type_display(file_type):
    if file_type.startswith('image/'):
        return 'Image'
    elif file_type.startswith('video/'):
        return 'Video'
    elif file_type.startswith('audio/'):
        return 'Audio'
    else:
        return 'Unknown'

def format_file_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} TB"

def main():
    """Main function"""
    init_session_state()
    
    # Handle Cognito callback
    callback_result = handle_cognito_callback()
    
    if callback_result is True:
        st.success("Successfully authenticated!")
        time.sleep(1)
        st.rerun()
    
    # Display application
    if st.session_state.authenticated:
        show_main_app()
    else:
        show_login_page()

if __name__ == "__main__":
    main()