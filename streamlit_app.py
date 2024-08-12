import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime
import pytz
import json
import re

# Load Firebase credentials and create Firestore client
key_dict = json.loads(st.secrets["textkey"])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds, project="pvpogo")

# Firestore collection name
collection_name = "location"

def get_latest_url():
    """Retrieve the latest URL from Firestore based on the highest document ID."""
    try:
        # Query to find the highest numeric document ID
        docs = db.collection(collection_name).stream()
        max_doc = None
        max_id = 0
        for doc in docs:
            doc_id = int(doc.id)  # Assuming document IDs are stored as numeric strings
            if doc_id > max_id:
                max_id = doc_id
                max_doc = doc
        if max_doc:
            data = max_doc.to_dict()
            timestamp = data['Timestamp'].to_datetime()
            est = pytz.timezone('US/Eastern')
            formatted_time = timestamp.astimezone(est).strftime("%Y-%m-%d %I:%M:%S %p %Z")
            return data['URL'], formatted_time
    except Exception as e:
        st.error(f"Error retrieving URL from Firestore: {e}")
    return None, None

def save_url_to_firestore(url):
    """Save the URL into Firestore with an incremented document ID."""
    try:
        docs = db.collection(collection_name).stream()
        max_id = max((int(doc.id) for doc in docs), default=0)
        new_id = str(max_id + 1)
        db.collection(collection_name).document(new_id).set({
            'URL': url,
            'Timestamp': firestore.SERVER_TIMESTAMP
        })
        st.success(f"URL saved to Firestore with ID {new_id}: {url}")
    except Exception as e:
        st.error(f"Error saving URL to Firestore: {e}")

# Admin Interface
query_params = st.experimental_get_query_params()
is_admin = query_params.get("admin", ["false"])[0].lower() == "true"

if is_admin:
    st.sidebar.title("Admin Interface")
    new_url = st.sidebar.text_area("Paste the URL:")
    if st.sidebar.button("Post URL"):
        if new_url:
            save_url_to_firestore(new_url)
        else:
            st.sidebar.error("No URL entered.")

# Display the latest URL
url, last_updated = get_latest_url()
if url:
    st.markdown(f'<div class="link-container"><a href="{url}" target="_blank">{url}</a></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="timestamp">Last Updated: {last_updated}</div>', unsafe_allow_html=True)
else:
    st.info("No URLs found.")
