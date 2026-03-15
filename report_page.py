import streamlit as st

def show_generate_report(generate_report_func):
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.session_state.get("signedOut", False):
            st.title(f"Welcome {st.session_state.user_name} 🎉")
            st.header("HealthScript Advisor Medical Report Generation 📃")
            st.divider()
            
            col3, col4 = st.columns([2, 2])
            with col3:
                name = st.text_input("Enter the patient Name below", placeholder="Name")
            with col4:
                age = st.number_input("Enter the patient Age below", placeholder="Age", value=None, min_value=1, max_value=120)
            
            generate = st.button("Generate HealthScript Advisor Report ✨")
            st.warning("⚠️ This is an automated AI generated report prepared by HealthScript Advisor.")
            st.write("It's always better to see a Doctor and consult them before taking any step further!")
            st.divider()
            
            if generate:
                if st.session_state.predicted:
                    if name and age:
                        # Yahan generate_report_func aayega taaki error na aaye
                        generate_report_func(
                            name,
                            age,
                            disease=st.session_state.disease,
                            description=st.session_state.description,
                            precautions=st.session_state.precautions,
                            workouts=st.session_state.workout,
                            diets=st.session_state.diets,
                            medications=st.session_state.medications,
                            vitals=st.session_state.vitals,
                            bmi=st.session_state.bmi,
                            file_path=f"DocBuddy_{name.title()}_Report.pdf"
                        )
                        with open(f"DocBuddy_{name.title()}_Report.pdf", "rb") as file:
                            st.download_button(
                                label="Download Generated Report ✅",
                                data=file,
                                file_name=f"DocBuddy_{name.title()}_Report.pdf",
                                mime="pdf",
                            )
                    else:
                        st.warning("⚠️ Please enter correct Name/Age to proceed")
                else:
                    st.warning("⚠️ It seems like you haven't got your Recommendations!")
                    st.markdown("* Go to `Recommendations` tab first on the top left sidebar.")
                    st.markdown("* Get your `Recommendations` there first.")
                    st.markdown("* Then comeback here and apply for `Report Generation`.")
        else:
            st.title("Please Login First ⚠️")
            st.subheader("Log in first, to Generate Report")
            st.markdown("* Please go back to the Account section.")
            st.markdown("* Then go to the Login Page and Login Yourself.")
            
    with col2:
        st.image(r"static\\DocBuddy-Generate-Report.png")