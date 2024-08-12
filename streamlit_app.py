from google.cloud import firestore
import streamlit as st
from datetime import datetime
import pytz
import json
import re

# Load Firebase credentials and create Firestore client
key_dict = json.loads(st.secrets["textkey"])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds, project="pvpogo")

# References
collection_name = "locations"

def save_url_to_firestore(url):
    """Save the URL with a timestamp to Firestore in a new document."""
    try:
        doc_ref = db.collection(collection_name).document()
        doc_ref.set({
            "url": url,
            "timestamp": firestore.SERVER_TIMESTAMP  # Firestore server timestamp
        })
        st.success(f"URL saved to Firestore: {url}")
    except Exception as e:
        st.error(f"Error saving URL to Firestore: {e}")

def get_latest_url():
    """Retrieve the latest URL from Firestore sorted by timestamp."""
    try:
        query = db.collection(collection_name).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1)
        docs = query.stream()
        for doc in docs:
            data = doc.to_dict()
            timestamp = data["timestamp"].to_datetime()
            est = pytz.timezone('US/Eastern')
            formatted_time = timestamp.astimezone(est).strftime("%Y-%m-%d %I:%M:%S %p %Z")
            return data["url"], formatted_time
    except Exception as e:
        st.error(f"Error retrieving URL from Firestore: {e}")
    return None, None

# Streamlit app layout and logic
st.markdown('<div class="title">Team Rocket HQ Pokémon Go Raid Tracker</div>', unsafe_allow_html=True)
is_admin = st.sidebar.checkbox("Admin Mode")

if is_admin:
    st.title("Admin Interface")
    new_url = st.text_area("Paste the URL:")
    if st.button("Post URL"):
        if new_url:
            save_url_to_firestore(new_url)
        else:
            st.error("No URL entered.")
else:
    url, last_updated = get_latest_url()
    if url:
        st.markdown(f'<div class="link-container"><a href="{url}" target="_blank">{url}</a></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="timestamp">Last Updated: {last_updated}</div>', unsafe_allow_html=True)
    else:
        st.info("No URLs found.")

