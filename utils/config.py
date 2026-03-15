import streamlit as st
import os

def get_secret(key, default=None):
    """
    Safely retrieves secrets from Streamlit Secrets (Cloud) 
    or Environment Variables (Local).
    """
    # 1. Try Streamlit Secrets
    try:
        if key in st.secrets:
            return st.secrets[key]
    except:
        pass
        
    # 2. Try Environment Variables (.env)
    return os.getenv(key, default)
