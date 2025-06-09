# streamlit_app.py (Complete Updated Version)
import streamlit as st
from auth import authenticate_user, add_logout_button

# Basic page configuration
st.set_page_config(
    page_title="Bird Tagging System",
    page_icon="🕊️",
    layout="wide"
)

# Use the centralized authentication function.
# If the user is not logged in, it will display the login page and stop execution.
authenticate_user()

# Add the logout button to the sidebar.
# This also safely displays the user's name.
add_logout_button()

# --- Main Page Content ---
# This section is only reached if the user is successfully authenticated.

st.title("🕊️ Bird Tagging System")

# Use .get() for safe access to the user_name to prevent errors
user_name = st.session_state.get('user_name', 'Guest')
st.header(f"Welcome back, {user_name}!")

st.markdown("---")
st.subheader("🚀 Main Features")

# First row of features
col1, col2 = st.columns(2)

with col1:
    st.info("**📤 Upload Files**\n\nUpload bird images, videos, or audio files for AI analysis.")
    if st.button("Go to Upload", use_container_width=True):
        st.switch_page("pages/1_📤_Upload.py")

with col2:
    st.info("**🔍 Search Files**\n\nFind your processed files by species name or tags.")
    if st.button("Go to Search", use_container_width=True):
        st.switch_page("pages/2_🔍_Search.py")

# Second row of features
col3, col4 = st.columns(2)

with col3:
    st.info("**🚫 Delete Files**\n\nDelete files by URLs from the database.")
    if st.button("Delete Files", use_container_width=True):
        st.switch_page("pages/3_🚫_Delete.py")

with col4:
    st.info("**🏷️ Manage Tags**\n\nBulk add or remove tags from your uploaded files.")
    if st.button("Manage Tags", use_container_width=True):
        st.switch_page("pages/4_🏷️_Manage_Tags.py")

# Third row of features
col5, = st.columns(1)
with col5:
    st.info("**🔔 Subscribe to Tags**\n\nGet email notifications for specific bird uploads.")
    if st.button("Go to Subscribe", use_container_width=True):
        st.switch_page("pages/5_🔔_Subscribe.py")

st.markdown("---")

# Quick information section
st.subheader("ℹ️ Quick Information")

info_col1, info_col2 = st.columns(2)

with info_col1:
    st.success("**System Status**\n\n✅ All systems operational\n\n🤖 AI detection online")

with info_col2:
    st.warning("**Usage Tips**\n\n📤 Supported: JPG, PNG, MP4, WAV, MP3\n\n🔍 Use commas for multiple species")