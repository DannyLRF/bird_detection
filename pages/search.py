# pages/2_🔍_Search.py
import streamlit as st
import requests
from helpers import init_session_state
from auth import check_authentication
from config import API_BASE_URL # import API URL

init_session_state()

def search_files_by_species(query):
    """Search for files by species name by calling the /species endpoint."""
    if not query.strip():
        st.warning("Please enter a species to search for.")
        return

    st.session_state.search_results = [] # Clear previous results
    api_url = f"{API_BASE_URL}/species"
    # The API expects a list of lists, e.g., [["crow"], ["pigeon"]]
    payload = [[tag.strip() for tag in query.split(',')]]

    with st.spinner(f"Searching for files with '{query}'..."):
        try:
            response = requests.post(api_url, json=payload)
            response.raise_for_status()
            results = response.json()
            # The API returns a dictionary with a list of presigned URLs
            st.session_state.search_results = results.get("matched_files", [])
            st.success(f"Found {len(st.session_state.search_results)} result(s).")
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {e.response.text}")
        except Exception as e:
            st.error(f"An error occurred: {e}")


def show_search_results():
    """Display search results (images/videos) from URLs."""
    if not st.session_state.get('search_results'):
        st.info("Your search results will appear here.")
        return

    st.subheader("Search Results")
    
    # Create columns to display results in a grid
    cols = st.columns(3)
    results = st.session_state.search_results
    
    for i, url in enumerate(results):
        with cols[i % 3]:
            try:
                # Check file extension to decide how to display
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
if not check_authentication():
    st.warning("Please log in to access this page.")
    st.stop()

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