# streamlit_app.py
import streamlit as st
import time
from auth import handle_cognito_callback, show_login_page, check_authentication
from helpers import init_session_state

# Page Configuration
st.set_page_config(
    page_title="Bird Tagging System",
    page_icon="🕊️",
    layout="wide"
)

def main():
    """Main function to handle page routing"""
    # Initialize session state
    init_session_state()

    # Handle authentication callback
    handle_cognito_callback()

    # Check authentication
    if not check_authentication():
        show_login_page()
    else:
        # Display main page
        st.title("🕊️ Bird Tagging System")
        st.header(f"Welcome, {st.session_state.user_name}!")
        
        st.markdown("---")
        
        # Main features
        st.subheader("🚀 Main Features")
        
        # First row
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("**📤 Upload Files**\n\nUpload bird images, videos, or audio files for AI analysis")
            if st.button("Go to Upload", key="upload_btn", use_container_width=True):
                st.switch_page("pages/1_📤_Upload.py")
                
        with col2:
            st.info("**🔍 Search Files**\n\nFind your processed files by species name or tags")
            if st.button("Go to Search", key="search_btn", use_container_width=True):
                st.switch_page("pages/2_🔍_Search.py")
        
        # Second row
        col3, col4 = st.columns(2)
        
        with col3:
            st.info("**📊 View Statistics**\n\nAnalyze upload history and detection results")
            if st.button("View Statistics", key="stats_btn", use_container_width=True):
                st.switch_page("pages/3_📊_Statistics.py")
                
        with col4:
            st.info("**🏷️ Manage Tags**\n\nBulk add or remove tags from uploaded files")
            if st.button("Manage Tags", key="tags_btn", use_container_width=True):
                st.switch_page("pages/4_🏷️_Manage_Tags.py")
        
        st.markdown("---")
        
        # Quick info
        st.subheader("ℹ️ Quick Information")
        
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.success("**System Status**\n\n✅ All systems operational\n\n🤖 AI detection online")
            
        with info_col2:
            st.warning("**Usage Tips**\n\n📤 Supported: JPG, PNG, MP4, WAV, MP3\n\n🔍 Use commas for multiple species")
        
        # Sidebar content
        with st.sidebar:
            st.header("User Info")
            st.write(f"**Logged in as:**")
            st.write(st.session_state.user_name)
            
            st.markdown("---")
            
            st.header("Quick Actions")
            if st.button("🔄 Refresh Page"):
                st.rerun()
                
            if st.button("🚪 Logout"):
                # Clear session
                for key in ['authenticated', 'user_name', 'id_token', 'access_token']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("Logged out successfully!")
                time.sleep(1)
                st.rerun()

if __name__ == "__main__":
    main()