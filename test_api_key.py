
import requests
API_KEY = "AIzaSyB0hr19-_e1nkSjTttPBRT66ZvZ0vhcyyc"
url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
payload = {"email": "test@test.com", "password": "password", "returnSecureToken": True}
try:
    resp = requests.post(url, json=payload)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")
except Exception as e:
    print(f"Error: {e}")
