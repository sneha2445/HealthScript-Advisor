import streamlit as st
import mysql.connector
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

@st.cache_resource
def get_mysql_connection():
    host = os.getenv("MYSQL_HOST", "localhost")
    
    # If host is a placeholder or we are on Streamlit Cloud trying to reach localhost
    if host == "your_database_host" or (host == "localhost" and os.getenv("STREAMLIT_RUNTIME_ENV") == "cloud"):
        return None
        
    try:
        conn = mysql.connector.connect(
            host=host,
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", "sneha"),
            database=os.getenv("MYSQL_DATABASE", "docbuddy_db"),
            connect_timeout=5 # Don't hang the app
        )
        return conn
    except Exception:
        return None

@st.cache_data
def load_db_mappings():
    conn = get_mysql_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Symptoms
            cursor.execute("SELECT symptom_name, symptom_id FROM symptoms")
            s_dict = {str(row[0]).strip(): int(row[1]) for row in cursor.fetchall()}
            s_list = list(s_dict.keys())
            
            # Diseases
            cursor.execute("SELECT disease_id, disease_name FROM diseases")
            d_list = {int(row[0]): str(row[1]).strip() for row in cursor.fetchall()}
            
            # Critical List
            cursor.execute("SELECT disease_name FROM critical_list")
            c_list = [str(row[0]).strip() for row in cursor.fetchall()]
            
            conn.close()
            return s_dict, d_list, s_list, c_list
        except Exception:
            return load_fallback_mappings()
    else:
        return load_fallback_mappings()

def load_fallback_mappings():
    try:
        sdf = pd.read_csv("Data/symptoms_df.csv")
        s_cols = ['Symptom_1', 'Symptom_2', 'Symptom_3', 'Symptom_4']
        all_s = []
        for col in s_cols:
            all_s.extend(sdf[col].dropna().unique())
        
        s_list = sorted(list(set(s.strip().replace('_', ' ').title() for s in all_s if isinstance(s, str))))
        s_dict = {s: i for i, s in enumerate(s_list)}
        
        ddf = pd.read_csv("Data/description.csv")
        d_list = {i: row['Disease'].strip() for i, row in ddf.iterrows()}
        c_list = ["Heart Attack", "AIDS", "Diabetes", "Hypertension", "Dengue", "Malaria"]
        
        return s_dict, d_list, s_list, c_list
    except Exception as e:
        st.error(f"Critical Error: Could not load data from DB or CSV. {e}")
        return {}, {}, [], []

@st.cache_data
def load_all_csv_data():
    data = {
        "symptoms": pd.read_csv("Data/symptoms_df.csv"),
        "precautions": pd.read_csv("Data/precautions_df.csv"),
        "workout": pd.read_csv("Data/workout_df.csv"),
        "description": pd.read_csv("Data/description.csv"),
        "diets": pd.read_csv("Data/diets.csv"),
        "medications": pd.read_csv("Data/medications.csv")
    }
    # Clean precautions
    data["precautions"].replace('nan', None, inplace=True)
    data["precautions"] = data["precautions"].where(pd.notnull(data["precautions"]), None)
    return data

def get_ayurvedic_remedy(disease_name):
    """Fetch ayurveda remedy from MySQL or fallback to CSV"""
    # 1. Try MySQL
    conn = get_mysql_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT remedy_text FROM ayurvedic_remedies WHERE disease_name = %s", (disease_name,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return row[0]
        except Exception:
            pass

    # 2. Try CSV Fallback (for Cloud/Offline)
    if os.path.exists("Data/ayurveda.csv"):
        try:
            df = pd.read_csv("Data/ayurveda.csv")
            match = df[df["Disease"].str.lower() == disease_name.lower()]
            if not match.empty:
                return match["Remedy"].values[0]
        except Exception:
            pass
            
    return "No specific Ayurvedic remedy found in database. Please consult an Ayurvedic practitioner."
