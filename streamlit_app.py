# streamlit_app.py
import streamlit as st
import time
from auth import handle_cognito_callback, show_login_page, check_authentication
from helpers import init_session_state

# --- Page Configuration ---
st.set_page_config(
    page_title="Bird Tagging System",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def hide_sidebar():
    """Hide the sidebar using CSS when user is not authenticated."""
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

def show_sidebar():
    """Show the sidebar when user is authenticated."""
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            display: block !important;
        }
    </style>
    """, unsafe_allow_html=True)

def main():
    """Main function to handle page routing."""
    # Initialize session state across all pages
    init_session_state()

    # Handle the authentication callback from Cognito
    handle_cognito_callback()

    # Check if user is authenticated
    if not check_authentication():
        # Hide sidebar when not authenticated
        hide_sidebar()
        
        # If not authenticated, show the login page
        show_login_page()
    else:
        # Show sidebar when authenticated
        show_sidebar()
        
        # If authenticated, show a welcome message on the home page
        st.title("🕊️ Bird Tagging System")
        st.header(f"Welcome back, {st.session_state.user_name}! 👋")
        
        # Hero section with overview
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; padding: 20px; background-color: #f0f8ff; border-radius: 10px; margin: 20px 0;">
            <h3>🎯 AI-Powered Bird Detection & Tagging</h3>
            <p style="font-size: 18px; color: #666;">Upload your bird media files and let our AI identify species automatically</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Main action cards in 2x2 grid
        st.markdown("### 🚀 Main Features")
        
        # First row - Primary actions
        col1, col2 = st.columns(2, gap="large")
        
        with col1:
            with st.container():
                st.markdown("""
                <div style="padding: 20px; border: 2px solid #4CAF50; border-radius: 10px; text-align: center; background-color: #f8fff8;">
                    <h4>📤 Upload Files</h4>
                    <p>Upload bird images, videos, or audio files for AI analysis</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🚀 Start Upload", key="upload_btn", type="primary", use_container_width=True):
                    st.switch_page("pages/1_📤_Upload.py")
                
        with col2:
            with st.container():
                st.markdown("""
                <div style="padding: 20px; border: 2px solid #2196F3; border-radius: 10px; text-align: center; background-color: #f8fbff;">
                    <h4>🔍 Search Files</h4>
                    <p>Find your processed files by species name or tags</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🔍 Search Now", key="search_btn", type="primary", use_container_width=True):
                    st.switch_page("pages/2_🔍_Search.py")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Second row - Secondary actions
        col3, col4 = st.columns(2, gap="large")
        
        with col3:
            with st.container():
                st.markdown("""
                <div style="padding: 20px; border: 2px solid #FF9800; border-radius: 10px; text-align: center; background-color: #fffbf0;">
                    <h4>📊 View Statistics</h4>
                    <p>Analyze your upload history and detection results</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("📊 View Stats", key="stats_btn", use_container_width=True):
                    st.switch_page("pages/3_📊_Statistics.py")
                
        with col4:
            with st.container():
                st.markdown("""
                <div style="padding: 20px; border: 2px solid #9C27B0; border-radius: 10px; text-align: center; background-color: #fdf8ff;">
                    <h4>🏷️ Manage Tags</h4>
                    <p>Bulk add or remove tags from your uploaded files</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🏷️ Manage Tags", key="tags_btn", use_container_width=True):
                    st.switch_page("pages/4_🏷️_Manage_Tags.py")
        
        # Quick tips section
        st.markdown("---")
        st.markdown("### 💡 Quick Tips")
        
        tip_col1, tip_col2, tip_col3 = st.columns(3)
        
        with tip_col1:
            st.info("**📤 Upload Tips**\n\nSupported formats: JPG, PNG, MP4, WAV, MP3")
            
        with tip_col2:
            st.info("**🔍 Search Tips**\n\nUse comma-separated species names for multiple searches")
            
        with tip_col3:
            st.info("**🏷️ Tag Tips**\n\nUse S3 URLs from search results for bulk tagging")
        
        # Display user info and logout button in the sidebar
        with st.sidebar:
            # User profile section
            st.markdown("### 👤 User Profile")
            st.markdown(f"""
            <div style="padding: 15px; background-color: #f0f2f6; border-radius: 10px; margin-bottom: 20px;">
                <div style="text-align: center;">
                    <div style="font-size: 48px; margin-bottom: 10px;">👤</div>
                    <div style="font-weight: bold; color: #333;">{st.session_state.user_name}</div>
                    <div style="color: #666; font-size: 12px;">Logged In</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Quick navigation
            st.markdown("### 🧭 Quick Navigation")
            if st.button("📤 Upload", key="sidebar_upload", use_container_width=True):
                st.switch_page("pages/1_📤_Upload.py")
            if st.button("🔍 Search", key="sidebar_search", use_container_width=True):
                st.switch_page("pages/2_🔍_Search.py")
            if st.button("📊 Statistics", key="sidebar_stats", use_container_width=True):
                st.switch_page("pages/3_📊_Statistics.py")
            if st.button("🏷️ Manage Tags", key="sidebar_tags", use_container_width=True):
                st.switch_page("pages/4_🏷️_Manage_Tags.py")
            
            st.markdown("---")
            
            # System actions
            st.markdown("### ⚙️ System")
            if st.button("🔄 Refresh", key="refresh_btn", use_container_width=True):
                st.rerun()
                
            if st.button("🚪 Logout", key="logout_btn", type="secondary", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.user_name = ''
                st.session_state.id_token = None
                st.session_state.access_token = None
                st.success("You have been logged out.")
                time.sleep(1)
                st.rerun()
                
            # Footer info
            st.markdown("---")
            st.markdown("""
            <div style="text-align: center; color: #666; font-size: 12px;">
                <div>🕊️ Bird Tagging System</div>
                <div>v1.0.0</div>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()