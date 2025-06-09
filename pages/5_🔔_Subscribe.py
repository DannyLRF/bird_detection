import streamlit as st
import requests
from auth import authenticate_user, add_logout_button # Import the new functions

# --- Authentication Check ---
# This single line handles the authentication check and displays the login page if needed.
authenticate_user()
# Add the logout button to the sidebar to maintain a consistent UI.
add_logout_button()

st.header("🔔 Subscribe")

st.markdown("Receive email alerts when new images containing your desired tags are uploaded to our database.")

# Input email
email = st.text_input("Your email address", placeholder="you@example.com")

# Tag inputs
st.markdown("### Bird Tags")
tag_inputs = []
default_tag_count = st.session_state.get("tag_count", 1)

# Initialize session state for dynamic tag fields
if "tags" not in st.session_state:
    st.session_state.tags = ["" for _ in range(default_tag_count)]

def add_tag_field():
    st.session_state.tags.append("")

# Display all tag fields
for i, tag in enumerate(st.session_state.tags):
    st.session_state.tags[i] = st.text_input(
        f"Tag {i+1}",
        value=tag,
        key=f"tag_{i}",
        label_visibility="collapsed",
        placeholder="e.g. Sparrow"
    )

st.button("Add Bird Tag", on_click=add_tag_field)

# Submit
if st.button("Subscribe"):
    clean_tags = [t.strip() for t in st.session_state.tags if t.strip()]
    if not email or not clean_tags:
        st.error("Please provide both an email address and at least one bird tag.")
    else:
        try:
            response = requests.post(
                "https://d2u7y2aieb.execute-api.ap-southeast-2.amazonaws.com/dev/api/subscribe",
                json={
                    "email": email,
                    "birdTag": clean_tags
                }
            )
            if response.status_code == 200:
                st.success("Subscription request sent! Please confirm via the email sent to your email.")
            else:
                st.error(f"Error: {response.status_code}\n{response.text}")
        except Exception as e:
            st.error(f"Request failed: {e}")
