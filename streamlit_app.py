import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import pytz
import json
import re

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
        margin-bottom: 20px;
    }
    .timestamp {
        color: #FFFFFF;
        font-size: 18px;
        text-align: center;
        margin-top: 10px;
        text-shadow: 1px 1px #3B4CCA;
    }
    .link-container {
        color: #FFFFFF;
        font-size: 24px;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .actual-link {
        color: #3B4CCA; /* Change to a contrasting color */
        font-size: 18px;
        text-align: center;
        margin-top: 10px;
        word-wrap: break-word;
        text-decoration: underline;
    }
    .link-button {
        display: inline-block;
        background-color: #FFCB05; /* Yellow color */
        color: #3B4CCA; /* Dark blue text */
        padding: 10px 20px;
        font-size: 24px;
        border-radius: 5px;
        text-decoration: none;
        box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2);
        transition: background-color 0.3s, color 0.3s;
    }
    .link-button:hover {
        background-color: #FFD700; /* Lighter yellow */
        color: #2B3CA0; /* Slightly darker blue */
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="title">Team Rocket HQ Pokémon Go Raid Tracker</div>', unsafe_allow_html=True)

# Initialize session state for storing the latest URL and notification state
if 'latest_url' not in st.session_state:
    st.session_state['latest_url'] = None
    st.session_state['initial_load'] = True  # Flag to indicate the initial load

# Function to update the displayed URL if it changes
def update_displayed_url():
    # Retrieve the latest URL from Firestore
    url, last_updated = get_latest_url()
    if url and url != st.session_state['latest_url']:
        st.session_state['latest_url'] = url
        st.session_state['last_updated'] = last_updated
        # Notify if it's not the initial load
        if not st.session_state['initial_load']:
            st.session_state['notification'] = True
        st.session_state['initial_load'] = False

# Function to play a sound using JavaScript
def play_sound():
    sound_html = """
    <audio autoplay>
        <source src="https://www.soundjay.com/button/beep-01a.mp3" type="audio/mpeg">
        Your browser does not support the audio element.
    </audio>
    """
    st.markdown(sound_html, unsafe_allow_html=True)

# Update the URL and check for changes
update_displayed_url()

# Display notification if the URL changed after initial load
if 'notification' in st.session_state and st.session_state['notification']:
    st.info("The link has changed. Please check the new link below.")
    play_sound()
    st.session_state['notification'] = False

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
if st.session_state['latest_url']:
    st.markdown(f"""
        <div class="link-container">
            <a href="{st.session_state['latest_url']}" target="_blank" class="link-button">Click Here to See Live Map</a>
        </div>
        <div class="actual-link">
            <a href="{st.session_state['latest_url']}" target="_blank">{st.session_state['latest_url']}</a>
        </div>
        <div class="timestamp">Last Updated: {st.session_state['last_updated']}</div>
    """, unsafe_allow_html=True)
else:
    st.info("No URLs found.")
