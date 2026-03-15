import streamlit as st
import os

def get_secret(key, default=None):
    # 1. Try Streamlit Secrets (Cloud)
    try:
        # Check direct key
        if key in st.secrets:
            return st.secrets[key]
        # Check lowercase version (sometimes TOML makes keys lowercase)
        if key.lower() in st.secrets:
            return st.secrets[key.lower()]
    except:
        pass
        
    # 2. Try Environment Variables (Local)
    val = os.getenv(key)
    if not val:
        val = os.getenv(key.upper()) # Check uppercase as well
        
    return val if val else default
