import streamlit as st
import requests
import json

st.set_page_config(page_title="🚫 Delete")

st.title("🚫 Delete")

st.markdown(
    """
    Use this page to delete one or more uploaded files from the system.
    Paste the S3 or HTTP URLs of the files you want to delete, then click **Submit for Deletion**.
    """
)

# Session state for storing URLs
if "url_fields" not in st.session_state:
    st.session_state.url_fields = [""]
if "delete_response" not in st.session_state:
    st.session_state.delete_response = None

# Function to dynamically add more URL inputs
def add_url_field():
    st.session_state.url_fields.append("")

# Function to submit the URLs
def submit_urls():
    valid_urls = [url for url in st.session_state.url_fields if url.strip()]
    if not valid_urls:
        st.warning("Please enter at least one valid URL.")
        return

    # Prepare the request payload
    payload = {"urls": valid_urls}

    try:
        # Replace this with your actual DELETE endpoint
        api_url = "https://your-api-gateway-url.com/delete"

        # Send DELETE request
        response = requests.delete(api_url, data=json.dumps(payload))

        if response.status_code == 200:
            st.success("Files successfully deleted.")
        else:
            st.error(f"Server responded with status code {response.status_code}: {response.text}")
    except Exception as e:
        st.error(f"Error sending request: {str(e)}")


st.subheader("File URLs to Delete")

# Input boxes for each URL
for i in range(len(st.session_state.url_fields)):
    st.session_state.url_fields[i] = st.text_input(f"URL {i+1}", st.session_state.url_fields[i], key=f"url_{i}")

# Add new URL input
st.button("➕ Add URL", on_click=add_url_field)

# Submit for deletion
st.button("🚫 Submit for Deletion", on_click=submit_urls)
