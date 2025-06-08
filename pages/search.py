# pages/2_🔍_Search.py
import streamlit as st
import pandas as pd
from helpers import init_session_state, get_file_type_display, generate_mock_search_results
from auth import check_authentication

init_session_state()

def search_files(query, file_type, confidence):
    """Search for files based on criteria."""
    if not query.strip():
        st.warning("Please enter a search term.")
        return
    
    with st.spinner("Searching..."):
        # Combine existing results with mock results for demo
        all_results = st.session_state.upload_results + generate_mock_search_results(query)
        
        # Filter by species query
        search_results = [r for r in all_results if query.lower() in r['species'].lower()]

        # Further filtering logic...
        # (Add file_type and confidence filtering here if needed)
        
        st.session_state.search_results = search_results
    st.success(f"Found {len(search_results)} result(s).")

def show_search_results():
    """Display search results in a table and detailed view."""
    if not st.session_state.search_results:
        st.info("Use the search function to find files.")
        return

    st.subheader("Search Results")
    df_data = [
        {
            'File Name': r['file_name'],
            'Species': r['species'],
            'Confidence': f"{r['confidence']:.1%}",
            'Count': r['count'],
            'Type': get_file_type_display(r['file_type']),
        } for r in st.session_state.search_results
    ]
    st.dataframe(pd.DataFrame(df_data), use_container_width=True)

# --- Main Page UI ---
if not check_authentication():
    st.warning("Please log in to access this page.")
    st.stop()

st.header("🔍 Search Files")

col1, col2 = st.columns([2, 1])
with col1:
    search_query = st.text_input("Search by species name", placeholder="e.g., crow, pigeon")
with col2:
    confidence_filter = st.selectbox(
        "Minimum Confidence",
        ["Any", "High (90%+)", "Medium (70%+)"]
    )

if st.button("🔍 Search", type="primary", use_container_width=True):
    search_files(search_query, "All", confidence_filter)

if st.session_state.search_results:
    if st.button("🗑️ Clear Search"):
        st.session_state.search_results = []
        st.rerun()

st.markdown("---")
show_search_results()