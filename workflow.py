import streamlit as st

def show_workflow():
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title('HealthScript Advisor WorkFlow ⛑️')
        st.header("How Does It Work? 🤔")
        st.divider()
        st.subheader("1️⃣ Symptom Input 🤒")
        st.markdown('''
            * Simply enter the symptoms you're experiencing into our user-friendly interface. Whether it's a 
            headache, fever, or any other discomfort, HealthScript Advisor is here to help.
        ''')
        st.subheader("2️⃣ Disease Prediction 🔍")
        st.markdown('''
            * Our sophisticated machine learning model analyzes the symptoms and predicts the most likely diseases. This fast and efficient process ensures you get accurate information without the wait.
        ''')
        st.subheader("3️⃣ Detailed Descriptions 📖")
        st.markdown('''
            * Once a disease is predicted, HealthScript Advisor provides a comprehensive description of the condition. You'll learn about its causes, symptoms, and potential treatments, helping you understand your health better.
        ''')
        st.subheader("4️⃣ Personalized Recommendations 🌿💊")
        st.markdown('''
            HealthScript Advisor goes beyond mere diagnosis. It offers personalized recommendations for:
            * `Medicines` : Find out which over-the-counter or prescription medicines can help alleviate your 
            symptoms.
            * `Workout Plans` : Get tailored exercise routines to boost your overall health and manage your condition.
            * `Diets` : Discover dietary suggestions to support your recovery and maintain a balanced lifestyle.
            * `Precautions` : Learn about preventive measures to avoid aggravating your condition and protect your 
            health.
        ''')

    with col2:
        st.image("static/DocBuddy-WorkFlow-Tab.png")