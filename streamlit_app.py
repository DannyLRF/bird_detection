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

def main():
    """Main function to handle page routing."""
    # Initialize session state across all pages
    init_session_state()

    # Handle the authentication callback from Cognito
    handle_cognito_callback()

    # Check if user is authenticated
    if not check_authentication():
        # If not authenticated, show the login page
        show_login_page()
    else:
        # If authenticated, show a welcome message on the home page
        st.title("🕊️ Bird Tagging System")
        st.header(f"Welcome, {st.session_state.user_name}!")
        st.markdown("---")
        st.info("Select a page from the sidebar to start.")
        
        # Display user info and logout button in the sidebar
        with st.sidebar:
            st.markdown("---")
            st.write(f"Logged in as: **{st.session_state.user_name}**")
            if st.button("🚪 Logout"):
                st.session_state.authenticated = False
                st.session_state.user_name = ''
                st.session_state.id_token = None
                st.session_state.access_token = None
                st.success("You have been logged out.")
                time.sleep(1)
                st.rerun()

if __name__ == "__main__":
    main()