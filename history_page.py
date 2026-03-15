import streamlit as st
import pandas as pd

def show_history(db):
    """
    Displays the history tab. Requires the initialized firestore db object.
    """
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.session_state.get("signedOut", False):
            st.title(f"Patient History: {st.session_state.user_name} 📅")
            st.divider()

            # 1. Fetch Data from Firestore
            try:
                # Security check to ensure user_mail exists
                current_user_email = st.session_state.get("user_mail", "")
                
                if not current_user_email:
                    st.warning("User email not found. Please log in again.")
                else:
                    # Query: Get documents where 'user_email' matches the logged-in user
                    docs = db.collection('history').where('user_email', '==', current_user_email).stream()
                    
                    history_data = []
                    for doc in docs:
                        data = doc.to_dict()
                        history_data.append(data)
                    
                    if len(history_data) > 0:
                        # Convert to Pandas DataFrame for easy display
                        df = pd.DataFrame(history_data)
                        
                        # Convert Timestamp to readable date
                        df['date'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
                        
                        # Select relevant columns to display
                        display_df = df[['date', 'patient_name', 'disease', 'severity_status', 'symptoms']]
                        
                        # --- VIZUALIZATION: DISEASE FREQUENCY ---
                        st.subheader("🛡️ Health Condition Statistics")
                        disease_counts = display_df['disease'].value_counts()
                        st.bar_chart(disease_counts)
                        
                        # --- DATA TABLE ---
                        st.subheader("📋 Past Records")
                        st.dataframe(display_df, use_container_width=True)

                        # --- DOCTOR CONSULTATIONS ---
                        st.divider()
                        st.subheader("👨‍⚕️ Doctor Consultations & Advice")
                        try:
                            consult_docs = db.collection('consultations').where('patient_email', '==', current_user_email).stream()
                            consults = []
                            for cdoc in consult_docs:
                                cdata = cdoc.to_dict()
                                consults.append(cdata)
                            
                            if consults:
                                for consult in consults:
                                    urgency = consult.get('urgency', 'Standard')
                                    with st.chat_message("assistant", avatar="👨‍⚕️"):
                                        st.write(f"**From Dr. {consult.get('doctor_name', 'Professional')}**")
                                        if urgency == "IMMEDIATE":
                                            st.error(f"🚨 **URGENT CONSULTATION REQUESTED:** {consult.get('advice')}")
                                            st.warning("⚠️ Please contact a doctor or visit the nearest clinic immediately for your safety.")
                                        else:
                                            st.info(consult.get('advice', 'No advice provided.'))
                                        st.caption(f"Received on: {consult.get('timestamp')}")
                            else:
                                st.write("No consultations received yet. If your case is marked 'CRITICAL', a doctor will review it and provide advice here.")
                        except Exception as e:
                            st.error(f"Error fetching consultations: {e}")

                        # Option to Download History
                        csv = display_df.to_csv(index=False).encode('utf-8')
                        file_name = f"{st.session_state.user_name}_medical_history.csv"
                        st.download_button(
                            label="Download History as CSV 📥",
                            data=csv,
                            file_name=file_name,
                            mime='text/csv',
                        )
                    else:
                        st.info("No history found. Go to 'Recommendations' and make a prediction first!")
            
            except Exception as e:
                st.error(f"Error fetching history: {e}")
                st.write("Make sure your Firestore Database is enabled in the Firebase Console.")

        else:
            st.title("Please Login First ⚠️")
            st.subheader("You are not logged in!")
            st.markdown("* Please go back to the Account section.")
            st.markdown("* Then go to the Login Page and Login Yourself.")
            
    with col2:
        st.image("static/DocBuddy-Recommendations.png")