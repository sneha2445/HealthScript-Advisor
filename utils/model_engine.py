import pandas as pd
import ast
import streamlit as st

def get_predicted_values(patient_symptoms, symptoms_df):
    # Normalize user symptoms
    user_symptoms = set(s.strip().lower().replace(' ', '_') for s in patient_symptoms)
    
    symptom_cols = ['Symptom_1', 'Symptom_2', 'Symptom_3', 'Symptom_4']
    best_disease = None
    best_score = -1
    
    for _, row in symptoms_df.iterrows():
        row_symptoms = set()
        for col in symptom_cols:
            val = str(row[col]).strip().lower().replace(' ', '_')
            if val and val != 'nan':
                row_symptoms.add(val)
        
        score = len(user_symptoms & row_symptoms)
        if score > best_score:
            best_score = score
            best_disease = row['Disease']
    
    return best_disease if best_disease else "Unknown"

def get_disease_details(disease, data):
    from utils.db_handler import get_ayurvedic_remedy
    details = {}
    
    # Description
    desc_row = data["description"][data["description"]["Disease"] == disease]
    details["description"] = desc_row["Description"].values[0] if not desc_row.empty else "No description available."
    
    # Precautions
    prec_row = data["precautions"][data["precautions"]['Disease'] == disease]
    details["precautions"] = prec_row.values[0][2:] if not prec_row.empty else []
    
    # Medications
    med_row = data["medications"][data["medications"]['Disease'] == disease]
    details["medications"] = ast.literal_eval(med_row['Medication'].values[0]) if not med_row.empty else []
    
    # Workout
    work_row = data["workout"][data["workout"]['disease'] == disease]
    details["workout"] = work_row["workout"].values if not work_row.empty else []
    
    # Diet
    diet_row = data["diets"][data["diets"]['Disease'] == disease]
    details["diets"] = ast.literal_eval(diet_row['Diet'].values[0]) if not diet_row.empty else []
    
    # Ayurveda
    details["ayurveda"] = get_ayurvedic_remedy(disease)

    return details
