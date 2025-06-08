# pages/1_📤_Upload.py
import streamlit as st
import requests
from helpers import init_session_state
from auth_utils import require_authentication
from config import API_BASE_URL

init_session_state()
require_authentication()

st.header("📤 Upload and Process Files")

def hide_sidebar():
    """Hide the sidebar using CSS when user is not authenticated."""
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

def process_uploaded_files(uploaded_files):
    """
    Process each uploaded file by getting a pre-signed URL and uploading to S3.
    """
    st.info(f"Starting upload for {len(uploaded_files)} file(s)...")
    progress_bar = st.progress(0)
    
    for i, uploaded_file in enumerate(uploaded_files):
        with st.status(f"Uploading {uploaded_file.name}...", expanded=True) as status:
            try:
                # 1. Get pre-signed URL from our API
                st.write("Requesting upload URL...")
                api_url = f"{API_BASE_URL}/upload"
                response = requests.post(
                    api_url,
                    json={"fileName": uploaded_file.name, "fileType": uploaded_file.type}
                )
                response.raise_for_status()  # Will raise an exception for 4XX/5XX errors
                
                presigned_data = response.json()
                upload_url = presigned_data["uploadUrl"]
                st.write("Upload URL received. Uploading to S3...")

                # 2. Upload file to the pre-signed URL
                s3_response = requests.put(
                    upload_url,
                    data=uploaded_file.getvalue(),
                    headers={"Content-Type": uploaded_file.type}
                )
                s3_response.raise_for_status()

                status.update(label=f"✅ {uploaded_file.name} uploaded successfully!", state="complete")

            except requests.exceptions.RequestException as e:
                status.update(label=f"❌ Error uploading {uploaded_file.name}: {e}", state="error")
            
        progress_bar.progress((i + 1) / len(uploaded_files))
    
    st.success("All file uploads initiated! Backend processing will start shortly.")
    st.warning("You can go to the 'Search' page to find your files after a few moments.")

# --- Authentication Check ---
if not check_authentication():
    hide_sidebar()
    st.warning("Please log in to access this page.")
    st.markdown("👈 **Go back to the main page to log in.**")
    if st.button("🏠 Go to Home Page"):
        st.switch_page("streamlit_app.py")
    st.stop()

# --- Main Page UI ---
st.header("📤 Upload and Process Files")

uploaded_files = st.file_uploader(
    "Choose bird images, videos, or audio files",
    type=['jpg', 'jpeg', 'png', 'mp4', 'wav', 'mp3'],
    accept_multiple_files=True
)

if uploaded_files:
    if st.button("🚀 Start Upload", type="primary", use_container_width=True):
        process_uploaded_files(uploaded_files)

st.markdown("---")
st.info(
    "**How it works:**\n\n"
    "1. Files are uploaded securely to our backend.\n"
    "2. The backend AI model processes each file to identify birds.\n"
    "3. Once processed, you can find your tagged files on the **Search** page."
)