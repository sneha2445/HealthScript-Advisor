import streamlit as st

def init_session_state():
    defaults = {
        "predicted": False,
        "disease": None,
        "description": None,
        "precautions": None,
        "workout": None,
        "diets": None,
        "medications": None,
        "vitals": None,
        "bmi": None,
        "user_role": "Patient",
        "user_mail": "",
        "user_name": "",
        "signedOut": False,
        "signOut": False,
        "otp_sent": False,
        "otp_verified": False,
        "generated_otp": None,
        "otp_time": None,
        "auth_mode": "Login",
        "firebase_available": False,
        "multi_disease_risk": False,
        "risk_diseases": set()
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def logout():
    keys_to_reset = [
        "predicted", "signOut", "signedOut", "user_name", "user_mail", 
        "otp_sent", "otp_verified", "user_role", "disease"
    ]
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()
