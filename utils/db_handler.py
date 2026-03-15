import streamlit as st
import mysql.connector
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from utils.config import get_secret

@st.cache_resource
def get_mysql_connection():
    # Use the safe get_secret utility
    host = get_secret("MYSQL_HOST", "localhost")
    user = get_secret("MYSQL_USER", "root")
    password = get_secret("MYSQL_PASSWORD", "sneha")
    database = get_secret("MYSQL_DATABASE", "docbuddy_db")
    
    # 1. Skip if it's a known placeholder
    if not host or host.strip() in ["", "your_database_host", "your-mysql-host-here"]:
        return None
        
    # 2. Skip if on Cloud and trying to hit localhost (impossible)
    is_cloud = os.getenv("STREAMLIT_RUNTIME_ENV") == "cloud" or "STREAMLIT_SERVER_PORT" in os.environ
    if is_cloud and host == "localhost":
        return None
        
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            connect_timeout=3 # Fast timeout
        )
        return conn
    except Exception:
        # Completely silent - fallback handles the rest
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

def get_ayurveda_remedies(disease_name):
    """Fetch ayurveda remedies from MySQL or fallback to CSV (returns list)"""
    # 1. Try MySQL
    conn = get_mysql_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT remedy_text FROM ayurvedic_remedies WHERE disease_name = %s", (disease_name,))
            rows = cursor.fetchall()
            conn.close()
            if rows:
                return [row[0] for row in rows]
        except Exception:
            pass

    # 2. Try CSV Fallback (for Cloud/Offline)
    if os.path.exists("Data/ayurveda.csv"):
        try:
            df = pd.read_csv("Data/ayurveda.csv")
            clean_search = str(disease_name).strip().lower()
            df["Disease_Clean"] = df["Disease"].str.strip().str.lower()
            
            match = df[df["Disease_Clean"] == clean_search]
            if not match.empty:
                return [match["Remedy"].values[0]]
        except Exception:
            pass
            
    return ["Consult a professional doctor."]
