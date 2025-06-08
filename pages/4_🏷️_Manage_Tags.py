# pages/4_🏷️_Manage_Tags.py
import streamlit as st
import requests
from helpers import init_session_state
from auth_utils import require_authentication
from config import API_BASE_URL
import json

init_session_state()
require_authentication()

def bulk_tag_files(urls, tags, operation):
    """Calls the bulk-tag API endpoint."""
    api_url = f"{API_BASE_URL}/bulk-tag"
    
    # Convert string inputs to lists
    url_list = [url.strip() for url in urls.split('\n') if url.strip()]
    tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
    
    if not url_list or not tag_list:
        st.warning("Please provide at least one URL and one Tag.")
        return

    payload = {
        "url": url_list,
        "operation": 1 if operation == "Add" else 0, # 1 for add, 0 for remove
        "tags": tag_list
    }

    with st.spinner("Applying tags..."):
        try:
            response = requests.post(api_url, json=payload)
            response.raise_for_status()
            st.success("Tags updated successfully!")
            st.json(response.json())
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {e.response.text}")
        except Exception as e:
            st.error(f"An error occurred: {e}")

# --- Main Page UI ---
st.header("🏷️ Bulk Tag Management")
st.info("Manually add or remove tags for multiple files at once.")

urls = st.text_area(
    "File S3 URLs (one per line)",
    placeholder="s3://team99-uploaded-files/thumbnails/pigeon_2.jpg\ns3://team99-uploaded-files/thumbnails/sparrow_1.jpg"
)

tags = st.text_input(
    "Tags (comma-separated)",
    placeholder="Crow,1, Sparrow,2"
)

operation = st.radio("Operation", ("Add", "Remove"))

if st.button("Apply Changes", type="primary"):
    bulk_tag_files(urls, tags, operation)