
import firebase_admin
from firebase_admin import credentials, auth, firestore

try:
    cred = credentials.Certificate("docbuddy-ai-firebase-adminsdk-fbsvc-a2af6aaab6.json")
    try:
        firebase_admin.initialize_app(cred)
    except ValueError:
        pass
    
    print("Testing Auth...")
    auth.list_users(max_results=1)
    print("Auth SUCCESS")
    
    print("Testing Firestore...")
    db = firestore.client()
    # Just a small read
    db.collection("users").limit(1).get()
    print("Firestore SUCCESS")

except Exception as e:
    print(f"FAILURE: {type(e).__name__}: {e}")
