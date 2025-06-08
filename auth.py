# auth.py
import streamlit as st
import requests
import urllib.parse
import jwt
from config import AWS_CONFIG, REDIRECT_URI

def build_cognito_url():
    """Build Cognito authorization URL."""
    params = {
        'response_type': 'code',
        'client_id': AWS_CONFIG['cognito']['app_client_id'],
        'redirect_uri': REDIRECT_URI,
        'scope': 'openid profile email'
    }
    base_url = f"https://{AWS_CONFIG['cognito']['domain']}/oauth2/authorize"
    return f"{base_url}?{urllib.parse.urlencode(params)}"

def show_login_page():
    """Display the login page UI."""
    st.title("🕊️ Bird Tagging System")
    st.markdown("### Please log in to continue")
    st.markdown("---")
    
    if st.session_state.get('auth_error'):
        st.error(st.session_state['auth_error'])
        st.session_state['auth_error'] = None

    login_url = build_cognito_url()
    st.link_button("🔐 Sign in with AWS", login_url, use_container_width=True)
    st.info("You will be redirected to AWS Cognito for secure authentication.")

def handle_cognito_callback():
    """Handle the callback from Cognito after login attempt."""
    query_params = st.query_params
    if 'code' in query_params and not st.session_state.get('authenticated'):
        auth_code = query_params['code']
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
            
            decoded = jwt.decode(st.session_state.id_token, options={"verify_signature": False})
            st.session_state.user_name = decoded.get('email') or decoded.get('cognito:username') or 'User'
            st.session_state.authenticated = True
            
            # Clear URL query parameters
            st.query_params.clear()

        except requests.exceptions.RequestException as e:
            st.session_state.auth_error = f"Token exchange failed: {e.response.text}"
        except Exception as e:
            st.session_state.auth_error = f"Authentication error: {e}"

def check_authentication():
    """Check if the user is authenticated."""
    return st.session_state.get('authenticated', False)