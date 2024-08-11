import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
from datetime import datetime
import pytz
import json
import re
import time

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

def extract_url(text):
    """Extract URL from a given text."""
    url_pattern = re.compile(r'https?://\S+')
    urls = url_pattern.findall(text)
    for each in urls:
        st.write(each)
    return urls[0] if urls else ""

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
        background-image: url('https://assets.pokemon.com//assets/cms2/img/misc/virtual-backgrounds/sword-shield/dynamax-battle.png');
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
    .embedded-link {
        width: 100%;
        height: 600px;
        border: none;
        border-radius: 10px;
        box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.3);
        margin-top: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="title">Team Rocket HQ Pokémon Go Raid Tracker</div>', unsafe_allow_html=True)

if is_admin:
    st.title("Admin Interface")
    
    # Container to control the layout
    with st.container():
        # Display the "Post URL" button above the text area
        post_button = st.button("Post URL")
        
        # Input box to post a new URL
        new_url = st.text_area("Paste the text containing the URL:")
        
        # Process after the button is clicked
        if post_button:
            extracted_url = extract_url(new_url)
            if extracted_url:
                save_url_to_firestore(extracted_url)
                st.success("URL updated successfully!")
                st.experimental_rerun()  # Refresh the page
            else:
                st.error("No valid URL found in the text.")
        
        # Fetch and display the latest URL below the input box
        latest_url, timestamp = get_latest_data()
        if latest_url:
            st.write("Latest URL:", latest_url)
        else:
            st.info("No URL has been posted yet.")
else:
    # Display the public page content
    latest_url, timestamp = get_latest_data()
    if latest_url:
        st.markdown('<div class="link-container">Click link below for Live Raid Tracker</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="link-container"><a href="{latest_url}" target="_blank">{latest_url}</a></div>', unsafe_allow_html=True)
        # Embed the link directly on the site
        st.markdown(f'<iframe src="{latest_url}" class="embedded-link"></iframe>', unsafe_allow_html=True)
        if timestamp:
            # Convert timestamp to EST
            est = pytz.timezone('US/Eastern')
            last_updated = timestamp.astimezone(est).strftime("%Y-%m-%d %I:%M:%S %p %Z")
            st.markdown(f'<div class="timestamp">Last Updated: {last_updated}</div>', unsafe_allow_html=True)
    else:
        st.info("No URL has been posted yet.")
