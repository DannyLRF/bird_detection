# pages/Upload.py
import streamlit as st
import time
import requests
from PIL import Image
import io
from helpers import init_session_state, simulate_ai_detection, format_file_size
from auth import check_authentication

init_session_state()

def process_uploaded_files(uploaded_files):
    """Process uploaded files and show progress."""
    progress_bar = st.progress(0)
    status_text = st.empty()
    results = []
    
    for i, uploaded_file in enumerate(uploaded_files):
        progress = (i + 1) / len(uploaded_files)
        progress_bar.progress(progress)
        status_text.text(f"Processing {uploaded_file.name}...")
        
        # This is a mock processing step
        result = simulate_ai_detection(uploaded_file)
        results.append(result)
    
    st.session_state.upload_results.extend(results)
    progress_bar.progress(1.0)
    status_text.success("Processing complete!")
    time.sleep(1)
    st.rerun()

def show_upload_results():
    """Display results from file uploads."""
    if not st.session_state.upload_results:
        st.info("Upload files to see identification results here.")
        return

    st.subheader(f"{len(st.session_state.upload_results)} Upload Result(s)")
    for i, result in enumerate(st.session_state.upload_results):
        with st.expander(f"🔍 {result['file_name']} - {result['species']} ({result['confidence']:.1%})"):
            col1, col2 = st.columns([1, 2])
            with col1:
                if result['file_type'].startswith('image/') and result.get('file_data'):
                    try:
                        st.image(Image.open(io.BytesIO(result['file_data'])), caption=result['file_name'], use_column_width=True)
                    except Exception as e:
                        st.warning(f"Could not display image: {e}")
                else:
                    st.info(f"📁 Preview not available for {result['file_type']}")
            with col2:
                st.markdown(f"**Species:** {result['species']}")
                st.metric("Confidence", f"{result['confidence']:.1%}")
                st.metric("Detected Count", result['count'])
                st.markdown(f"**File Size:** {format_file_size(result['file_size'])}")

# --- Main Page UI ---
if not check_authentication():
    st.warning("Please log in to access this page.")
    st.stop()

st.header("📤 Upload and Process Files")

uploaded_files = st.file_uploader(
    "Choose bird images, videos, or audio files",
    type=['jpg', 'jpeg', 'png', 'mp4', 'wav', 'mp3'],
    accept_multiple_files=True
)

if uploaded_files:
    if st.button("🔍 Process Files", type="primary", use_container_width=True):
        process_uploaded_files(uploaded_files)

st.markdown("---")
show_upload_results()