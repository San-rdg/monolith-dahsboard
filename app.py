import pandas as pd
import streamlit as st
import numpy as np
import os
import math
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG & THEME ---
st.set_page_config(page_title="MONOLITH | OS", page_icon="🏗️", layout="wide")

# --- 2. PALANTIR CINEMATIC CSS ---
st.markdown("""
    <style>
    .stApp { background: #05070a; color: #e6edf3; font-family: 'Inter', sans-serif; }
    
    /* Hero Landing Page */
    .hero-wrapper {
        text-align: center;
        padding-top: 12vh;
        background: radial-gradient(circle at center, #112244 0%, #05070a 80%);
        height: 60vh;
    }
    .hero-logo {
        font-size: 80px; font-weight: 900; letter-spacing: -4px;
        background: linear-gradient(to bottom, #ffffff, #8899aa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .hero-tagline { 
        color: #58a6ff; font-size: 1.2rem; letter-spacing: 6px; 
        text-transform: uppercase; margin-bottom: 60px; opacity: 0.9;
    }

    /* Grid Feature Cards */
    .p-feature-card {
        background: rgba(10, 15, 25, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 30px; border-radius: 2px; height: 220px;
        transition: 0.3s;
    }
    .p-feature-card:hover { border-color: #58a6ff; background: rgba(88, 166, 255, 0.05); }

    /* Buttons */
    .stButton>button {
        background: transparent; color: white; border: 1px solid rgba(255,255,255,0.3);
        padding: 15px 50px; border-radius: 0px; letter-spacing: 4px; font-weight: 300;
        transition: 0.4s;
    }
    .stButton>button:hover { border-color: #58a6ff; color: #58a6ff; box-shadow: 0 0 20px rgba(88,11,255,0.2); }
    
    /* Dashboard specific */
    .status-dot { color: #ff7b72; animation: blinker 2s linear infinite; font-size: 14px; }
    @keyframes blinker { 50% { opacity: 0; } }
    .dashboard-card {
        background: rgba(22, 27, 34, 0.7); backdrop-filter: blur(10px);
        border: 1px solid rgba(88, 166, 255, 0.2); border-radius: 4px;
        padding: 20px; margin-bottom: 20px;
    }
    .total-display {
        background: rgba(0, 0, 0, 0.4); border-radius: 4px; padding: 20px;
        border-left: 5px solid #3fb950; margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA UTILITIES ---
def fetch_system_data():
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, "price_history.csv")
    if not os.path.exists(file_path): return pd.DataFrame()
    try:
        df = pd.read_csv(file_path)
        df.columns = [c.strip().lower() for c in df.columns]
        # FIX FOR DATA READ ERROR: Coerce errors to ignore strings like "Tokyo Cement"
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', format='mixed')
        df = df.dropna(subset=['timestamp']) 
        df['price'] = df['price'].apply(lambda x: float(str(x).replace(',', '').strip()) if pd.notnull(x) else 0.0)
        return df
    except: return pd.DataFrame()

def process_latest(df):
    items = []
    for name in df['item'].unique():
        subset = df[df['item'] == name].sort_values('timestamp')
        curr = subset.iloc[-1]['price']
        change = 0.0
        if len(subset) > 1:
            prev = subset.iloc[-2]['price']
            if prev != 0: change = ((curr - prev) / prev) * 100
        items.append({"item": name, "price": curr, "change": round(change, 2)})
    return items

# --- 4. NAVIGATION STATE ---
if 'init' not in st.session_state:
    st.session_state.init = False

# --- 5. PAGE 1: PALANTIR HOMEPAGE ---
if not st.session_state.init:
    st.markdown("""
        <div class="hero-wrapper">
            <div class="hero-logo">MONOLITH</div>
            <div class="hero-tagline">Intelligence for the Modern Grid</div>
        </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1.6, 1, 1.6])
    with c2:
        if st.button("INITIALIZE SYSTEMS"):
            st.session_state.init = True
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown('<div class="p-feature-card"><h4>01 / INGESTION</h4><p style="color:#8b949e;">Neural engines monitoring 24/7 market fluctuations across national construction hubs.</p></div>', unsafe_allow_html=True)
    with f2:
        st.markdown('<div class="p-feature-card"><h4>02 / FORECAST</h4><p style="color:#8b949e;">Polynomial trend analysis predicting material trajectories with historical accuracy.</p></div>', unsafe_allow_html=True)
    with f3:
        st.markdown('<div class="p-feature-card"><h4>03 / LOGISTICS</h4><p style="color:#8b949e;">Enterprise-grade geospatial routing for 10-Ton fleet optimization and recovery.</p></div>', unsafe_allow_html=True)

# --- 6. PAGE 2: THE INTELLIGENCE GRID (DASHBOARD) ---
else:
    df_raw = fetch_system_data()
    live_items = process_latest(df_raw)

    with st.sidebar:
        st.markdown("### 🛰️ NODE: ACTIVE")
        tier = st.radio("Clearance", ["Standard", "L7 Enterprise (Rs. 7000)"])
        if st.button("TERMINATE SESSION"):
            st.session_state.init = False
            st.rerun()

    st.markdown("<h3><span class='status-dot'>●</span> GRID TELEMETRY ACTIVE</h3>", unsafe_allow_html=True)

    if not live_items:
        st.error("Waiting for price_history.csv sync...")
    else:
        # TOP METRICS
        m1, m2, m3 = st.columns(3)
        m1.metric("Coverage", f"{len(live_items)} Units", "Live")
        m2.metric("Market Flux", f"{sum(i['change'] for i in live_items)/len(live_items):.2f}%")
        m3.metric("System Load", "1.2ms", "-0.1ms")

        col_left, col_right = st.columns([1, 1.2])

        with col_left:
            st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
            st.markdown("#### 📡 LIVE FEED")
            for item in live_items:
                color = "#3fb950" if item['change'] >= 0 else "#f85149"
                st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid #30363d;">
                        <span>{item['item']}</span>
                        <span style="color:{color}; font-family:monospace;">Rs.{item['price']:,.0f} ({item['change']:+.2f}%)</span>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_right:
            st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
            st.markdown("#### 🚚 LOGISTICS & ESTIMATION")
            selected = st.selectbox("Resource", [i['item'] for i in live_items])
            qty = st.number_input("Quantity", min_value=1, value=100)
            
            # Simple Math
            price = next(i['price'] for i in live_items if i['item'] == selected)
            mat_cost = price * qty
            
            # Tier Check
            if tier == "L7 Enterprise (Rs. 7000)":
                dist = st.select_slider("Distance (km)", options=[25, 50, 100, 200])
                trans_cost = (dist * 150) * math.ceil((qty * 50)/10000) # Assume 50kg/unit
                st.success(f"Logistics Unlocked: Rs. {trans_cost:,.2f}")
            else:
                trans_cost = 0
                st.warning("🔒 Upgrade to L7 for Transport Analysis")
            
            st.markdown(f"""
                <div class="total-display">
                    <small style="color:#8b949e;">GRAND TOTAL ESTIMATE</small>
                    <h2 style="color:#3fb950; margin:0;">Rs. {mat_cost + trans_cost:,.2f}</h2>
                </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)




