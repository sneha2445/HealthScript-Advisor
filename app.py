# importing the required libraries here.
import streamlit as st
import mysql.connector
from mysql.connector import Error
from streamlit_option_menu import option_menu
import pandas as pd
import numpy as np
import pickle
import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth
import requests
import json
import ast
from dotenv import load_dotenv
import os
import warnings
import re
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from typing import Generator
from groq import Groq
from langdetect import detect
from translate import Translator
from firebase_admin import firestore
warnings.filterwarnings("ignore")
load_dotenv()
import streamlit as st

from recommendations import show_recommendations
from home import show_home
from chatbot import show_chatbot
from workflow import show_workflow
from report_page import show_generate_report
from history_page import show_history
from profile_page import show_profile
# ================= DATABASE CONNECTION  =================

def get_db_mappings():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", "sneha"), # Mysql password
            database=os.getenv("MYSQL_DATABASE", "docbuddy_db")
        )
        cursor = conn.cursor()
        
        # 1. To fetch Symptoms  
        cursor.execute("SELECT symptom_name, symptom_id FROM symptoms ")
        rows = cursor.fetchall()
        s_dict = {str(row[0]).strip(): int(row[1]) for row in rows}
        s_list = list(s_dict.keys()) # Dropdown  list
        
        # 2. To fetch Diseases 
        cursor.execute("SELECT disease_id, disease_name FROM diseases")
        d_list = {int(row[0]): str(row[1]).strip() for row in cursor.fetchall()}
        
        # 3.  To fetch Critical List 
        cursor.execute("SELECT disease_name FROM critical_list")
        c_list = [str(row[0]).strip() for row in cursor.fetchall()]
        conn.close()
        return s_dict, d_list, s_list, c_list
    except Exception as e:
        print(f"Database Connection Failed: {e}. Falling back to local data files.")
        try:
            # Fallback 1: Load Symptoms from symptoms_df.csv
            sdf = pd.read_csv("Data/symptoms_df.csv")
            # Extract all symptom columns and flatten
            s_cols = ['Symptom_1', 'Symptom_2', 'Symptom_3', 'Symptom_4']
            all_s = []
            for col in s_cols:
                all_s.extend(sdf[col].dropna().unique())
            
            # Clean and get unique list
            s_list = sorted(list(set(s.strip().replace('_', ' ').title() for s in all_s if isinstance(s, str))))
            s_dict = {s: i for i, s in enumerate(s_list)}
            
            # Fallback 2: Load Diseases from description.csv
            ddf = pd.read_csv("Data/description.csv")
            d_list = {i: row['Disease'].strip() for i, row in ddf.iterrows()}
            
            # Fallback 3: Critical list (placeholder as there's no CSV for this)
            c_list = ["Heart Attack", "AIDS", "Diabetes", "Hypertension", "Dengue", "Malaria"]
            
            return s_dict, d_list, s_list, c_list
        except Exception as fallback_err:
            st.error(f"Fallback Data Loading Failed: {fallback_err}")
            return {}, {}, [], []

# Data Load 
symptoms_dict, diseases_list, symptoms_list, critical_diseases = get_db_mappings()

try:
    # Try to initialize or refresh the Firebase app
    try:
        app = firebase_admin.get_app()
        # If we reached here, the app is already initialized. 
        # But if it was initialized with old/broken credentials, we might need to refresh.
        # For safety in Streamlit, we check a session variable.
        if not st.session_state.get('firebase_initialized', False):
             firebase_admin.delete_app(app)
             raise ValueError("Re-initializing")
    except ValueError:
        cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH", "docbuddy-ai-firebase-adminsdk-fbsvc-a2af6aaab6.json"))
        firebase_admin.initialize_app(cred)
        st.session_state.firebase_initialized = True
    
    firebase_working = True
    st.session_state.firebase_available = True
    db = firestore.client()
except Exception as e:
    print(f"Firebase initialization failed: {e}")
    firebase_working = False
    st.session_state.firebase_available = False
    st.session_state.firebase_initialized = False
    # Create a mock db object to prevent errors
    class MockDB:
        def collection(self, name):
            return MockCollection()
    class MockCollection:
        def add(self, data):
            pass
        def stream(self):
            return []
        def document(self, doc_id):
            return MockDocument()
    class MockDocument:
        def get(self):
            return MockDoc()
        def set(self, data, **kwargs):
            pass
    class MockDoc:
        pass
    db = MockDB()
    print("Running in offline mode - Firebase not available")

# setting up the page header here.
hide_st_style = """<style>
                #MainMenu {visibility : hidden;}
                footer {visibility : hidden;}
                .stAppDeployButton {display:none;}
                /* Allow the header and sidebar toggle button to be visible again */
                header {visibility: visible !important;}
                </style>"""

# setting up the page config here.
st.set_page_config(
    page_title="HealthScript Advisor",
    page_icon="static/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",)

st.markdown(hide_st_style, unsafe_allow_html=True)

# loading the dataset here
symptom_data = pd.read_csv("Data/symptoms_df.csv")
precautions_data = pd.read_csv("Data/precautions_df.csv")
workout_data = pd.read_csv("Data/workout_df.csv")
desc_data = pd.read_csv("Data/description.csv")
diets_data = pd.read_csv("Data/diets.csv")
medication_data = pd.read_csv("Data/medications.csv")

# Replace 'nan' string and np.nan with None for consistency
precautions_data.replace('nan', None, inplace=True)
precautions_data = precautions_data.where(pd.notnull(precautions_data), None)

# Initialize session state for the data to generate the report
if "predicted" not in st.session_state:
    st.session_state.predicted = False
if 'disease' not in st.session_state:
    st.session_state.disease = None
if 'description' not in st.session_state:
    st.session_state.description = None
if 'precautions' not in st.session_state:
    st.session_state.precautions = None
if 'workout' not in st.session_state:
    st.session_state.workout = None
if 'diets' not in st.session_state:
    st.session_state.diets = None
if 'medications' not in st.session_state:
    st.session_state.medications = None
if 'vitals' not in st.session_state:
    st.session_state.vitals = None
if 'bmi' not in st.session_state:
    st.session_state.bmi = None

# ================= ayurveda_remedies =================
def get_ayurveda_remedies(disease_name):
    try:
        conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"), user=os.getenv("MYSQL_USER", "root"), password=os.getenv("MYSQL_PASSWORD", "sneha"), database=os.getenv("MYSQL_DATABASE", "docbuddy_db") )
        cursor = conn.cursor()
        query = "SELECT remedy_text FROM ayurvedic_remedies WHERE disease_name = %s"
        cursor.execute(query, (disease_name,))
        rows = cursor.fetchall()
        conn.close()

        if rows:
            return [row[0] for row in rows]
        return ["Consult a professional doctor."]
    except Exception as e:
        return [f"DB Error: {e}"]

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

# app.py mein isse replace karein
def save_prediction_history(user_email, name, disease, status, symptoms, bmi, age, gender, existing_diseases, vitals): # Updated arguments
    # Prepare data
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
        "vitals": vitals, # dict with spo2, temp, bp
        "timestamp": firestore.SERVER_TIMESTAMP
    }
    # Save to Firestore 'history' collection
    db.collection("history").add(data)

def check_multi_disease_risk(user_email):
    """
    Check if user has been predicted with DIFFERENT diseases within the past 5 days.
    Returns (True, disease_set) if risky, else (False, set()).
    """
    from datetime import datetime, timedelta, timezone
    cutoff = datetime.now(timezone.utc) - timedelta(days=5)
    try:
        docs = (
            db.collection("history")
            .where("user_email", "==", user_email)
            .stream()
        )
        recent_diseases = set()
        for doc in docs:
            data = doc.to_dict()
            ts = data.get("timestamp")
            if ts is None:
                continue
            # Firestore timestamps are datetime-aware
            if hasattr(ts, "tzinfo") and ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts >= cutoff:
                disease = data.get("disease", "").strip()
                if disease:
                    recent_diseases.add(disease)
        if len(recent_diseases) >= 2:
            return True, recent_diseases
        return False, set()
    except Exception as e:
        print(f"Multi-disease check error: {e}")
        return False, set()

# ================= Report Generation =================
def generate_report(name, age, disease, description, precautions, workouts, diets, medications, vitals, bmi, file_path):
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    styles = getSampleStyleSheet()
    styleN = styles['BodyText']
    styleH = styles['Heading1']
    styleH2 = styles['Heading2']

    # getting the current date and time here
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    # Title
    title = Paragraph("DocBuddy Health Report", styleH)
    story = [title, Spacer(1, 12)]
    # Personal details
    details = Paragraph("Patient Details ", styleH2)
    story = [details, Spacer(1, 10)]
    name_para = Paragraph(f"Patient Name : <b>{name.title()}</b>", styleN)
    story.append(name_para)
    story.append(Spacer(1, 5))
    age_para = Paragraph(f"Patient Age : <b>{age} Years</b>", styleN)
    story.append(age_para)
    story.append(Spacer(1, 5))
    date_para = Paragraph(f"Report Generated On : <b>{current_time}</b>", styleN)
    story.append(date_para)
    story.append(Spacer(1, 12))

    # Vitals and BMI Section
    vitals_title = Paragraph("Patient Vitals & BMI", styleH2)
    story.append(vitals_title)
    story.append(Spacer(1, 10))
    if vitals:
        story.append(Paragraph(f"SpO2: <b>{vitals.get('spo2', 'N/A')}%</b>", styleN))
        story.append(Paragraph(f"Body Temp: <b>{vitals.get('temp', 'N/A')}°F</b>", styleN))
        story.append(Paragraph(f"Systolic BP: <b>{vitals.get('bp', 'N/A')}</b>", styleN))
        story.append(Paragraph(f"Height: <b>{vitals.get('height', 'N/A')} cm</b>", styleN))
        story.append(Paragraph(f"Weight: <b>{vitals.get('weight', 'N/A')} kg</b>", styleN))
    
    if bmi:
        story.append(Paragraph(f"Calculated BMI: <b>{bmi:.1f}</b>", styleN))
    story.append(Spacer(1, 12))

    # Predicted Disease
    disease_title = Paragraph("Health Assessment", styleH2)
    story.append(disease_title)
    story.append(Spacer(1, 10))
    disease_paragraph = Paragraph(f"Predicted Disease : <b>{disease.title()}</b>", styleN)
    story.append(disease_paragraph)
    story.append(Spacer(1, 12))

    # Description
    description_paragraph = Paragraph(f"Description : <b>{description}</b>", styleN)
    story.append(description_paragraph)
    story.append(Spacer(1, 12))

    # Precautions
    precautions_paragraph = Paragraph("Precautions : ", styleH)
    story.append(precautions_paragraph)
    story.append(Spacer(1, 12))
    precautions_list = ListFlowable([ListItem(Paragraph(p, styleN)) for p in precautions if p is not None],bulletType='bullet')
    story.append(precautions_list)
    story.append(Spacer(1, 12))

    # Workouts
    workouts_paragraph = Paragraph("Recommendations : ", styleH)
    story.append(workouts_paragraph)
    story.append(Spacer(1, 12))
    workouts_list = ListFlowable([ListItem(Paragraph(w, styleN)) for w in workouts], bulletType='bullet')
    story.append(workouts_list)
    story.append(Spacer(1, 12))

    # Diets
    diets_paragraph = Paragraph("Diets :", styleH)
    story.append(diets_paragraph)
    story.append(Spacer(1, 12))
    diets_list = ListFlowable([ListItem(Paragraph(d, styleN)) for d in diets], bulletType='bullet')
    story.append(diets_list)
    story.append(Spacer(1, 12))

    # Medications
    medications_paragraph = Paragraph("Medications :", styleH)
    story.append(medications_paragraph)
    story.append(Spacer(1, 12))
    medications_list = ListFlowable([ListItem(Paragraph(m, styleN)) for m in medications], bulletType='bullet')
    story.append(medications_list)
    story.append(Spacer(1, 12))

    # Build the PDF
    doc.build(story)
    print(f"PDF report generated successfully: {file_path}")

# Function to predict the disease using symptoms_df.csv for accuracy
def get_predicted_values(patient_symptoms):
    st.session_state.predicted = True
    
    # Load the symptoms dataset
    symptoms_df = pd.read_csv('Data/symptoms_df.csv')
    symptom_cols = ['Symptom_1', 'Symptom_2', 'Symptom_3', 'Symptom_4']
    
    # Normalize user symptoms: lowercase + underscores to match CSV format
    user_symptoms = set(s.strip().lower().replace(' ', '_') for s in patient_symptoms)
    
    best_disease = None
    best_score = -1
    
    for _, row in symptoms_df.iterrows():
        # Get all symptoms from this row, normalize them
        row_symptoms = set()
        for col in symptom_cols:
            val = str(row[col]).strip().lower().replace(' ', '_')
            if val and val != 'nan':
                row_symptoms.add(val)
        
        # Count matching symptoms between user selection and this row
        score = len(user_symptoms & row_symptoms)
        
        if score > best_score:
            best_score = score
            best_disease = row['Disease']
    
    return best_disease if best_disease else "Unknown"


def get_desc(predicted_value):
    predicted_description = desc_data[desc_data["Disease"] == predicted_value]["Description"].values[0]
    return predicted_description

def get_precautions(predicted_value):
    predicted_precaution = precautions_data[precautions_data['Disease'] == predicted_value].values[0][2:]
    return predicted_precaution

def print_precautions(p):
    c = 1
    for j in range(len(p)):
        if p[j] is not None:
            st.write(f"Precaution {c}. -> {p[j].title()}.")
            c += 1

def print_workout(w):
    c = 1
    for j in range(len(w)):
        st.write(f"Workout {c}. -> {w[j].title()}.")
        c += 1

def get_medication(predicted_value):
    med = medication_data[medication_data['Disease'] == predicted_value]['Medication'].values[0]
    return ast.literal_eval(med)

def get_workout(predicted_value):
    work = workout_data[workout_data['disease'] == predicted_value]["workout"].values
    return work

def get_diet(predicted_value):
    diet = diets_data[diets_data['Disease'] == predicted_value]['Diet'].values[0]
    return ast.literal_eval(diet)

#=========== Account creation =============
from account import account
from doctor_dashboard import show_doctor_dashboard

def icon(emoji: str):
    """Shows an emoji as a Notion-style page icon."""
    st.write(
        f'<span style="font-size: 78px; line-height: 0">{emoji}</span>',unsafe_allow_html=True,)

def detect_lang(text: str) -> str:
    detected_lang = detect(text)
    return detected_lang

def get_translation(src, target_lang):
    translator = Translator(to_lang=target_lang)
    translation = translator.translate(src)
    return translation

is_logged_in = st.session_state.get("signedOut", False)

if is_logged_in:
    with st.sidebar:
        user_role = st.session_state.get("user_role", "Patient")
        
        if user_role == "Doctor":
            # Doctor only sees Dashboard and Account
            options = ["Doctor Dashboard", "Account"]
            icons = ["clipboard-pulse", "gear"]
        else:
            # Patient sees everything else
            options = ["Home", "Recommendations", "Generate Report", "History", "Chat With Me", "WorkFlow", "Account"]
            icons = ["house", "magic", "book", "clock-history", "chat", "activity", "gear"]
            
        selected = option_menu(
            menu_title="HealthScript Advisor",
            options=options,
            icons=icons,
            menu_icon="app-indicator",
            default_index=0,
        )
else:
    selected = "Account"

if not is_logged_in and selected != "Account":
    st.title("Please Login First ⚠️")
    st.subheader("You are not logged in!")
    st.markdown("* Please go to the Account section.")
    st.stop()

if not is_logged_in and selected == "Account":
    account()
    st.stop()

# ========= HOME TAB =========
if selected == "Home" and user_role != "Doctor":
    show_home()
# ========= WORKFLOW TAB =========
elif selected == "WorkFlow" and user_role != "Doctor":
    show_workflow()
# ========= Accounts TAB =========
elif selected == "Account":
    account()
# ========= My Profile TAB =========
elif selected == "My Profile" and user_role != "Doctor":
    show_profile()

# ========= Recommendations TAB =========
elif selected == "Recommendations" and user_role != "Doctor":
    show_recommendations(
        symptoms_dict, symptoms_list, critical_diseases, 
        get_predicted_values, get_desc, get_precautions, 
        get_workout, get_diet, get_medication, 
        get_ayurveda_remedies, check_severity, save_prediction_history,
        check_multi_disease_risk
    )

# ========= Doctor Dashboard TAB =========
elif selected == "Doctor Dashboard":
    show_doctor_dashboard(db)

# ========= Report Generation TAB =========
elif selected == "Generate Report" and user_role != "Doctor":
    show_generate_report(generate_report)
# ========= HISTORY TAB =========
elif selected == "History" and user_role != "Doctor":
    show_history(db)
# ========= Chat with me TAB =========
elif selected == "Chat With Me" and user_role != "Doctor":
    show_chatbot()