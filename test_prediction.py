import pickle
import numpy as np
import mysql.connector

# Simulate what happens in the app
conn = mysql.connector.connect(host='localhost', user='root', password='sneha', database='docbuddy_db')
cursor = conn.cursor()

# Get symptoms like app.py does
cursor.execute("SELECT symptom_name, symptom_id FROM symptoms")
rows = cursor.fetchall()
symptoms_dict = {str(row[0]).strip(): int(row[1]) for row in rows}
symptoms_list = list(symptoms_dict.keys())

# Get diseases
cursor.execute("SELECT disease_id, disease_name FROM diseases")
diseases_list = {int(row[0]): str(row[1]).strip() for row in cursor.fetchall()}

conn.close()

# Load model
model = pickle.load(open('Model\\model.pkl', 'rb'))

# Test various single symptoms
test_cases = [
    ['burning_micturition'],
    ['spotting_urination'],
    ['itching'],
    ['skin_rash'],
    ['cough'],
    ['high_fever'],
    ['headache'],
]

print("Testing individual symptoms:\n")
for test_symptoms in test_cases:
    input_vector = np.zeros(len(symptoms_dict))
    for symptom in test_symptoms:
        if symptom in symptoms_dict:
            input_vector[symptoms_dict[symptom]] = 1
    
    if np.sum(input_vector) > 0:
        prediction = model.predict([input_vector])[0]
        predicted_disease = diseases_list.get(prediction, "Unknown")
        print(f"Symptom: {test_symptoms[0]:30} -> Predicted: {predicted_disease}")
    else:
        print(f"Symptom: {test_symptoms[0]:30} -> NOT FOUND IN DICT")
