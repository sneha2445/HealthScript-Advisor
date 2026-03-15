import streamlit as st

def show_home():
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title('HealthScript Advisor 🩺')
        st.header("Your Personalized 🪄 Doctor Buddy you can call me 👨🏻‍⚕️")
        st.divider()
        st.header("About 👨🏻‍⚕️🩺")
        st.markdown('''
        HealthScript Advisor is an innovative application designed to revolutionize the way you manage your health.
        Our intelligent machine learning model accurately predicts potential diseases based on your symptoms, 
        providing you with timely insights and empowering you to take control of your well-being. 🏥✨
        ''')
        st.markdown('''
        ### Join the `HealthScript Advisor` Community 😃
        Take charge of your health with HealthScript Advisor! 🌟 Download the app today and experience the future of health management.
        Connect with us on social media and be part of a community that values well-being and proactive health management.
        ''')
        st.markdown("_Stay healthy, stay informed, and let HealthScript Advisor be your trusted health companion_ 💪❤️")
        st.markdown("#### Get Started Now!")
        st.markdown("HealthScript Advisor is here to help you live your healthiest life!")

    with col2:
        st.image("static/DocBuddy-Home.png")