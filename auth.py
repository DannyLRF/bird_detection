# auth.py (Improved Version with Debugging)
import streamlit as st
import requests
import urllib.parse
import jwt
from config import AWS_CONFIG, REDIRECT_URI

def _initialize_session_state():
    """
    Ensures all required session state variables are initialized.
    This is a private function as it should only be called within authenticate_user.
    """
    defaults = {
        'authenticated': False,
        'user_name': 'Guest',
        'id_token': None,
        'access_token': None,
        'auth_error': None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
            
    # 添加调试信息（可在生产环境中移除）
    if st.session_state.get('debug_mode', False):
        st.sidebar.write("🔍 Debug: Session State")
        st.sidebar.write(f"- Authenticated: {st.session_state.authenticated}")
        st.sidebar.write(f"- User: {st.session_state.user_name}")
        st.sidebar.write(f"- Has ID Token: {bool(st.session_state.id_token)}")

def _build_cognito_auth_url():
    """Builds the Cognito authorization URL."""
    params = {
        'response_type': 'code',
        'client_id': AWS_CONFIG['cognito']['app_client_id'],
        'redirect_uri': REDIRECT_URI,
        'scope': 'openid profile email'
    }
    base_url = f"https://{AWS_CONFIG['cognito']['domain']}/oauth2/authorize"
    return f"{base_url}?{urllib.parse.urlencode(params)}"

def _handle_cognito_callback():
    """
    Handles the authentication code from the Cognito callback and exchanges it for a token.
    Executes only if a 'code' is in the URL params and the user is not yet authenticated.
    """
    auth_code = st.query_params.get('code')
    if auth_code and not st.session_state.authenticated:
        try:
            token_endpoint = f"https://{AWS_CONFIG['cognito']['domain']}/oauth2/token"
            data = {
                'grant_type': 'authorization_code',
                'client_id': AWS_CONFIG['cognito']['app_client_id'],
                'code': auth_code,
                'redirect_uri': REDIRECT_URI
            }
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}

            response = requests.post(token_endpoint, data=urllib.parse.urlencode(data), headers=headers)
            response.raise_for_status()

            tokens = response.json()
            st.session_state.id_token = tokens.get('id_token')
            st.session_state.access_token = tokens.get('access_token')

            # Decode the ID token to get user info
            decoded = jwt.decode(st.session_state.id_token, options={"verify_signature": False})
            st.session_state.user_name = decoded.get('email') or decoded.get('cognito:username') or 'User'
            st.session_state.authenticated = True
            st.session_state.auth_error = None

            # Clear the auth code from the URL
            st.query_params.clear()
            
            # 强制重新运行以确保状态更新
            st.rerun()

        except requests.exceptions.RequestException as e:
            error_msg = f"Authentication failed: {e.response.text if hasattr(e, 'response') else str(e)}"
            st.session_state.auth_error = error_msg
            st.session_state.authenticated = False
        except Exception as e:
            st.session_state.auth_error = f"An unknown authentication error occurred: {e}"
            st.session_state.authenticated = False

def _show_login_page():
    """
    Displays the login interface and hides the sidebar.
    """
    # Hide sidebar
    st.markdown("""
        <style>
        section[data-testid='stSidebar'] { display: none !important; }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🕊️ Bird Tagging System")
    st.markdown("### Please log in to continue")
    st.markdown("---")

    # Display auth error if it exists
    if st.session_state.auth_error:
        st.error(st.session_state.auth_error)

    # 显示当前的 Redirect URI（调试用）
    with st.expander("🔧 Debug Information"):
        st.info(f"Redirect URI: {REDIRECT_URI}")
        st.info(f"Current URL: {st.get_option('browser.serverAddress')}")

    login_url = _build_cognito_auth_url()
    st.link_button("🔐 Sign in with AWS", login_url, use_container_width=True, type="primary")
    st.info("You will be redirected to AWS Cognito for secure authentication.")

def authenticate_user():
    """
    A centralized function to handle authentication for all pages.
    
    Returns:
        bool: True if the user is authenticated, False otherwise.
    """
    _initialize_session_state()
    _handle_cognito_callback()

    if not st.session_state.get('authenticated', False):
        _show_login_page()
        st.stop()
        return False
    else:
        # Ensure the sidebar is visible when logged in
        st.markdown("""
            <style>
            section[data-testid='stSidebar'] { display: block !important; }
            </style>
        """, unsafe_allow_html=True)
        return True

def add_logout_button():
    """
    Adds a logout button to the sidebar with safer state handling.
    """
    with st.sidebar:
        st.header("👤 User Info")
        
        user_name = st.session_state.get('user_name', 'Guest')
        st.write(f"**Welcome, {user_name}**")
        
        # 添加认证状态指示器
        if st.session_state.get('authenticated', False):
            st.success("✅ Authenticated")
        else:
            st.error("❌ Not Authenticated")
            
        st.markdown("---")
        
        logout_params = {
            'client_id': AWS_CONFIG['cognito']['app_client_id'],
            'logout_uri': REDIRECT_URI,
        }
        logout_url = f"https://{AWS_CONFIG['cognito']['domain']}/logout?{urllib.parse.urlencode(logout_params)}"
        
        if st.button("🚪 Logout", use_container_width=True):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            # Redirect to logout URL
            st.write(f'<meta http-equiv="refresh" content="0; url={logout_url}">', unsafe_allow_html=True)

def toggle_debug_mode():
    """Toggle debug mode for troubleshooting"""
    with st.sidebar:
        st.markdown("---")
        if st.checkbox("🐛 Debug Mode", value=st.session_state.get('debug_mode', False)):
            st.session_state.debug_mode = True
        else:
            st.session_state.debug_mode = False