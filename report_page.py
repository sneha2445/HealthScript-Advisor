import streamlit as st
from utils.report_generator import generate_pdf_report
import os

def show_generate_report():
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.session_state.get("signedOut", False):
            st.title(f"Generate Medical Report 📃")
            st.divider()
            
            c1, c2 = st.columns(2)
            name = c1.text_input("Patient Name", placeholder="e.g. John Doe", value=st.session_state.get("user_name", ""))
            age = c2.number_input("Patient Age", min_value=1, max_value=120, value=25)
            
            # Automatically fetch phone number from session
            phone = st.session_state.get("user_phone", "N/A")
            
            if st.button("Generate Health Report ✨", use_container_width=True):
                if st.session_state.get("predicted"):
                    if name:
                        file_path = f"DocBuddy_{name.replace(' ', '_')}_Report.pdf"
                        try:
                            with st.spinner("Generating PDF..."):
                                generate_pdf_report(
                                    name, age, phone,
                                    st.session_state.disease,
                                    st.session_state.description,
                                    st.session_state.precautions,
                                    st.session_state.workout,
                                    st.session_state.diets,
                                    st.session_state.medications,
                                    st.session_state.vitals,
                                    st.session_state.bmi,
                                    file_path
                                )
                            
                            with open(file_path, "rb") as f:
                                st.download_button(
                                    label="Download PDF Report ✅",
                                    data=f,
                                    file_name=file_path,
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                            st.success("Report generated successfully!")
                        except Exception as e:
                            st.error(f"Error generating report: {e}")
                    else:
                        st.warning("Please enter a patient name.")
                else:
                    st.warning("No prediction data found. Please go to the Recommendations page first.")
        else:
            st.info("Please log in to generate reports.")
            
    with col2:
        st.image("static/DocBuddy-Generate-Report.png")