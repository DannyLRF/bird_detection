import streamlit as st
import requests
import json
import base64
from auth import authenticate_user, add_logout_button
from config import API_BASE_URL

# --- Authentication ---
authenticate_user()
add_logout_button()
headers = {"Authorization": f"Bearer {st.session_state['id_token']}"}

# --- API URLs ---
SPECIES_API = f"{API_BASE_URL}/species"
BIRDS_API = f"{API_BASE_URL}/birds"

# --- Search Functions ---
def search_by_species():
    if "species_conditions" not in st.session_state:
        st.session_state.species_conditions = [[""]]

    st.markdown("Define one or more species conditions. Each group matches files that include **all** tags in that group. Multiple groups will be OR'ed.")

    new_conditions = []
    for idx, group in enumerate(st.session_state.species_conditions):
        st.markdown(f"**Condition {idx+1}**")
        tags_str = ", ".join(group)
        input_val = st.text_input(f"Species tags (comma-separated)", value=tags_str, key=f"species_group_{idx}", placeholder="sparrow, crow")
        tags = [tag.strip() for tag in input_val.split(",") if tag.strip()]
        new_conditions.append(tags)

    st.session_state.species_conditions = new_conditions

    c_add, c_clear = st.columns(2)
    if c_add.button("➕ Add Species Condition Group", key="add_species_group"):
        st.session_state.species_conditions.append([""])
        st.rerun()
    if c_clear.button("♻️ Reset Species Conditions", key="reset_species_group"):
        st.session_state.species_conditions = [[""]]
        for k in list(st.session_state.keys()):
            if k.startswith("species_group_"):
                del st.session_state[k]
        st.rerun()

    if st.button("Search by Species", use_container_width=True, key="search_species_button"):
        payload = [group for group in st.session_state.species_conditions if group]

        if not payload:
            st.warning("Please define at least one condition group with tags.")
            return

        st.write("🔍 **Search by Species Debug**")
        st.json(payload)

        st.session_state.search_results = []
        with st.spinner("Searching by species..."):
            try:
                response = requests.post(SPECIES_API, json=payload, headers=headers)
                response.raise_for_status()
                results = response.json()
                st.session_state.search_results = results.get("matched_files", [])
                st.success(f"Found {len(st.session_state.search_results)} result(s).")
            except Exception as e:
                st.error(f"API error: {e}")
                st.error(getattr(e.response, "text", None))

def search_by_uploaded_file():
    uploaded_file = st.file_uploader(
        "Upload a file (image, audio, or video)",
        type=["jpg", "jpeg", "png", "mp3", "wav", "mp4", "mov"],
        key="similarity_file"
    )

    file_type = st.selectbox(
        "Select file type",
        options=["image", "audio", "video"],
        help="This tells the backend how to process the uploaded file"
    )

    if st.button("🔍 Find Similar Files"):
        if not uploaded_file:
            st.warning("Please upload a file first.")
            return

        # Read and encode file
        file_bytes = uploaded_file.read()
        file_b64 = base64.b64encode(file_bytes).decode("utf-8")
        payload = {
            "file_type": file_type,
            "file_base64": file_b64
        }

        st.write("📤 **Request Payload Preview**")
        st.code(f'{{"file_type": "{file_type}", "file_base64": "<{len(file_b64)} characters>"}}', language="json")

        st.session_state.search_results = []
        with st.spinner("Processing uploaded file and searching for similar matches..."):
            try:
                response = requests.post(f"{API_BASE_URL}/files", json=payload, headers=headers)
                response.raise_for_status()
                results = response.json()
                st.session_state.search_results = results.get("matched_files", [])
                st.success(f"Found {len(st.session_state.search_results)} similar file(s).")
            except Exception as e:
                st.error(f"API error: {e}")
                st.error(getattr(e.response, "text", None))

# --- Result Renderer ---
def show_search_results():
    results = st.session_state.get("search_results", [])
    if not results:
        st.info("Your search results will appear here.")
        return

    st.subheader("Search Results")
    st.write(f"**Total Results:** {len(results)}")

    # When showing original image for thumbnail
    if (type(results[0]) is str):
        cols = st.columns(1)
        original_url = results[0]
        try:
         st.image(original_url, caption="Original Image", use_container_width=True)
        except Exception as e:
            st.error(f"Display error: {e}")
            st.json(item)

    else:
        # Display in 3-column layout
        cols = st.columns(3)
        for i, item in enumerate(results):
            with cols[i % 3]:
                # Handle expected keys
                thumbnail_s3_url = item.get("thumbnail_s3_url") or None
                original_url = item.get("original_url") or None
                thumbnail_url = item.get("thumbnail_url") or None

                if not original_url and not thumbnail_url:
                    st.warning("No valid URLs found for this item.")
                    st.json(item)
                    continue

                # Display thumbnail_s3_url above preview
                if thumbnail_s3_url:
                    st.code(thumbnail_s3_url)

                # Determine media type by URL (if known)
                preview_url = thumbnail_url or original_url
                if not preview_url:
                    st.warning("No previewable URL found.")
                    st.json(item)
                    continue

                try:
                    # If image with thumbnail and original_url
                    if thumbnail_url and original_url:
                        # Make thumbnail clickable
                        st.markdown(
                            f"[![thumbnail]({thumbnail_url})]({original_url})",
                            unsafe_allow_html=True
                        )
                    elif ".mp4" in preview_url.lower() or ".mov" in preview_url.lower():
                        st.video(preview_url)
                    elif "mp3" in preview_url.lower() or "wav" in preview_url.lower():
                        st.audio(preview_url)
                    else:
                        st.code(preview_url)
                except Exception as e:
                    st.error(f"Display error: {e}")
                    st.json(item)

# --- UI ---
st.header("🔍 Search Files")

# Search by species
with st.expander("🧬 Search by Species (Flexible Conditions)"):
    search_by_species()

# Search by tag and count
with st.expander("🔧 Search by Tag and Exact Count (Query Params)"):
    if "tag_count_rows" not in st.session_state:
        st.session_state.tag_count_rows = 1

    cols = st.columns([3, 2])
    cols[0].markdown("**Tag**")
    cols[1].markdown("**Count**")

    tags = []
    counts = []
    for i in range(st.session_state.tag_count_rows):
        c1, c2 = st.columns([3, 2])
        tags.append(c1.text_input(f"Tag {i+1}", key=f"tag_query_{i}", placeholder="crow"))
        counts.append(c2.number_input(f"Count {i+1}", min_value=1, step=1, key=f"count_query_{i}"))

    c_add, c_clear = st.columns(2)
    if c_add.button("➕ Add Another Tag", use_container_width=True):
        st.session_state.tag_count_rows += 1
        st.rerun()
    if c_clear.button("♻️ Reset Fields", use_container_width=True):
        st.session_state.tag_count_rows = 1
        for i in range(10):  # Clear previous fields if any
            st.session_state.pop(f"tag_query_{i}", None)
            st.session_state.pop(f"count_query_{i}", None)
        st.rerun()

    if st.button("Search by Tag & Count", use_container_width=True):
        query_params = {}
        for i in range(st.session_state.tag_count_rows):
            tag_val = st.session_state.get(f"tag_query_{i}")
            count_val = st.session_state.get(f"count_query_{i}")
            if tag_val and count_val:
                query_params[f"tag{i+1}"] = tag_val
                query_params[f"count{i+1}"] = int(count_val)

        if not query_params:
            st.warning("Please provide at least one tag and count.")
        else:
            st.write("🔍 **Search by Query Params Debug**")
            st.write("- Query Params:", query_params)

            st.session_state.search_results = []
            with st.spinner("Searching by query params..."):
                try:
                    response = requests.get(BIRDS_API, params=query_params, headers=headers)
                    response.raise_for_status()
                    results = response.json()
                    st.session_state.search_results = results.get("matched_files", [])
                    st.success(f"Found {len(st.session_state.search_results)} result(s).")
                except Exception as e:
                    st.error(f"API error: {e}")
                    st.error(getattr(e.response, "text", None))

# Search by min threshold
with st.expander("📉 Search by Minimum Count Threshold (Flexible JSON Body)"):

    if "min_threshold_conditions" not in st.session_state:
        st.session_state.min_threshold_conditions = [{}]  # List of dicts

    # Display all current conditions
    for idx, condition in enumerate(st.session_state.min_threshold_conditions):
        st.markdown(f"**Condition {idx+1}**")
        tag_keys = list(condition.keys()) or [""]
        cols = st.columns([3, 2])
        tag_input = cols[0].text_input(f"Tags (comma-separated)", value=", ".join(tag_keys), key=f"min_tags_{idx}", placeholder="crow, sparrow")
        count_input = cols[1].text_input("Counts (same order)", value=", ".join(str(condition.get(k, 1)) for k in tag_keys), key=f"min_counts_{idx}")

        # Update condition in session state
        tags = [t.strip() for t in tag_input.split(",") if t.strip()]
        counts = [c.strip() for c in count_input.split(",") if c.strip().isdigit()]
        if len(tags) == len(counts):
            st.session_state.min_threshold_conditions[idx] = dict(zip(tags, map(int, counts)))
        else:
            st.warning(f"Condition {idx+1} has mismatched tags/counts.")

    c_add, c_clear = st.columns(2)
    if c_add.button("➕ Add Condition", use_container_width=True):
        st.session_state.min_threshold_conditions.append({})
        st.rerun()
    if c_clear.button("♻️ Reset All Conditions", use_container_width=True):
        st.session_state.min_threshold_conditions = [{}]
        for k in list(st.session_state.keys()):
            if k.startswith("min_tags_") or k.startswith("min_counts_"):
                del st.session_state[k]
        st.rerun()

    if st.button("Search with Min Threshold", use_container_width=True):
        payload = [cond for cond in st.session_state.min_threshold_conditions if cond]
        if not payload:
            st.warning("Please define at least one tag-count condition.")
        else:
            st.write("🔍 **Min Threshold Search Debug**")
            st.json(payload)

            st.session_state.search_results = []
            with st.spinner("Searching with threshold..."):
                try:
                    response = requests.post(BIRDS_API, json=payload, headers=headers)
                    response.raise_for_status()
                    results = response.json()
                    st.session_state.search_results = results.get("matched_files", [])
                    st.success(f"Found {len(st.session_state.search_results)} result(s).")
                except Exception as e:
                    st.error(f"API error: {e}")
                    st.error(getattr(e.response, "text", None))

# Search by thumbnail URL
with st.expander("🖼️ Lookup Full Image from Thumbnail URL"):
    thumbnail_input = st.text_input("Enter S3 Thumbnail URL", placeholder="s3://team99-uploaded-files/thumbnails/sparrow_2.jpg", key="thumbnail_input")

    if st.button("🔍 Lookup Full Image URL", key="lookup_thumbnail"):
        if not thumbnail_input.strip().startswith("s3://"):
            st.warning("Please enter a valid S3 URI starting with `s3://`.")
        else:
            lookup_url = f"{API_BASE_URL}/thumbnails"
            payload = {"thumbnail_url": thumbnail_input.strip()}

            st.write("📤 **Request Payload**")
            st.json(payload)

            with st.spinner("Looking up full image URL..."):
                try:
                    response = requests.post(lookup_url, json=payload, headers=headers)
                    response.raise_for_status()
                    result = response.json()
                    if "original_url" in result:
                        st.session_state.search_results = [result["original_url"]]
                        st.success("Full image URL found!")
                    else:
                        st.warning("No full image URL found for the provided thumbnail.")
                except Exception as e:
                    st.error(f"API Error: {e}")
                    st.error(getattr(e.response, "text", None))

# Search by uploaded file
with st.expander("🧪 Search by Uploaded File (No Storage)"):
    search_by_uploaded_file()

# Clear Results
if st.session_state.get("search_results"):
    if st.button("🗑️ Clear Results"):
        st.session_state.search_results = []
        st.rerun()

st.markdown("---")
show_search_results()