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
    """Display search results (images/videos) from URLs."""
    if not st.session_state.get('search_results'):
        st.info("Your search results will appear here.")
        return

    st.subheader("Search Results")
    results = st.session_state.search_results
    st.write(f"**Total Results:** {len(results)}")
    
    cols = st.columns(3)
    
    for i, url in enumerate(results):
        with cols[i % 3]:
            st.write(f"**File {i+1}:**")
            st.code(url, language=None)
            
            try:
                if ".mp4" in url.lower() or ".mov" in url.lower():
                    st.video(url)
                elif ".jpg" in url.lower() or ".jpeg" in url.lower() or ".png" in url.lower():
                    st.image(url, use_column_width=True)
                elif ".wav" in url.lower() or ".mp3" in url.lower():
                    st.audio(url)
                else:
                    st.write(f"[Link to file]({url})")
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