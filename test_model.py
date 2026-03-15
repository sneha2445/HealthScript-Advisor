import pickle
import numpy as np
import mysql.connector

# Load the model
model = pickle.load(open('Model\\model.pkl', 'rb'))

# Get database mappings
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="sneha",
    database="docbuddy_db"
)
cursor = conn.cursor()

# Get symptoms
cursor.execute("SELECT symptom_name, symptom_id FROM symptoms")
rows = cursor.fetchall()
symptoms_dict = {str(row[0]).strip(): int(row[1]) for row in rows}

# Get diseases
cursor.execute("SELECT disease_id, disease_name FROM diseases")
diseases_dict = {int(row[0]): str(row[1]).strip() for row in cursor.fetchall()}

conn.close()

# Test with a few different symptom combinations
test_cases = [
    ['itching', 'skin_rash'],
    ['continuous_sneezing', 'cough'],
    ['high_fever', 'fatigue'],
    ['headache', 'dizziness'],
    ['burning_micturition', 'spotting_urination'],
]

print("Testing model predictions:\n")
for symptoms in test_cases:
    input_vector = np.zeros(len(symptoms_dict))
    for symptom in symptoms:
        if symptom in symptoms_dict:
            input_vector[symptoms_dict[symptom]] = 1
        else:
            print(f"Warning: symptom '{symptom}' not found in database")
    
    prediction = model.predict([input_vector])[0]
    disease_name = diseases_dict.get(prediction, "Unknown")
    print(f"Symptoms: {symptoms}")
    print(f"Predicted Disease: {disease_name}\n")
