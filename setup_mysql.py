import mysql.connector
import pandas as pd
import os

def setup_database():
    DB_NAME = "docbuddy_db"
    # Found in app.py
    PASSWORD = "sneha" 
    
    print("Connecting to MySQL...")
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=PASSWORD
        )
        cursor = conn.cursor()
        
        # 1. Create Database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cursor.execute(f"USE {DB_NAME}")
        print(f"Database '{DB_NAME}' ready.")

        # 2. Create Tables
        print("Creating tables...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS symptoms (
                symptom_id INT AUTO_INCREMENT PRIMARY KEY,
                symptom_name VARCHAR(255) UNIQUE NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS diseases (
                disease_id INT AUTO_INCREMENT PRIMARY KEY,
                disease_name VARCHAR(255) UNIQUE NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS critical_list (
                id INT AUTO_INCREMENT PRIMARY KEY,
                disease_name VARCHAR(255) UNIQUE NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ayurvedic_remedies (
                remedy_id INT AUTO_INCREMENT PRIMARY KEY,
                disease_name VARCHAR(255),
                remedy_text TEXT
            )
        """)
        
        # 3. Populate Symptoms
        print("Populating symptoms...")
        if os.path.exists("Data/symptoms_df.csv"):
            df = pd.read_csv("Data/symptoms_df.csv")
            s_cols = ['Symptom_1', 'Symptom_2', 'Symptom_3', 'Symptom_4']
            all_s = []
            for col in s_cols:
                all_s.extend(df[col].dropna().unique())
            
            unique_symptoms = sorted(list(set(s.strip().replace('_', ' ').title() for s in all_s if isinstance(s, str))))
            for s in unique_symptoms:
                try:
                    cursor.execute("INSERT IGNORE INTO symptoms (symptom_name) VALUES (%s)", (s,))
                except: pass
        
        # 4. Populate Diseases
        print("Populating diseases...")
        if os.path.exists("Data/description.csv"):
            ddf = pd.read_csv("Data/description.csv")
            for _, row in ddf.iterrows():
                try:
                    cursor.execute("INSERT IGNORE INTO diseases (disease_name) VALUES (%s)", (row['Disease'].strip(),))
                except: pass
        
        # 5. Populate Critical List
        print("Populating critical list...")
        critical_defaults = ["Heart Attack", "AIDS", "Diabetes", "Hypertension", "Dengue", "Malaria", "Cancer"]
        for d in critical_defaults:
            try:
                cursor.execute("INSERT IGNORE INTO critical_list (disease_name) VALUES (%s)", (d,))
            except: pass

        # 6. Ayurvedic Remedies (from CSV)
        print("Populating ayurvedic remedies from CSV...")
        if os.path.exists("Data/ayurveda.csv"):
            adf = pd.read_csv("Data/ayurveda.csv")
            for _, row in adf.iterrows():
                try:
                    cursor.execute(
                        "INSERT IGNORE INTO ayurvedic_remedies (disease_name, remedy_text) VALUES (%s, %s)", 
                        (row['Disease'].strip(), row['Remedy'].strip())
                    )
                except: pass
        else:
            # Fallback for very basic setup
            remedies = [
                ("Fungal infection", "Apply neem oil or turmeric paste to the affected area."),
                ("Allergy", "Consume a teaspoon of honey or drink ginger tea."),
                ("Diabetes", "Include bitter gourd (Karela) and fenugreek seeds in your diet."),
                ("Hypertension", "Practice Savasana and take Ashwagandha supplements.")
            ]
            for d, r in remedies:
                try:
                    cursor.execute("INSERT IGNORE INTO ayurvedic_remedies (disease_name, remedy_text) VALUES (%s, %s)", (d, r))
                except: pass

        conn.commit()
        print("\n✅ Database Setup Complete!")
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        print("\nMake sure MySQL is running and the password in the script is correct.")

if __name__ == "__main__":
    setup_database()
