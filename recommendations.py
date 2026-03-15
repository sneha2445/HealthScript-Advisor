import streamlit as st

def show_recommendations_page(symptoms_dict, symptoms_list, critical_diseases, 
                          predict_wrapper, check_severity, save_prediction_history, db):
   
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.session_state.get("signedOut", False):
            st.title(f"Welcome {st.session_state.get('user_name','User')}")
            st.header("Medical Recommendation Center")
            st.divider()

            # --- STEP 1: PATIENT DETAILS ---
            st.subheader("Step 1: Patient Details")
            p1, p2, p3 = st.columns(3)
            gender = p1.radio("Gender", ["Male", "Female", "Other"], horizontal=True, key="rec_gender")
            age = p2.number_input("Age", 1, 120, 25, key="rec_age")
            is_pregnant = False
            if gender == "Female":
                preg = p3.radio("Pregnant?", ["No", "Yes"], horizontal=True, key="rec_preg")
                is_pregnant = (preg == "Yes")

            st.subheader("Existing Medical Conditions")
            options = ["None"] + critical_diseases + ["Other"]
            existing = st.multiselect("Select if any:", options, default=["None"], key="rec_cond")
            other_cond = st.text_input("Specify 'Other':", key="rec_other") if "Other" in existing else ""
            st.divider()

            # --- STEP 2: VITALS ---
            st.subheader("Step 2: Enter Vitals and BMI")
            v1, v2, v3 = st.columns(3)
            spo2 = v1.number_input("SpO2 Level (%)", 70, 100, 98, key="rec_spo2")
            temp = v2.number_input("Body Temperature (°F)", 95.0, 108.0, 98.6, key="rec_temp")
            bp = v3.number_input("Systolic BP", 80, 220, 120, key="rec_bp")
            
            st.markdown("**Body Mass Index (BMI) Calculator ⚖️**")
            bmi_col1, bmi_col2, bmi_col3 = st.columns(3)
            
            with bmi_col1:
                weight = st.number_input("Weight (kg)", 10.0, 300.0, 70.0, key="rec_weight")
            with bmi_col2:
                height_cm = st.number_input("Height (cm)", 50.0, 250.0, 170.0, key="rec_height")
            with bmi_col3:
                bmi = weight / ((height_cm / 100) ** 2)
                st.metric(label="Calculated BMI", value=f"{bmi:.1f}")
                
                if bmi < 18.5: bmi_status = "Underweight 🔵"
                elif 18.5 <= bmi <= 24.9: bmi_status = "Normal weight 🟢"
                elif 25 <= bmi <= 29.9: bmi_status = "Overweight 🟡"
                else: bmi_status = "Obese 🔴"
                st.write(f"**Status:** {bmi_status}")
            
            # Return values for use in the main function
            vitals_data = {"spo2": spo2, "temp": temp, "bp": bp, "weight": weight, "height": height_cm, "bmi": bmi}
            st.divider()

            # --- STEP 3: SYMPTOMS ---
            st.subheader("Step 3: Select Symptoms 🤒")
            symptoms = st.multiselect("Select Patient's Symptoms below 👇🏻", symptoms_list, default=[], key="rec_symptoms")
            
            if st.button("Predict Disease & Health Status 🔮", key="rec_predict"):
                if not symptoms:
                    st.warning("Please Select Symptoms first from the Dropdown List ⚠️")
                else:
                    with st.status("Analyzing symptoms...", expanded=True) as status_box:
                        disease, details = predict_wrapper(symptoms)
                        
                        st.session_state.disease = disease
                        st.session_state.description = details["description"]
                        st.session_state.precautions = details["precautions"]
                        st.session_state.workout = details["workout"]
                        st.session_state.diets = details["diets"]
                        st.session_state.medications = details["medications"]
                        st.session_state.ayurveda = details["ayurveda"]
                        
                        sev_status, color, warnings = check_severity(spo2, temp, bp)
                        vitals = {"spo2": spo2, "temp": temp, "bp": bp, "weight": weight, "height": height_cm}
                        
                        st.session_state.vitals = vitals
                        st.session_state.bmi = bmi
                        
                        save_prediction_history(
                            st.session_state.get("user_mail"), 
                            st.session_state.get("user_name"), 
                            disease, sev_status, symptoms, bmi,
                            age, gender, existing, vitals
                        )
                        status_box.update(label="Analysis Complete!", state="complete", expanded=False)

                    # --- SAFETY LOGIC & DISPLAY ---
                    # (Keep the existing safety logic but cleaner)
                    show_meds = True
                    med_warn = ""

                    if is_pregnant:
                        show_meds, med_warn = False, "⚠️ MEDICATIONS HIDDEN: Pregnant case."
                    elif other_cond.strip() != "":
                        show_meds, med_warn = False, f"⚠️ MEDICATIONS HIDDEN: Specific condition '{other_cond}'."
                    elif any(c in critical_diseases for c in existing if c != "None"):
                        show_meds, med_warn = False, "⚠️ MEDICATIONS HIDDEN: Critical condition detected."
                    elif 1 <= age <= 5:
                        show_meds, med_warn = False, "⚠️ MEDICATIONS HIDDEN: Pediatric case."
                    elif sev_status.startswith("CRITICAL"):
                        show_meds, med_warn = False, "⚠️ MEDICATIONS HIDDEN: Vitals are CRITICAL."

                    # Results
                    st.subheader(f"Predicted Condition: '{disease}' 🤒")
                    st.write(st.session_state.description)
                    st.markdown(f"<div style='background-color:{color}; padding:10px; color:white; border-radius:5px;'>Status: {sev_status}</div>", unsafe_allow_html=True)
                    st.divider()

                    c1, c2, c3, c4 = st.columns(4)
                    with c1: 
                        st.subheader("⚠️ Precautions")
                        for p in st.session_state.precautions:
                            if p: st.write(f"• {p}")
                    with c2: 
                        st.subheader("✨ Workout")
                        for w in st.session_state.workout: st.write(f"👉 {w}")
                    with c3:
                        st.subheader("🍎 Diet Plan")
                        for d in st.session_state.diets: st.write(f"➕ {d.title()}")
                    with c4: 
                        st.subheader("💊 Medications")
                        if show_meds:
                            for m in st.session_state.medications: st.write(f"✔️ {m}")
                        else:
                            st.error(med_warn)

                    st.divider()
                    st.subheader("🌿 Ayurvedic Remedies")
                    st.info(st.session_state.get("ayurveda", "No remedy available."))
   
    with col2:
        st.image("static/DocBuddy-Recommendations.png")

