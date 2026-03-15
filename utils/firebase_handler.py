import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
from dotenv import load_dotenv

load_dotenv()

@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        try:
            # 1. Try Streamlit Secrets (for Cloud Deployment)
            if "firebase_credentials" in st.secrets:
                secret_dict = dict(st.secrets["firebase_credentials"])
                cred = credentials.Certificate(secret_dict)
                firebase_admin.initialize_app(cred)
                return True, firestore.client()
            
            # 2. Try Local File
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "docbuddy-ai-firebase-adminsdk-fbsvc-a2af6aaab6.json")
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                return True, firestore.client()
            
            return False, None
        except Exception as e:
            st.error(f"Firebase initialization error: {str(e)}")
            return False, None
    else:
        try:
            return True, firestore.client()
        except Exception as e:
            st.error(f"Firestore connection error: {str(e)}")
            return False, None

def get_mock_db():
    class MockDB:
        def collection(self, name): return MockCollection()
    class MockCollection:
        def add(self, data): pass
        def stream(self): return []
        def document(self, doc_id): return MockDocument()
        def where(self, *args): return self
    class MockDocument:
        def get(self): return MockDoc()
        def set(self, data, **kwargs): pass
    class MockDoc:
        exists = False
        def to_dict(self): return {}
    return MockDB()
