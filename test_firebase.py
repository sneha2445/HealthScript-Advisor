
import firebase_admin
from firebase_admin import credentials, auth
import sys

try:
    cred = credentials.Certificate("docbuddy-ai-firebase-adminsdk-fbsvc-a2af6aaab6.json")
    try:
        firebase_admin.initialize_app(cred)
    except ValueError:
        pass # Already initialized
    
    # Try a simple operation
    try:
        # We don't need a real user, just calling any auth method 
        # that requires a token will trigger the RefreshError if the JWT is invalid.
        # list_users(max_results=1) is a good test.
        page = auth.list_users(max_results=1)
        print("SUCCESS: Connection to Firebase Auth successful.")
        for user in page.users:
            print(f"Found user: {user.uid}")
    except Exception as e:
        print(f"FAILURE: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

except Exception as e:
    print(f"CRITICAL: Could not even initialize or load cert: {e}")
