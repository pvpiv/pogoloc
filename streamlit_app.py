import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
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

def get_latest_url():
    """Retrieve the latest URL from Firestore."""
    try:
        doc_ref = db.collection(collection_name).document(document_name)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get("url", "")
    except Exception as e:
        print(f"Error retrieving URL from Firestore: {e}")
    return ""

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

# Display the latest URL for non-admin users
st.title("Public Page")

# Display the last posted URL in a code box
latest_url = get_latest_url()
if latest_url:
    st.code(latest_url, language='text')
else:
    st.info("No URL has been posted yet.")
