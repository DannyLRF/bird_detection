# pages/4_🏷️_Manage_Tags.py (Corrected Version)
import streamlit as st
import requests
from auth import authenticate_user, add_logout_button # Import the new functions
from config import API_BASE_URL

# --- Authentication Check ---
authenticate_user()
add_logout_button()
headers = {"Authorization": f"Bearer {st.session_state['id_token']}"}

# --- Page-specific Functions ---
def bulk_tag_manager():
    st.markdown("""
    - 🔗 Enter one or more S3 thumbnail URLs (comma-separated)
    - ➕ Add: requires `Tag,Count` (e.g., Crow,1)
    - ➖ Remove: just `Tag` (count ignored)
    """)

    # Inputs
    url_input = st.text_area(
        "S3 Thumbnail URLs (comma-separated)",
        placeholder="s3://team99-uploaded-files/thumbnails/pigeon_2.jpg"
    )

    operation = st.radio("Operation", options=["Add", "Remove"], horizontal=True)
    op_code = 1 if operation == "Add" else 0

    tags_input = st.text_area(
        "Tags",
        placeholder="e.g., Crow,1\nSparrow,2" if op_code == 1 else "e.g., Crow\nSparrow"
    )

    if st.button("🛠️ Submit Bulk Tag Update", use_container_width=True):
        # Parse inputs
        urls = [u.strip() for u in url_input.split(",") if u.strip()]
        tags = [t.strip() for t in tags_input.split("\n") if t.strip()]

        if not urls or not tags:
            st.warning("Please provide both URLs and tags.")
            return

        payload = {
            "url": urls,
            "operation": op_code,
            "tags": tags
        }

        st.write("📤 **Payload Preview**")
        st.json(payload)

        try:
            response = requests.post(
                f"{API_BASE_URL}/bulk-tag",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()
            st.success("✅ Bulk tag operation completed successfully.")
            st.json(result)
        except Exception as e:
            st.error(f"API error: {e}")
            st.error(getattr(e.response, "text", None))

st.header("🏷️ Bulk Tag Management")
st.info("Manually add or remove tags for multiple files at once.")
bulk_tag_manager()