# auth_utils.py
import streamlit as st
from auth import check_authentication

def hide_sidebar():
    """Hide the sidebar using CSS when user is not authenticated."""
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

def require_authentication():
    """
    Decorator function to require authentication for pages.
    Call this at the beginning of each page that requires login.
    """
    if not check_authentication():
        hide_sidebar()
        st.warning("🔒 **Access Denied**")
        st.error("Please log in to access this page.")
        
        st.markdown("---")
        st.markdown("### 🏠 Return to Login")
        st.info("Click the button below to return to the main page and log in.")
        
        if st.button("🏠 Go to Home Page", type="primary", use_container_width=True):
            st.switch_page("streamlit_app.py")
        
        st.stop()  # Stop execution of the rest of the page
    
    # If authenticated, ensure sidebar is visible
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            display: block !important;
        }
    </style>
    """, unsafe_allow_html=True)