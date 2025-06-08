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
    Display search results from a list that may contain dictionaries or strings.
    This function is designed to be robust against changes in the API response format.
    """
    # Get search results from the session state, default to an empty list to prevent errors.
    search_results = st.session_state.get('search_results', [])
    
    # If there are no results, display an informational message and exit.
    if not search_results:
        st.info("Your search results will appear here.")
        return

    st.subheader("Search Results")
    st.write(f"**Total Results:** {len(search_results)}")
    
    # --- IMPORTANT: Determine the key for the URL ---
    # We inspect the first result item to guess the key that holds the URL string.
    # The API might return something like {'presigned_url': '...'} or {'link': '...'}.
    # This key name is needed to extract the URL from the dictionary.
    
    first_item = search_results[0]
    url_key = None # This variable will store the name of the key (e.g., 'presigned_url').

    # Check if the items in the result list are dictionaries.
    if isinstance(first_item, dict):
        # A list of common possible key names for a URL.
        possible_keys = ['presigned_url', 'url', 'annotated_s3_url', 'link', 'matched_files']
        for key in possible_keys:
            # If a key exists in the dictionary and its value is a string, we assume it's our URL key.
            if key in first_item and isinstance(first_item[key], str):
                url_key = key
                break # Stop searching once we've found a valid key.
        
        # If no valid URL key was found after checking all possibilities, show an error.
        if not url_key:
            st.error("Could not automatically determine the URL key in the search result dictionary.")
            st.write("Please check the structure of a single result item below to find the correct key:")
            st.json(first_item) # Display the dictionary structure to help the user debug.
            return
    
    # Create a 3-column layout for displaying results.
    cols = st.columns(3)
    
    # Iterate through each item in the search results.
    for i, result_item in enumerate(search_results):
        # Place each result in one of the three columns in a repeating pattern.
        with cols[i % 3]:
            st.write(f"**File {i+1}:**")
            
            url = None # Initialize url variable for the current item.

            # Extract the URL string from the result item.
            if isinstance(result_item, dict) and url_key:
                # If the item is a dictionary, get the URL using the key we identified.
                url = result_item.get(url_key)
            elif isinstance(result_item, str):
                # For backward compatibility, if the item is just a string, use it directly.
                url = result_item
            else:
                # If the format is unexpected, show a warning and the item's content.
                st.warning(f"Skipping item {i+1} due to unknown format.")
                st.write(result_item)
                continue # Skip to the next item in the loop.

            # If no URL could be extracted, show a warning and skip.
            if not url:
                st.warning(f"No URL found for item {i+1}.")
                continue

            # Display the raw URL string.
            st.code(url, language=None)
            
            # This try-except block handles potential errors when rendering the media file.
            try:
                # Now, call .lower() on the 'url' STRING, not the dictionary.
                if ".mp4" in url.lower() or ".mov" in url.lower():
                    st.video(url)
                elif ".jpg" in url.lower() or ".jpeg" in url.lower() or ".png" in url.lower():
                    st.image(url, use_column_width=True)
                elif ".wav" in url.lower() or ".mp3" in url.lower():
                    st.audio(url)
                else:
                    # If the file type is not media, display a simple link.
                    st.write(f"[Link to file]({url})")
            except Exception as e:
                # If rendering fails, display the error message.
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