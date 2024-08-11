import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime
from urllib.parse import unquote_plus
import json

# Load Firebase credentials from Streamlit secrets
key_dict = json.loads(st.secrets["textkey"])
creds = service_account.Credentials.from_service_account_info(key_dict)

# Firestore client
db = firestore.Client(credentials=creds, project="pvpogo")

# Collection and document references
collection_name = "location"
document_name = "locs"

def save_url_to_firestore(url):
    """Save the URL with a timestamp to Firestore."""
    try:
        doc_ref = db.collection(collection_name).document(document_name)
        doc_ref.set({
            "url": url,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        print(f"URL saved to Firestore: {url}")
    except Exception as e:
        print(f"Error saving URL to Firestore: {e}")

def get_latest_data():
    """Retrieve the latest URL and timestamp from Firestore."""
    try:
        doc_ref = db.collection(collection_name).document(document_name)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            return data.get("url", ""), data.get("timestamp")
    except Exception as e:
        print(f"Error retrieving URL from Firestore: {e}")
    return "", None

def restore_special_characters(url):
    """Restore special characters in the URL."""
    return url.replace('!!!', '?').replace('[[[', '&')

# Check query parameters
query_params = st.experimental_get_query_params()
modified_link = query_params.get("link", [None])[0]

if modified_link:
    # Restore special characters and reconstruct the full URL
    restored_link = restore_special_characters(modified_link)
    st.write(f"Reconstructed URL: {restored_link}")
    print(f"Reconstructed URL: {restored_link}")

    # Save the reconstructed link to Firestore
    save_url_to_firestore(restored_link)
    st.success(f"Auto-submitted URL: {restored_link}")

# Page title and background styling
st.markdown(
    """
    <style>
    body {
        background-image: url('https://i.imgur.com/your_image.jpg');
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
        text-align: center;
        margin-top: 10px;
        text-shadow: 1px 1px #3B4CCA;
    }
    .hyperlink {
        color: #0074D9;
        font-size: 24px;
        text-align: center;
        text-decoration: none;
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 10px;
        padding: 10px;
        box-shadow: 3px 3px 10px rgba(0, 0, 0, 0.5);
        display: inline-block;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="title">Team Rocket HQ Pokémon Go Raid Tracker</div>', unsafe_allow_html=True)

# Display the latest URL and timestamp
latest_url, timestamp = get_latest_data()
if latest_url:
    hyperlink_html = f'<a href="{latest_url}" target="_blank" class="hyperlink">Open Raid Link</a>'
    st.markdown(hyperlink_html, unsafe_allow_html=True)
    if timestamp:
        if isinstance(timestamp, datetime):
            last_updated = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        else:
            last_updated = datetime.fromtimestamp(timestamp.timestamp()).strftime("%Y-%m-%d %H:%M:%S")
        st.markdown(f'<div class="timestamp">Last Updated: {last_updated}</div>', unsafe_allow_html=True)
else:
    st.info("No URL has been posted yet.")
