import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import json
import re
from datetime import datetime

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
    doc_ref = db.collection(collection_name).document(document_name)
    doc_ref.set({
        "url": url,
        "timestamp": firestore.SERVER_TIMESTAMP
    })

def get_latest_url():
    """Retrieve the latest URL from Firestore."""
    doc_ref = db.collection(collection_name).document(document_name)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict().get("url", "")
    return ""

def extract_url(text):
    """Extract URL from a given text."""
    url_pattern = re.compile(r'https?://\S+')
    urls = url_pattern.findall(text)
    return urls[0] if urls else ""

# Check if the admin query parameter is present
query_params = st.experimental_get_query_params()
is_admin = query_params.get("admin", ["false"])[0].lower() == "true"

if is_admin:
    st.title("Admin Interface")
    
    # Display the "Post URL" button
    st.write("Post the URL to update for all users:")
    new_url = st.text_area("Paste the text containing the URL:")
    
    # Extract URL
    extracted_url = extract_url(new_url)
    
    if st.button("Post URL"):
        if extracted_url:
            save_url_to_firestore(extracted_url)
            st.success("URL updated successfully!")
        else:
            st.error("No valid URL found in the text.")
else:
    st.title("Public Page")
    
    # Display the last posted URL in a code box
    latest_url = get_latest_url()
    if latest_url:
        st.code(latest_url, language='text')
    else:
        st.info("No URL has been posted yet.")
