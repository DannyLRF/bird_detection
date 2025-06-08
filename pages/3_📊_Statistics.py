# pages/3_📊_Statistics.py
import streamlit as st
import pandas as pd
import requests
from helpers import init_session_state
from auth_utils import require_authentication 
from config import API_BASE_URL

init_session_state()
require_authentication()

def show_statistics():
    """Display overall statistics."""
    results = st.session_state.upload_results
    if not results:
        st.info("Upload files to see statistics.")
        return

    st.subheader("Overall Statistics")
    
    species_count = {}
    for r in results:
        species_count[r['species']] = species_count.get(r['species'], 0) + r['count']

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Files Uploaded", len(results))
    col2.metric("Total Detections", sum(r['count'] for r in results))
    col3.metric("Unique Species", len(species_count))

    st.markdown("---")
    st.subheader("Distribution Charts")
    
    # Species Distribution
    if species_count:
        species_df = pd.DataFrame(list(species_count.items()), columns=['Species', 'Count'])
        st.bar_chart(species_df.set_index('Species'))

# --- Main Page UI ---
if not check_authentication():
    st.warning("Please log in to access this page.")
    st.stop()

st.header("📊 Statistics")
show_statistics()