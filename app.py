import streamlit as st
import pandas as pd
import hashlib
import json
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

# Google API Imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="SpamGuard Pro | Candy.Dev", page_icon="🛡️", layout="wide")

# --- CREDENTIALS HELPERS ---
CREDENTIALS_FILE = "users.json"

def load_credentials() -> dict:
    """Load username/hashed-password map from credentials.json."""
    if not os.path.exists(CREDENTIALS_FILE):
        # Bootstrap a default admin account if the file is missing
        default = {"admin": hash_password("admin123")}
        save_credentials(default)
        return default
    with open(CREDENTIALS_FILE, "r") as f:
        return json.load(f)

def save_credentials(creds: dict) -> None:
    """Persist the credentials dict back to credentials.json."""
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(creds, f, indent=2)

def hash_password(password: str) -> str:
    """Return the SHA-256 hex digest of a plaintext password."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(username: str, password: str) -> bool:
    """Return True if the supplied password matches the stored hash."""
    creds = load_credentials()
    stored_hash = creds.get(username)
    return stored_hash is not None and stored_hash == hash_password(password)

def change_password(username: str, new_password: str) -> None:
    """Overwrite the stored hash for *username* with the hash of *new_password*."""
    creds = load_credentials()
    creds[username] = hash_password(new_password)
    save_credentials(creds)

# --- 1. SECURE AUTHENTICATION BARRIER ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center;'>Candy.Dev Security Portal 🔐</h1>", unsafe_allow_html=True)
    st.write("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("Supervisor Demo Login: Username: **admin** | Password: **admin123**")
        username = st.text_input("Administrator Username")
        password = st.text_input("Administrator Password", type="password")

        if st.button("Authenticate", use_container_width=True, type="primary"):
            if verify_password(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.rerun()
            else:
                st.error("🚨 Authentication Failed. Unauthorized Access Attempt Logged.")
    st.stop()

# --- 2. AI MODEL TRAINING ---
@st.cache_resource(show_spinner="Initializing AI Core...")
def train_model():
    url = "https://raw.githubusercontent.com/justmarkham/pycon-2016-tutorial/master/data/sms.tsv"
    df = pd.read_csv(url, sep='\t', header=None, names=['label', 'message'])
    X, y = df['message'], df['label']

    model = Pipeline([
        ('vectorizer', TfidfVectorizer(stop_words='english')),
        ('classifier', MultinomialNB())
    ])
    model.fit(X, y)
    return model

model = train_model()

# --- 3. GMAIL API INTEGRATION ---
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_credentials_from_secrets():
    cfg = st.secrets["google_oauth"]
    return {
        "installed": {
            "client_id":     cfg["client_id"],
            "project_id":    cfg["project_id"],
            "auth_uri":      cfg["auth_uri"],
            "token_uri":     cfg["token_uri"],
            "client_secret": cfg["client_secret"],
            "redirect_uris": [cfg["redirect_uri"]],
        }
    }

def fetch_live_gmails():
    import json
    creds = None

    if "gmail_token" in st.session_state:
        creds = Credentials.from_authorized_user_info(
            json.loads(st.session_state["gmail_token"]), SCOPES
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            st.session_state["gmail_token"] = creds.to_json()
        else:
            client_config = get_credentials_from_secrets()
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)
            st.session_state["gmail_token"] = creds.to_json()

    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=5).execute()
    messages = results.get('messages', [])

    email_data = []
    if not messages:
        return email_data

    for msg in messages:
        txt = service.users().messages().get(userId='me', id=msg['id'], format='snippet').execute()
        email_data.append({"Snippet": txt['snippet'], "ID": msg['id']})

    return email_data

# --- 4. SIDEBAR ---
st.sidebar.title("🛡️ SpamGuard Pro")
st.sidebar.caption("Powered by Candy.Dev Architecture")
st.sidebar.markdown("---")
st.sidebar.write(f"👤 Logged in as **{st.session_state['username']}**")

# --- CHANGE PASSWORD ---
with st.sidebar.expander("🔑 Change Password"):
    current_pw  = st.text_input("Current Password",  type="password", key="cp_current")
    new_pw      = st.text_input("New Password",       type="password", key="cp_new")
    confirm_pw  = st.text_input("Confirm New Password", type="password", key="cp_confirm")

    if st.button("Update Password", use_container_width=True):
        if not current_pw or not new_pw or not confirm_pw:
            st.warning("Please fill in all three fields.")
        elif not verify_password(st.session_state["username"], current_pw):
            st.error("❌ Current password is incorrect.")
        elif len(new_pw) < 6:
            st.error("❌ New password must be at least 6 characters.")
        elif new_pw != confirm_pw:
            st.error("❌ New passwords do not match.")
        elif new_pw == current_pw:
            st.warning("⚠️ New password must differ from the current one.")
        else:
            change_password(st.session_state["username"], new_pw)
            st.success("✅ Password updated successfully!")

st.sidebar.markdown("---")
if st.sidebar.button("Log Out"):
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.rerun()

# --- 5. MAIN DASHBOARD UI ---
st.title("Advanced Threat Detection Dashboard")

tab1, tab2 = st.tabs(["📲 Live Gmail Scanner (Pro)", "💬 Manual Scanner"])

with tab1:
    st.markdown("### OAuth 2.0 Gmail Integration")
    st.write("Securely fetch and scan the latest emails directly from your inbox using the Google API.")

    if st.button("Connect to Gmail & Scan Inbox"):
        try:
            with st.spinner("Authenticating with Google and fetching live emails..."):
                live_emails = fetch_live_gmails()

            if live_emails:
                st.success(f"Successfully fetched {len(live_emails)} recent emails.")
                for email in live_emails:
                    snippet = email["Snippet"]
                    prediction = model.predict([snippet])[0]
                    confidence = max(model.predict_proba([snippet])[0]) * 100

                    with st.expander(f"Email ID: {email['ID']} | AI Status: {prediction.upper()}"):
                        st.write(f"**Preview:** {snippet}")
                        st.write(f"**Confidence:** {confidence:.2f}%")
                        if prediction == 'spam':
                            st.error("🚨 AI flagged this email as Spam.")
                        else:
                            st.success("✅ AI flagged this email as Safe.")
            else:
                st.info("Your inbox is empty.")
        except FileNotFoundError:
            st.error("⚠️ **Missing credentials.json!** Download your OAuth credentials from the Google Cloud Console and place them in the project folder.")
        except Exception as e:
            st.error(f"API Error: {e}")

with tab2:
    st.markdown("### Text Vector Analysis")
    user_input = st.text_area("Enter suspicious text manually:")
    if st.button("Run Diagnostics"):
        if user_input:
            prediction = model.predict([user_input])[0]
            if prediction == 'spam':
                st.error("🚨 SPAM DETECTED")
            else:
                st.success("✅ SAFE MESSAGE")

