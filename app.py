import streamlit as st
import os
import warnings
from dotenv import load_dotenv

# Import utilities
from utils.db_handler import load_db_mappings, load_all_csv_data
from utils.firebase_handler import init_firebase, get_mock_db
from utils.session_manager import init_session_state, logout
from utils.model_engine import get_predicted_values, get_disease_details

# Import page modules
from recommendations import show_recommendations_page
from home import show_home
from chatbot import show_chatbot
from workflow import show_workflow
from report_page import show_generate_report
from history_page import show_history
from profile_page import show_profile
from account import account
from doctor_dashboard import show_doctor_dashboard
from streamlit_option_menu import option_menu

# Initial Setup
warnings.filterwarnings("ignore")
load_dotenv()

# Page Config (MUST be first Streamlit command)
st.set_page_config(
    page_title="HealthScript Advisor",
    page_icon="static/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styles
hide_st_style = """
<style>
    #MainMenu {visibility : hidden;}
    footer {visibility : hidden;}
    .stAppDeployButton {display:none;}
    header {visibility: visible !important;}
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# Initialize Session State
init_session_state()

# Load Data
symptoms_dict, diseases_list, symptoms_list, critical_diseases = load_db_mappings()
csv_data = load_all_csv_data()

# Firebase Initialization
firebase_available, db = init_firebase()
if not firebase_available:
    db = get_mock_db()
st.session_state.firebase_available = firebase_available

# Helper Functions (Logic that depends on DB/API)
def check_severity(spo2, temp, bp_sys):
    severity_score = 0
    warnings = []
    color = "green"
    status = "Mild - Home Care"

    if spo2 < 90:
        severity_score += 2
        warnings.append("Critical SpO2 Levels (<90%)")
    elif spo2 < 95:
        severity_score += 1
        warnings.append("Low SpO2 Levels")

    if temp > 102:
        severity_score += 2
        warnings.append("High Fever (>102°F)")
    
    if bp_sys > 160:
        severity_score += 2
        warnings.append("High Blood Pressure (Hypertension)")

    if severity_score >= 2:
        status = "CRITICAL - CONSULT DOCTOR IMMEDIATELY"
        color = "red"
    elif severity_score == 1:
        status = "Moderate - Monitor Closely"
        color = "orange"   
    return status, color, warnings

def save_prediction_history(user_email, name, disease, status, symptoms, bmi, age, gender, existing_diseases, vitals, phone):
    from firebase_admin import firestore
    data = {
        "user_email": user_email,
        "patient_name": name,
        "disease": disease,
        "severity_status": status,
        "symptoms": symptoms,
        "bmi": float(bmi),
        "age": int(age),
        "gender": gender,
        "existing_diseases": existing_diseases,
        "vitals": vitals,
        "patient_phone": phone,
        "timestamp": firestore.SERVER_TIMESTAMP
    }
    try:
        db.collection("history").add(data)
    except Exception as e:
        print(f"Error saving history: {e}")

# Sidebar & Navigation
is_logged_in = st.session_state.get("signedOut", False)

if is_logged_in:
    with st.sidebar:
        user_role = st.session_state.get("user_role", "Patient")
        user_name = st.session_state.get("user_name", "User")
        
        st.markdown(f"### Welcome, {user_name}!")
        
        if user_role == "Doctor":
            options = ["Doctor Dashboard", "Account"]
            icons = ["clipboard-pulse", "gear"]
        else:
            options = ["Home", "Recommendations", "Generate Report", "History", "Chat With Me", "WorkFlow", "Account"]
            icons = ["house", "magic", "book", "clock-history", "chat", "activity", "gear"]
            
        selected = option_menu(
            menu_title="Main Menu",
            options=options,
            icons=icons,
            menu_icon="cast",
            default_index=0,
        )
        
        st.divider()
        if st.button("Log Out 👋", use_container_width=True):
            logout()
else:
    selected = "Account"

# Page Routing
if not is_logged_in and selected != "Account":
    st.title("Please Login First ⚠️")
    st.info("Please go to the Account section to log in.")
    st.stop()

if selected == "Account":
    account()
elif selected == "Home":
    show_home()
elif selected == "WorkFlow":
    show_workflow()
elif selected == "Recommendations":
    # Wrap utility functions for the recommendations page
    def predict_wrapper(symptoms):
        disease = get_predicted_values(symptoms, csv_data["symptoms"])
        details = get_disease_details(disease, csv_data)
        return disease, details

    show_recommendations_page(
        symptoms_dict, symptoms_list, critical_diseases,
        predict_wrapper, check_severity, save_prediction_history, db
    )
elif selected == "Doctor Dashboard":
    show_doctor_dashboard(db)
elif selected == "Generate Report":
    show_generate_report()
elif selected == "History":
    show_history(db)
elif selected == "Chat With Me":
    show_chatbot()