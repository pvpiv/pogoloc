import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from urllib.parse import unquote_plus, parse_qs, urlencode
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

# Check query parameters
query_params = st.experimental_get_query_params()
base_url = query_params.get("base", [None])[0]
encoded_params = query_params.get("params", [None])[0]

if base_url and encoded_params:
    # Decode parameters and reconstruct the full URL
    decoded_params = parse_qs(unquote_plus(encoded_params))
    query_string = urlencode(decoded_params, doseq=True)
    full_url = f"{base_url}?{query_string}"
    st.write(f"Reconstructed URL: {full_url}")
    print(f"Reconstructed URL: {full_url}")

    # Save the reconstructed link to Firestore
    save_url_to_firestore(full_url)
    st.success(f"Auto-submitted URL: {full_url}")

# Display the latest URL for non-admin users
st.title("Public Page")

# Display the last posted URL in a code box
latest_url = get_latest_url()
if latest_url:
    st.code(latest_url, language='text')
else:
    st.info("No URL has been posted yet.")
