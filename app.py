import streamlit as st
import pandas as pd
import time
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

# --- 1. SECURE AUTHENTICATION BARRIER ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center;'>Candy.Dev Security Portal 🔐</h1>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("Supervisor Demo Login: Username: **admin** | Password: **admin123**")
        username = st.text_input("Administrator Username")
        password = st.text_input("Administrator Password", type="password")
        
        if st.button("Authenticate", use_container_width=True, type="primary"):
            if username == "admin" and password == "admin123":
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("🚨 Authentication Failed. Unauthorized Access Attempt Logged.")
    st.stop() # Halts all execution below this line until logged in

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

def fetch_live_gmails():
    creds = None
    # Token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no valid credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Requires a credentials.json file from Google Cloud Console
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Call the Gmail API
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

# --- 4. MAIN DASHBOARD UI ---
st.sidebar.title("🛡️ SpamGuard Pro")
st.sidebar.caption("Powered by Candy.Dev Architecture")
st.sidebar.markdown("---")
if st.sidebar.button("Log Out"):
    st.session_state["logged_in"] = False
    st.rerun()

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
            st.error("⚠️ **Missing credentials.json!** You must download your OAuth credentials from the Google Cloud Console and place them in the project folder to use this feature.")
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
