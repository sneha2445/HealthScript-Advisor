import streamlit as st
import os

def get_secret(key, default=None):
    """
    Safely retrieves secrets from Streamlit Secrets (Cloud) 
    or Environment Variables (Local).
    Now searches recursively in nested secrets.
    """
    # 1. Try Streamlit Secrets (Cloud)
    try:
        # Define a recursive searcher
        def find_in_dict(d, target_key):
            # Direct check
            if target_key in d:
                return d[target_key]
            # Lowercase check
            tk_low = target_key.lower()
            if tk_low in d:
                return d[tk_low]
            # Recursive check in nested dicts
            for k, v in d.items():
                if isinstance(v, (dict, st.runtime.secrets.AttrDict)):
                    res = find_in_dict(v, target_key)
                    if res is not None: return res
            return None

        val = find_in_dict(st.secrets, key)
        if val: return val
    except:
        pass
        
    # 2. Try Environment Variables (Local)
    val = os.getenv(key)
    if not val:
        val = os.getenv(key.upper()) # Check uppercase
    if not val:
        val = os.getenv(key.lower()) # Check lowercase
        
    return val if val else default
