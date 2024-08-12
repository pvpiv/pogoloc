import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime
import pytz
import json
import re
import requests
from urllib.parse import urlparse, parse_qs
import streamlit.components.v1 as components


# Load Firebase credentials and create Firestore client
key_dict = json.loads(st.secrets["textkey"])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds, project="pvpogo")

# Firestore collection name
collection_name = "location"

def save_url_to_firestore(url):
    """Save the URL with a timestamp to Firestore."""
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

def get_latest_url():
    """Retrieve the latest URL from Firestore based on the highest document ID."""
    try:
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
            timestamp = data['Timestamp']
            est = pytz.timezone('US/Eastern')
            formatted_time = timestamp.astimezone(est).strftime("%Y-%m-%d %I:%M:%S %p %Z")
            return data['URL'], formatted_time
    except Exception as e:
        st.error(f"Error retrieving URL from Firestore: {e}")
    return None, None

def restore_special_characters(url):
    """Restore special characters in the URL."""
    return url.replace('!!!', '?').replace('[[[', '&')

# Check query parameters
query_params = st.experimental_get_query_params()
is_admin = query_params.get("admin", ["false"])[0].lower() == "true"
auto_link = query_params.get("link", [None])[0]

if auto_link:
    # If the link parameter is provided, decode it and save it
    decoded_link = restore_special_characters(auto_link)
    save_url_to_firestore(decoded_link)
    st.success(f"Auto-submitted URL: {decoded_link}")

# Page title and background styling
st.markdown(
    """
    <style>
    body {
        background-image: url('dynamax-battle.png');
        background-size: cover;
    }
    .title {
        color: #FFCB05;
        font-size: 48px;
        text-align: center;
        text-shadow: 2px 2px #3B4CCA;
    }
    .timestamp {
        color: #FFFFFF;
        font-size: 18px;
        text-align: left;
        margin-top: 10px;
        text-shadow: 1px 1px #3B4CCA;
    }
    .link-container {
        color: #FFFFFF;
        font-size: 24px;
        text-align: left;
        margin-top: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="title">Team Rocket HQ Pokémon Go Raid Tracker</div>', unsafe_allow_html=True)

# Admin Interface
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

