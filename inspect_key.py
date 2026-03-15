
import json
try:
    with open('docbuddy-ai-firebase-adminsdk-fbsvc-bc8b294369.json') as f:
        data = json.load(f)
        pk = data.get('private_key', '')
        print(f"Key length: {len(pk)}")
        print(f"Newline count: {pk.count('\n')}")
        print(f"Begins correctly: {pk.startswith('-----BEGIN PRIVATE KEY-----')}")
        print(f"Ends correctly: {pk.strip().endswith('-----END PRIVATE KEY-----')}")
        
        # Check for weird characters
        import string
        valid_chars = string.ascii_letters + string.digits + "+/=\n-" + " "
        weird = [c for c in pk if c not in valid_chars]
        if weird:
            print(f"WEIRD CHARACTERS FOUND: {set(weird)}")
        else:
            print("No weird characters found.")

except Exception as e:
    print(f"Error: {e}")
