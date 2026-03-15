import os
import subprocess
import sys

def run():
    print("Checking dependencies...")
    try:
        import streamlit
        import mysql.connector
        import firebase_admin
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return

    print("Starting DocBuddy.ai...")
    try:
        subprocess.run(["streamlit", "run", "app.py"], check=True)
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error starting the app: {e}")

if __name__ == "__main__":
    run()
