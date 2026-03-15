import streamlit as st
from groq import Groq
from typing import Generator
from utils.config import get_secret

def medical_chatbot():
    import os
    
    # 1. Proactive Safety: Ensure GROQ environment variables are strings
    # Streamlit Cloud sometimes puts dicts/tables from Secrets into os.environ
    for env_key in list(os.environ.keys()):
        if env_key.startswith("GROQ_") and env_key != "GROQ_API_KEY":
            if not isinstance(os.environ[env_key], str):
                del os.environ[env_key]

    # 2. Key Retrieval
    raw_key = get_secret("GROQ_API_KEY") or get_secret("Grok") or get_secret("groq_api_key")
    
    # Ensure it's a string or None
    if raw_key is not None and not isinstance(raw_key, str):
        # If it's a dict or other object, we can't use it directly
        st.error(f"❌ Groq API Key found but it is format '{type(raw_key).__name__}'. Please make sure it is a simple string in your Secrets.")
        st.stop()
    
    api_key = str(raw_key).strip() if raw_key else None
    
    if not api_key or api_key in ["None", "", "your_key_here"]:
        st.error("❌ Groq API Key is missing or invalid.")
        st.markdown("""
        **Please check your Secrets box for these common mistakes:**
        1. **Quotes**: Ensure it looks like `GROQ_API_KEY = "gsk_..."` (with quotes).
        2. **Typos**: Make sure there are no spaces in `GROQ_API_KEY`.
        3. **Section**: Don't put it in a `[section]` unless you know what you're doing.
        """)
        if st.button("I have updated my Secrets - Refresh App 🔄"):
            st.rerun()
        st.stop()
        
    try:
        client = Groq(api_key=api_key)
    except Exception as e:
        st.error(f"Failed to initialize Chatbot: {e}")
        st.stop()

    # Initialize chat history and selected model
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": "You are a helpful medical AI assistant named HealthScript Advisor. You answer medical queries politely. IMPORTANT: If the user types in Hindi, you MUST reply in Hindi. If the user types in English, reply in English."}]

    if "selected_model" not in st.session_state:
        st.session_state.selected_model = None

    # Define model details
    models = {
        "llama-3.3-70b-versatile": {"name": "LLaMA 3.3 (Newest & Smartest)", "tokens": 32768, "developer": "Meta"},
        "llama-3.1-8b-instant": {"name": "LLaMA 3.1 (Fast & Hindi Support)", "tokens": 8192, "developer": "Meta"}
    }
    
    col_1, col_2 = st.columns(2)
    with col_1:
        model_option = st.selectbox(
            "Choose a model:",
            options=list(models.keys()),
            format_func=lambda x: models[x]["name"],
            index=0
        )

    # Detect model change and clear chat history if model has changed
    if st.session_state.selected_model != model_option:
        st.session_state.messages = []
        st.session_state.selected_model = model_option
    max_tokens_range = models[model_option]["tokens"]

    with col_2:
        max_tokens = st.slider(
            "Max Tokens:",
            min_value=512,
            max_value=max_tokens_range,
            value=min(32768, max_tokens_range),
            step=512,
            help=f"Adjust the maximum number of tokens (words) for the model's response. Max for selected model: {max_tokens_range}"
        )

    # Display chat messages from history
    for message in st.session_state.messages:
        if message["role"] != "system": # Hide system prompt from UI
            if message["role"] == "user":
                # Render User Message as a right-aligned HTML block without breaking layout
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: flex-end; margin-bottom: 1.5rem;">
                        <div style="background-color: var(--secondary-background-color); color: var(--text-color); padding: 12px 18px; border-radius: 18px 18px 4px 18px; max-width: 80%; word-wrap: break-word; font-family: sans-serif; line-height: 1.5;">
                            {message['content']}
                        </div>
                        <div style="margin-left: 10px; font-size: 1.5rem; display: flex; align-items: flex-end;">👨‍💻</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(message["content"])

    def generate_chat_responses(chat_completion) -> Generator[str, None, None]:
        for chunk in chat_completion:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    if prompt := st.chat_input("Enter your texts here and chat..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Render active User Message
        st.markdown(
            f"""
            <div style="display: flex; justify-content: flex-end; margin-bottom: 1.5rem;">
                <div style="background-color: var(--secondary-background-color); color: var(--text-color); padding: 12px 18px; border-radius: 18px 18px 4px 18px; max-width: 80%; word-wrap: break-word; font-family: sans-serif; line-height: 1.5;">
                    {prompt}
                </div>
                <div style="margin-left: 10px; font-size: 1.5rem; display: flex; align-items: flex-end;">👨‍💻</div>
            </div>
            """, 
            unsafe_allow_html=True
        )

        full_response = ""
        try:
            chat_completion = client.chat.completions.create(
                model=model_option,
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                max_tokens=max_tokens,
                stream=True
            )

            with st.chat_message("assistant", avatar="🤖"):
                chat_responses_generator = generate_chat_responses(chat_completion)
                full_response = st.write_stream(chat_responses_generator)
        except Exception as e:
            st.error(e, icon="🚨")

        if isinstance(full_response, str):
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        else:
            combined_response = "\n".join(str(item) for item in full_response)
            st.session_state.messages.append({"role": "assistant", "content": combined_response})


def show_chatbot():
    if st.session_state.get("signedOut", False):
        st.markdown(f"#### Welcome, {st.session_state.user_name} 🎉")
        st.markdown("""
            # :rainbow[Chat With HealthScript Advisor 🗨️]
        """)
        st.subheader("Medical HealthCare ChatBot `Premium`", divider="rainbow", anchor=False)
        medical_chatbot()
    else:
        st.title("Please Login First ⚠️")
        st.subheader("Start Chatting with HealthScript Advisor 🗨️")
        st.markdown("* Please go back to the Account section.")
        st.markdown("* Then go to the Login Page and Login Yourself.")