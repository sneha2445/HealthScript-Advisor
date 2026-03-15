import streamlit as st

def show_recommendations(symptoms_dict, symptoms_list, critical_diseases, 
                         get_predicted_values, get_desc, get_precautions, 
                         get_workout, get_diet, get_medication, 
                         get_ayurveda_remedies, check_severity, save_prediction_history,
                         check_multi_disease_risk):
   
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.session_state.get("signedOut", False):
            st.title(f"Welcome {st.session_state.get('user_name','User')} 🎉")
            st.header("DocBuddy Recommendation Center 🔮")
            st.divider()

            # --- STEP 1: PATIENT DETAILS ---
            st.subheader("Step 1: Patient Details 👤")
            p1, p2, p3 = st.columns(3)
            gender = p1.radio("Gender", ["Male", "Female", "Other"], horizontal=True, key="rec_gender")
            age = p2.number_input("Age", 1, 120, 25, key="rec_age")
            is_pregnant = False
            if gender == "Female":
                preg = p3.radio("Pregnant? 🤰", ["No", "Yes"], horizontal=True, key="rec_preg")
                is_pregnant = (preg == "Yes")

            st.subheader("Existing Medical Conditions 🏥")
            options = ["None"] + critical_diseases + ["Other"]
            existing = st.multiselect("Select if any:", options, default=["None"], key="rec_cond")
            other_cond = st.text_input("Specify 'Other':", key="rec_other") if "Other" in existing else ""
            st.divider()

            # --- STEP 2: VITALS ---
# --- BMI CALCULATOR ---
            st.subheader("Step 2: Enter Vitals & BMI 💓")
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
                # Calculate BMI
                bmi = weight / ((height_cm / 100) ** 2)
                st.metric(label="Calculated BMI", value=f"{bmi:.1f}")
                
                # Determine BMI Category
                if bmi < 18.5:
                    bmi_status = "Underweight 🔵"
                elif 18.5 <= bmi <= 24.9:
                    bmi_status = "Normal weight 🟢"
                elif 25 <= bmi <= 29.9:
                    bmi_status = "Overweight 🟡"
                else:
                    bmi_status = "Obese 🔴"
                st.caption(f"Status: **{bmi_status}**")    
            st.divider()

            # --- STEP 3: SYMPTOMS ---
            st.subheader("Step 3: Select Symptoms 🤒")
            symptoms = st.multiselect("Select Patient's Symptoms below 👇🏻", symptoms_list, default=[], key="rec_symptoms")
            
            if st.button("Predict Disease & Health Status 🔮", key="rec_predict"):
                if not symptoms:
                    st.warning("Please Select Symptoms first from the Dropdown List ⚠️")
                else:
                    #1. AI Prediction
                    disease = get_predicted_values(symptoms)
                    st.session_state.disease = disease
                    st.session_state.description = get_desc(disease)
                    st.session_state.precautions = get_precautions(disease)
                    st.session_state.workout = get_workout(disease)
                    st.session_state.diets = get_diet(disease)
                    st.session_state.medications = get_medication(disease)
                    
                    # 2. Get Ayurveda & Severity
                    ayurveda = get_ayurveda_remedies(disease)
                    status, color, warnings = check_severity(spo2, temp, bp)
                    
                    vitals = {
                        "spo2": spo2,
                        "temp": temp,
                        "bp": bp,
                        "weight": weight,
                        "height": height_cm
                    }
                    # Store in session state for report generation
                    st.session_state.vitals = vitals
                    st.session_state.bmi = bmi
                    
                    save_prediction_history(
                        st.session_state.get("user_mail"), 
                        st.session_state.get("user_name"), 
                        disease, status, symptoms, bmi,
                        age, gender, existing, vitals
                    )

                    # 3. Check 5-day multi-disease risk
                    multi_risk, risk_diseases = check_multi_disease_risk(st.session_state.get("user_mail"))
                    st.session_state["multi_disease_risk"] = multi_risk
                    st.session_state["risk_diseases"] = risk_diseases

                    # --- SAFETY LOGIC ---
                    show_meds = True
                    med_warn = ""

                    if multi_risk:
                        show_meds = False
                        med_warn = None  # handled separately below

                    elif is_pregnant:
                        show_meds, med_warn = False, "⚠️ MEDICATIONS HIDDEN: You are Pregnant.  Please consult a Gynecologist for safe prescriptions."
                    elif other_cond.strip() != "":
                        show_meds, med_warn = False, f"⚠️ MEDICATIONS HIDDEN: Since you mentioned a specific condition '{other_cond}'requires  safe recommend medicine. Please consult a doctor."
                    elif any(c in critical_diseases for c in existing if c != "None"):
                        show_meds, med_warn = False, "⚠️ MEDICATIONS HIDDEN: Existing critical condition detected."
                    elif 1 <= age <= 5:
                        show_meds, med_warn = False, "⚠️ MEDICATIONS HIDDEN: Pediatric case, needs specialist consult."
                    elif status.startswith("CRITICAL"):
                        show_meds, med_warn = False, "⚠️ MEDICATIONS HIDDEN: Vitals are CRITICAL. Go to Hospital  immediately."

                    # ── 🚨 MULTI-DISEASE URGENT ALERT ──────────────────────
                    if multi_risk:
                        st.markdown("""
                        <div style='background-color:#ff1744; padding:18px; border-radius:10px; margin-bottom:15px;'>
                            <h3 style='color:white; margin:0;'>🚨 URGENT: CONSULT A DOCTOR IMMEDIATELY</h3>
                        </div>""", unsafe_allow_html=True)
                        st.error(
                            f"**⚠️ Multiple different diseases have been detected for your account in the past 5 days.**\n\n"
                            f"Diseases recorded: **{', '.join(risk_diseases)}**\n\n"
                            "This pattern of varying symptoms and diseases is medically concerning. "
                            "**Medications cannot be recommended safely.** "
                            "Please visit a qualified doctor or hospital on an **urgent basis** for a proper diagnosis."
                        )
                        st.info("📞 Emergency: 112 (India) | 911 (USA) | 999 (UK)")
                        st.divider()

                    # Results
                    st.subheader(f"You have : '{disease}' 🤒")
                    st.write(st.session_state.description)
                    st.markdown(f"<div style='background-color:{color}; padding:10px; color:white;'>Status: {status}</div>", unsafe_allow_html=True)
                    st.divider()
                #  Display
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: 
                        st.subheader("⚠️ Precautions")
                        [st.write(f"• {p}") for p in st.session_state.precautions if p]
                    with c2: 
                        st.subheader("✨ Workout")
                        [st.write(f"👉 {w}") for w in st.session_state.workout]
                    with c3:
                        st.subheader("🍎 Diet Plan")
                        for diet in st.session_state.diets:
                            st.write(f"➕ {diet.title()}")
                    with c4: 
                        st.subheader("💊 Medications")
                        if show_meds:
                            [st.write(f"✔️ {m}") for m in st.session_state.medications]
                        elif med_warn:
                            st.error(med_warn)
                        else:
                            st.error("🚨 Medications withheld — multiple diseases detected. See urgent alert above.")
                   
                    
                    # Ayurveda Section
                    st.divider()
                    st.subheader("🌿 Ayurveda & Home Remedies")
                    for tip in ayurveda:
                        st.write(f"🍵 {tip}")
                
        else:
            st.title("Please Login First ⚠️")
            st.subheader("You are not logged in!")
            st.markdown("* Please go back to the Account section.")
            st.markdown("* Then go to the Login Page and Login Yourself.")
   
    with col2:
        st.image(r"static\\Docbuddy-Recommendations.png")

