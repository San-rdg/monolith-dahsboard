import pandas as pd
import streamlit as st
import numpy as np
import os
import math
from datetime import datetime

# --- 1. USER DATABASE (Demo Credentials) ---
USER_DB = {
    "admin": "MONOLITH-2026",
    "judge": "EXHIBIT-PRO"
}

# --- 2. SESSION STATE ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# --- 3. PAGE CONFIG & PALANTIR UI ---
st.set_page_config(page_title="MONOLITH | OS", page_icon="🏗️", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #05070a; color: #e6edf3; font-family: 'Inter', sans-serif; }
    
    /* Hero Landing Page */
    .hero-wrapper {
        text-align: center;
        padding-top: 10vh;
        background: radial-gradient(circle at center, #112244 0%, #05070a 85%);
    }
    .hero-logo {
        font-size: 85px; font-weight: 900; letter-spacing: -4px;
        background: linear-gradient(to bottom, #ffffff, #8899aa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .hero-tagline { 
        color: #58a6ff; font-size: 1.1rem; letter-spacing: 7px; 
        text-transform: uppercase; margin-bottom: 40px; opacity: 0.9;
    }

    /* Login Form Styling */
    .stForm {
        background: rgba(13, 17, 23, 0.4) !important;
        border: 1px solid rgba(88, 166, 255, 0.2) !important;
        border-radius: 4px !important;
        padding: 30px !important;
    }
    
    /* Feature Cards */
    .p-feature-card {
        background: rgba(10, 15, 25, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 25px; border-radius: 2px; height: 180px;
        transition: 0.3s; margin-top: 50px;
    }
    
    /* Buttons */
    .stButton>button {
        background: #58a6ff; color: #05070a; border: none;
        width: 100%; border-radius: 2px; letter-spacing: 2px; font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. DATA LOADER (With Bug Fix) ---
def fetch_system_data():
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, "price_history.csv")
    if not os.path.exists(file_path): return pd.DataFrame()
    try:
        df = pd.read_csv(file_path)
        df.columns = [c.strip().lower() for c in df.columns]
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', format='mixed')
        df = df.dropna(subset=['timestamp']) 
        df['price'] = df['price'].apply(lambda x: float(str(x).replace(',', '').strip()) if pd.notnull(x) else 0.0)
        return df
    except: return pd.DataFrame()

# --- 5. LOGIC FLOW ---

if not st.session_state.authenticated:
    # --- HOMEPAGE WITH INTEGRATED LOGIN ---
    st.markdown("""
        <div class="hero-wrapper">
            <div class="hero-logo">MONOLITH</div>
            <div class="hero-tagline">Intelligence for the Modern Grid</div>
        </div>
    """, unsafe_allow_html=True)

    # Login Form in the center
    _, col, _ = st.columns([1.2, 1, 1.2])
    with col:
        with st.form("gatekeeper_login"):
            st.markdown("<p style='text-align:center; color:#8b949e; font-size:0.8rem;'>AUTHORIZATION REQUIRED</p>", unsafe_allow_html=True)
            u_id = st.text_input("Operator ID", placeholder="e.g. admin")
            a_key = st.text_input("Access Key", type="password")
            if st.form_submit_button("INITIALIZE SYSTEM"):
                if u_id in USER_DB and USER_DB[u_id] == a_key:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid Credentials")

    # Features below login
    f1, f2, f3 = st.columns(3)
    with f1: st.markdown('<div class="p-feature-card"><h4>01 / INGESTION</h4><p style="color:#8b949e;">Scraping engines monitoring 24/7 market fluctuations.</p></div>', unsafe_allow_html=True)
    with f2: st.markdown('<div class="p-feature-card"><h4>02 / FORECAST</h4><p style="color:#8b949e;">Polynomial trend analysis for predictive trajectory.</p></div>', unsafe_allow_html=True)
    with f3: st.markdown('<div class="p-feature-card"><h4>03 / LOGISTICS</h4><p style="color:#8b949e;">Geospatial routing for fleet optimization.</p></div>', unsafe_allow_html=True)

else:
    # --- THE INTELLIGENCE GRID (DASHBOARD) ---
    df_raw = fetch_system_data()
    
    with st.sidebar:
        st.markdown(f"### 🛰️ NODE: ACTIVE")
        st.write(f"Operator: `{datetime.now().strftime('%H:%M')}`")
        tier = st.radio("Clearance", ["Standard", "L7 Enterprise"])
        if st.button("TERMINATE SESSION"):
            st.session_state.authenticated = False
            st.rerun()

    st.markdown("<h3><span style='color:#ff7b72;'>●</span> GRID TELEMETRY ACTIVE</h3>", unsafe_allow_html=True)
    
    # Place your Grid/Dashboard code here (Tabs, Metrics, etc.)
    st.info("Verified Access. System operational.")
    if not df_raw.empty:
        st.dataframe(df_raw.tail(10), use_container_width=True)





