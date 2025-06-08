# pages/3_📊_Statistics.py (New Version)
import streamlit as st
import pandas as pd
from auth import authenticate_user, add_logout_button # Import the new functions
from config import API_BASE_URL

# --- Authentication Check ---
authenticate_user()
add_logout_button()

# --- Page-specific Functions ---
def show_statistics():
    """Display overall statistics."""
    # Note: This page relies on `st.session_state.upload_results`.
    # You may need a mechanism to fetch this data from your backend if it's not already in the session.
    results = st.session_state.get('upload_results', [])
    if not results:
        st.info("Upload files to see statistics. This page currently shows data from the current session's uploads.")
        return

    st.subheader("Overall Statistics")
    
    species_count = {}
    for r in results:
        species_count[r['species']] = species_count.get(r['species'], 0) + r.get('count', 0)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Files Uploaded (in session)", len(results))
    col2.metric("Total Detections (in session)", sum(r.get('count', 0) for r in results))
    col3.metric("Unique Species (in session)", len(species_count))

    st.markdown("---")
    st.subheader("Distribution Charts")
    
    if species_count:
        species_df = pd.DataFrame(list(species_count.items()), columns=['Species', 'Count'])
        st.bar_chart(species_df.set_index('Species'))

# --- Main Page UI ---
st.header("📊 Statistics")
show_statistics()