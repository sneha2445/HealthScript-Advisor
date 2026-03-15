import pandas as pd
import mysql.connector

# Get CSV symptoms
symptoms_df = pd.read_csv('Data\\symptoms_df.csv')
csv_symptoms = set()
for col in ['Symptom_1', 'Symptom_2', 'Symptom_3', 'Symptom_4']:
    csv_symptoms.update([str(s).strip() for s in symptoms_df[col].dropna().unique()])

# Get database symptoms
conn = mysql.connector.connect(host='localhost', user='root', password='sneha', database='docbuddy_db')
cursor = conn.cursor()
cursor.execute('SELECT symptom_name FROM symptoms ORDER BY symptom_id')
db_symptoms = set([str(row[0]).strip() for row in cursor.fetchall()])
conn.close()

print(f'CSV symptoms count: {len(csv_symptoms)}')
print(f'Database symptoms count: {len(db_symptoms)}')
print()

# Check for mismatches
in_csv_not_db = csv_symptoms - db_symptoms
in_db_not_csv = db_symptoms - csv_symptoms

print(f'In CSV but not in DB ({len(in_csv_not_db)}):')
for s in sorted(in_csv_not_db):
    print(f'  "{s}"')

print()
print(f'In DB but not in CSV ({len(in_db_not_csv)}):')
for s in sorted(list(in_db_not_csv)[:30]):
    print(f'  "{s}"')
