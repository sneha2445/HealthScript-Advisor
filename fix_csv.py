import pandas as pd

# Load the CSV
df = pd.read_csv('Data\\symptoms_df.csv')

# Replace symptom names to match database format
replace_map = {
    'dischromic _patches': 'dischromic_patches',
    'foul_smell_of urine': 'foul_smell_of_urine',
    'spotting_ urination': 'spotting_urination'
}

# Replace in all Symptom columns
for col in ['Symptom_1', 'Symptom_2', 'Symptom_3', 'Symptom_4']:
    for old, new in replace_map.items():
        df[col] = df[col].replace(old, new)

# Save back
df.to_csv('Data\\symptoms_df.csv', index=False)
print("CSV fixed!")
print(f"Replaced {len(replace_map)} symptom names")

# Verify
print("\nVerified replacements:")
for col in ['Symptom_1', 'Symptom_2', 'Symptom_3', 'Symptom_4']:
    for new_name in replace_map.values():
        count = (df[col] == new_name).sum()
        if count > 0:
            print(f"  {new_name}: {count} occurrences")
