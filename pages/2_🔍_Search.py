# pages/2_🔍_Search.py (New Version)
import streamlit as st
import requests
import json
from auth import authenticate_user, add_logout_button # Import the new functions
from config import API_BASE_URL

# --- Authentication Check ---
# This single line handles the authentication check and displays the login page if needed.
authenticate_user()
# Add the logout button to the sidebar to maintain a consistent UI.
add_logout_button()

# --- Page-specific Functions ---
def search_files_by_species(query):
    """Search for files by species name by calling the /species endpoint."""
    if not query.strip():
        st.warning("Please enter a species to search for.")
        return

    st.session_state.search_results = [] # Clear previous results
    api_url = f"{API_BASE_URL}/species"
    # The API expects a list of lists, e.g., [["crow"], ["pigeon"]]
    payload = [[tag.strip() for tag in query.split(',')]]

    # Debug information
    st.write(f"🔍 **Debug Info:**")
    st.write(f"- API URL: `{api_url}`")
    st.write(f"- Payload: `{payload}`")

    with st.spinner(f"Searching for files with '{query}'..."):
        try:
            response = requests.post(api_url, json=payload)
            st.write(f"- Response Status: `{response.status_code}`")
            response.raise_for_status()
            results = response.json()
            
            st.write(f"- Raw Response: `{json.dumps(results, indent=2)}`")
            
            matched_files = results.get("matched_files", [])
            st.session_state.search_results = matched_files
            
            st.write(f"- Matched Files Count: `{len(matched_files)}`")
            st.success(f"Found {len(st.session_state.search_results)} result(s).")
            
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                st.error(f"Response Text: {e.response.text}")
                st.error(f"Response Status: {e.response.status_code}")
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.error(f"Error type: {type(e).__name__}")

def show_search_results():
    """
    Display search results, handling different URL formats and potential errors.
    """
    search_results = st.session_state.get('search_results', [])
    if not search_results:
        st.info("Your search results will appear here.")
        return

    st.subheader("Search Results")
    st.write(f"**Total Results:** {len(search_results)}")
    
    first_item = search_results[0]
    url_key = None
    if isinstance(first_item, dict):
        possible_keys = ['annotated_url', 'original_url', 'thumbnail_url', 'url', 'presigned_url', 'link']
        for key in possible_keys:
            if key in first_item and isinstance(first_item[key], str):
                url_key = key
                break
        if not url_key:
            st.error("Could not automatically determine the URL key in the search result dictionary.")
            st.json(first_item)
            return
    
    cols = st.columns(3)
    
    for i, result_item in enumerate(search_results):
        with cols[i % 3]:
            st.write(f"**File {i+1}:**")
            
            url = None
            if isinstance(result_item, dict) and url_key:
                url = result_item.get(url_key)
            elif isinstance(result_item, str):
                url = result_item
            else:
                st.warning(f"Skipping item {i+1} due to unknown format.")
                st.write(result_item)
                continue

            if not url:
                st.warning(f"No URL found for item {i+1}.")
                continue

            st.code(url, language=None)
            
            # FIX 3: Check if the URL is an s3:// URI before trying to display it.
            if url.startswith('s3://'):
                st.error("Cannot display file. Received an S3 URI instead of an accessible HTTPS URL from the API.")
                continue

            try:
                if ".mp4" in url.lower() or ".mov" in url.lower():
                    st.video(url)
                elif ".jpg" in url.lower() or ".jpeg" in url.lower() or ".png" in url.lower():
                    # FIX 2: Use use_container_width instead of use_column_width.
                    st.image(url, use_container_width=True)
                elif ".wav" in url.lower() or ".mp3" in url.lower():
                    st.audio(url)
                else:
                    # FIX 1: Use st.markdown to render the link correctly.
                    st.markdown(f"[Link to file]({url})")
            except Exception as e:
                st.error(f"Could not display file: {e}")

# --- Main Page UI ---
st.header("🔍 Search Files")
search_query = st.text_input(
    "Search by species name",
    placeholder="e.g., crow, pigeon (comma-separated for multiple)"
)

if st.button("🔍 Search by Species", type="primary", use_container_width=True):
    search_files_by_species(search_query)

if st.session_state.get('search_results'):
    if st.button("🗑️ Clear Search Results"):
        st.session_state.search_results = []
        st.rerun()

st.markdown("---")
show_search_results()