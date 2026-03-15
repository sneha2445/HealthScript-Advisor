import streamlit as st
import pandas as pd
from firebase_admin import firestore

def show_doctor_dashboard(db):
    # --- DOCTOR PROFILE HEADER ---
    st.markdown("""
        <div style='background-color:#003366; padding:20px; border-radius:10px; color:white; margin-bottom:25px;'>
            <h2 style='margin:0;'>👨‍⚕️ DR. Pramoad Suryakant Tripathi</h2>
            <p style='font-size:18px; margin:5px 0;'><b>MBBS | 10+ Years of Experience</b></p>
            <p style='margin:2px 0;'>📍 Clinic Center: Indira Nagar, Thane West, 400604, Mumbai, Maharashtra</p>
            <p style='margin:2px 0;'>⏰ Timing: 10:00 AM - 11:00 PM</p>
        </div>
    """, unsafe_allow_html=True)

    # --- DOCTOR CONTACT INFO ---
    with st.container(border=True):
        st.subheader("📋 Doctor Contact Information")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**📧 Email:** {st.session_state.get('user_mail', 'pramoadtri24@gamil.com')}")
        with col2:
            # Get current phone from Firebase Auth or use default
            try:
                from firebase_admin import auth as firebase_auth
                uid = st.session_state.get('user_uid', 'Tripathipramoad24')
                user_record = firebase_auth.get_user(uid)
                phone = user_record.phone_number or "8197964567"
            except:
                # Fallback to default doctor phone
                phone = "8197964567"
            st.markdown(f"**📱 Phone:** {phone}")
    
    st.title("Patient Monitoring Panel")
    st.markdown("---")

    # Fetch all records from 'history' collection
    try:
        history_ref = db.collection("history").order_by("timestamp", direction=firestore.Query.DESCENDING)
        docs = history_ref.stream()

        patient_records = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            patient_records.append(data)

        if not patient_records:
            st.info("No patient records found.")
            return

        # Display Patients in an expandable list
        for record in patient_records:
            severity = record.get('severity_status', 'Mild')
            header_color = "red" if "CRITICAL" in severity else "orange" if "Moderate" in severity else "green"
            
            with st.expander(f"👤 Patient: {record.get('patient_name')} | Disease: {record.get('disease')} | Status: {severity}"):
                st.markdown(f"### Detailed Patient Record")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Name:** {record.get('patient_name')}")
                    st.write(f"**Gender:** {record.get('gender', 'N/A')}")
                    st.write(f"**Age:** {record.get('age', 'N/A')} Years")
                    st.write(f"**Symptoms Selected:** {', '.join(record.get('symptoms', []))}")
                    st.write(f"**Existing Diseases:** {', '.join(record.get('existing_diseases', []))}")

                with col2:
                    st.markdown("**📉 Vitals & BMI Data**")
                    vitals = record.get('vitals', {})
                    st.write(f"- **SpO2:** {vitals.get('spo2', 'N/A')}%")
                    st.write(f"- **Body Temp:** {vitals.get('temp', 'N/A')}°F")
                    st.write(f"- **Systolic BP:** {vitals.get('bp', 'N/A')}")
                    st.write(f"- **Height:** {vitals.get('height', 'N/A')} cm")
                    st.write(f"- **Weight:** {vitals.get('weight', 'N/A')} kg")
                    bmi_val = record.get('bmi', 'N/A')
                    st.write(f"- **Calculated BMI:** {f'{float(bmi_val):.1f}' if bmi_val != 'N/A' else 'N/A'}")
                    st.write(f"**🩺 Predicted Disease:** {record.get('disease')}")

                st.markdown("---")
                # Urgent Consultation Trigger
                if "CRITICAL" in severity:
                    st.error("⚠️ **CRITICAL CONDITION DETECTED**")
                    if st.button(f"🚨 CONTACT PATIENT IMMEDIATELY", key=f"urg_{record['id']}", type="primary"):
                        db.collection("consultations").add({
                            "patient_email": record['user_email'],
                            "doctor_name": "DR. Pramoad Suryakant Tripathi",
                            "advice": "URGENT: Your symptoms are serious. Please visit our clinic at Indira Nagar, Thane West immediately for your safety.",
                            "urgency": "IMMEDIATE",
                            "original_case_id": record['id'],
                            "timestamp": firestore.SERVER_TIMESTAMP
                        })
                        st.error(f"Emergency Consultation Request sent to {record['patient_name']}!")
                
                consultation_note = st.text_area("Doctor's Advice / Consultation Note", key=f"note_{record['id']}")
                if st.button("Send Advice", key=f"send_{record['id']}"):
                    if consultation_note.strip():
                        db.collection("consultations").add({

                            "doctor_name": "DR. Pramoad Suryakant Tripathi",
                            "advice": consultation_note,
                            "urgency": "Standard",
                            "original_case_id": record['id'],
                            "timestamp": firestore.SERVER_TIMESTAMP
                        })
                        st.success(f"Advice sent to {record['patient_name']}!")

    except Exception as e:
        # Suppress USER_NOT_FOUND errors for doctor dashboard
        if "USER_NOT_FOUND" in str(e):
            st.warning("Doctor profile information not found in Firebase Auth. Dashboard functionality is limited.")
        else:
            st.error(f"Error fetching patient data: {e}")

if __name__ == "__main__":
    # For testing, assuming db is passed
    pass
