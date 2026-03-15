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
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "docbuddy-ai-firebase-adminsdk-fbsvc-a2af6aaab6.json")
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                return True, firestore.client()
            else:
                return False, None
        except Exception as e:
            st.error(f"Firebase initialization error: {e}")
            return False, None
    else:
        return True, firestore.client()

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
