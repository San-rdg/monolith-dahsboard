import pandas as pd
import streamlit as st
import numpy as np
import os
import math
from datetime import datetime

# --- 1. USER DATABASE (Demo Credentials) ---
# In a real app, these would be encrypted in a database
USER_DB = {
    "admin": "MONOLITH-2026",
    "judge": "EXHIBIT-PRO",
    "guest": "1234"
}

# --- 2. SESSION STATE INITIALIZATION ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'system_initialized' not in st.session_state:
    st.session_state.system_initialized = False

# --- 3. PAGE STYLING ---
st.markdown("""
    <style>
    .stApp { background: #05070a; color: #e6edf3; }
    
    /* Login Box Styling */
    .login-card {
        background: rgba(13, 17, 23, 0.9);
        border: 1px solid #30363d;
        padding: 40px;
        border-radius: 8px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        margin-top: 10vh;
    }
    .stTextInput>div>div>input {
        background-color: #0d1117 !important;
        color: white !important;
        border: 1px solid #30363d !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. LOGIN LOGIC ---
def login_page():
    st.markdown("<div class='hero-wrapper' style='text-align:center; padding-top:5vh;'><h1 style='font-size:50px; letter-spacing:-2px;'>MONOLITH <span style='color:#58a6ff; font-weight:300;'>OS</span></h1><p style='color:#8b949e; letter-spacing:2px;'>SECURE GATEWAY v4.0.2</p></div>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 1, 1])
    with col:
        with st.form("login_form"):
            st.markdown("### 🔐 Authentication Required")
            user = st.text_input("Operator ID")
            pw = st.text_input("Access Key", type="password")
            submit = st.form_submit_button("VERIFY IDENTITY")
            
            if submit:
                if user in USER_DB and USER_DB[user] == pw:
                    st.session_state.authenticated = True
                    st.success("Identity Verified. Bypassing Firewalls...")
                    st.rerun()
                else:
                    st.error("Access Denied: Invalid Credentials")

# --- 5. THE SYSTEM FLOW ---

# STEP 1: If not logged in, show login
if not st.session_state.authenticated:
    login_page()

# STEP 2: If logged in, but not initialized, show Palantir Homepage
elif st.session_state.authenticated and not st.session_state.system_initialized:
    st.markdown("""
        <div style="text-align:center; padding-top:15vh;">
            <h1 style="font-size:80px; font-weight:900; letter-spacing:-4px; color:white;">MONOLITH</h1>
            <p style="color:#58a6ff; letter-spacing:8px; text-transform:uppercase;">Initialization Ready</p>
        </div>
    """, unsafe_allow_html=True)
    
    _, btn_col, _ = st.columns([1.5, 1, 1.5])
    with btn_col:
        if st.button("START SESSION"):
            st.session_state.system_initialized = True
            st.rerun()
            
    # Logout option
    if st.button("Exit System"):
        st.session_state.authenticated = False
        st.rerun()

# STEP 3: The Intelligence Grid (Dashboard)
else:
    # --- Put your previous Dashboard/Grid code here ---
    st.sidebar.success(f"Verified Operator: {datetime.now().strftime('%H:%M:%S')}")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.system_initialized = False
        st.rerun()
    
    st.title("📡 Intelligence Grid Active")
    st.write("Welcome back, Commander.")
    # (Rest of your market data code goes here)




