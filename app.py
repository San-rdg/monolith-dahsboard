import pandas as pd
import streamlit as st
import numpy as np
import os
from datetime import datetime

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="MONOLITH | OS", page_icon="🏗️", layout="wide")

# --- 2. CINEMATIC PALANTIR CSS ---
st.markdown("""
    <style>
    .stApp { background: #05070a; color: #e6edf3; font-family: 'Inter', sans-serif; }
    
    /* Homepage Hero */
    .hero-container {
        text-align: center;
        padding-top: 15vh;
        background: radial-gradient(circle at center, #112244 0%, #05070a 85%);
        height: 100vh;
    }
    .hero-title {
        font-size: 80px; font-weight: 900; letter-spacing: -4px;
        background: linear-gradient(to bottom, #ffffff, #8899aa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .hero-subtitle { color: #58a6ff; font-size: 1.1rem; letter-spacing: 6px; text-transform: uppercase; margin-top: -10px; opacity: 0.8; }
    
    /* Feature Cards */
    .feature-card {
        background: rgba(10, 15, 25, 0.6); border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 30px; border-radius: 4px; transition: 0.4s;
    }
    .feature-card:hover { border-color: #58a6ff; background: rgba(88, 166, 255, 0.03); }
    
    /* Palantir Button */
    .stButton>button {
        background: transparent; color: white; border: 1px solid rgba(255,255,255,0.3);
        padding: 12px 60px; border-radius: 0px; letter-spacing: 4px; font-weight: 300; transition: 0.5s;
    }
    .stButton>button:hover { border-color: #58a6ff; color: #58a6ff; box-shadow: 0 0 30px rgba(88,166,255,0.2); }
    </style>
""", unsafe_allow_html=True)

# --- 3. THE DATA ENGINE (REPAIRING THE CRASH) ---
def fetch_system_data():
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, "price_history.csv")
    if not os.path.exists(file_path): return pd.DataFrame()
    
    try:
        df = pd.read_csv(file_path)
        df.columns = [c.strip().lower() for c in df.columns]
        
        # THE FIX: Handle the 'Tokyo Cement' error by coercing non-dates to NaT and dropping them
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', format='mixed')
        df = df.dropna(subset=['timestamp'])
        
        df['price'] = df['price'].apply(lambda x: float(str(x).replace(',', '').strip()) if pd.notnull(x) else np.nan)
        return df
    except Exception as e:
        return pd.DataFrame()

# --- 4. SESSION NAVIGATION ---
if 'system_init' not in st.session_state:
    st.session_state.system_init = False

# --- 5. PAGE 1: THE PALANTIR HOMEPAGE ---
if not st.session_state.system_init:
    st.markdown("""
        <div class="hero-container">
            <div class="hero-title">MONOLITH</div>
            <div class="hero-subtitle">Intelligence for the Modern Grid</div>
            <div style="margin-top: 50px;">
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1.5, 1, 1.5])
    with c2:
        if st.button("INITIALIZE"):
            st.session_state.system_init = True
            st.rerun()

    st.markdown("</div><div style='margin-top: 100px;'>", unsafe_allow_html=True)
    
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown('<div class="feature-card"><h4>01 / DATA INGESTION</h4><p style="color:#8b949e;">Automated neural engines monitoring 24/7 market fluctuations across national hubs.</p></div>', unsafe_allow_html=True)
    with f2:
        st.markdown('<div class="feature-card"><h4>02 / NEURAL FORECAST</h4><p style="color:#8b949e;">Polynomial trend analysis predicting material trajectories with historical accuracy.</p></div>', unsafe_allow_html=True)
    with f3:
        st.markdown('<div class="feature-card"><h4>03 / LOGISTICS OS</h4><p style="color:#8b949e;">Enterprise-grade geospatial routing for 10-Ton fleet optimization and recovery.</p></div>', unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

# --- 6. PAGE 2: THE INTELLIGENCE GRID ---
else:
    df_raw = fetch_system_data()
    # Insert your Grid UI code here (Metrics, Feed, Estimator, and Forecast)
    st.sidebar.markdown("### 🛰️ NODE: ACTIVE")
    if st.sidebar.button("TERMINATE SESSION"):
        st.session_state.system_init = False
        st.rerun()
    st.write("System online. Grid telemetry active.")




