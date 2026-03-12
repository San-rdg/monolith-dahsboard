import pandas as pd
import streamlit as st
import numpy as np
import os
import math
import hashlib
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="MONOLITH | OS", page_icon="🏗️", layout="wide")

# --- 2. SESSION STATE NAVIGATION ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# --- 3. PREMIUM CSS (INTEGRATED HOMEPAGE + COMMAND CENTER) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=IBM+Plex+Mono:wght@400;600&display=swap');

:root {
    --bg-primary: #05070a;
    --bg-secondary: #10161A;
    --accent-blue: #106BA3;
    --text-primary: #F5F8FA;
}

.stApp { background: var(--bg-primary); color: var(--text-primary); }

/* --- HOMEPAGE SPECIFIC --- */
.hero-wrapper {
    text-align: center;
    padding-top: 10vh;
    background: radial-gradient(circle at center, #112244 0%, #05070a 85%);
    height: 60vh;
}
.hero-logo {
    font-size: 90px; font-weight: 900; letter-spacing: -5px;
    background: linear-gradient(to bottom, #ffffff, #8899aa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0px;
}
.hero-tagline { 
    color: #58a6ff; font-size: 1rem; letter-spacing: 8px; 
    text-transform: uppercase; margin-bottom: 40px; opacity: 0.8;
}
.p-feature-card {
    background: rgba(16, 22, 26, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.05);
    padding: 25px; border-radius: 2px; height: 180px;
}

/* --- COMMAND CENTER CSS (Your Original Styles) --- */
.dashboard-card {
    background: #182026; border: 1px solid rgba(255, 255, 255, 0.15);
    padding: 12px; margin-bottom: 12px; border-radius: 2px;
}
.status-indicator { width: 6px; height: 6px; border-radius: 50%; background: #0F9960; display: inline-block; margin-right: 4px; }
.live-indicator { display: inline-block; width: 8px; height: 8px; background: #DB3737; border-radius: 50%; margin-right: 6px; animation: blink 1.5s infinite; }
@keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }

/* Re-styling Streamlit's default form for the Login */
[data-testid="stForm"] {
    background: rgba(24, 32, 38, 0.6) !important;
    border: 1px solid var(--accent-blue) !important;
    padding: 30px !important;
}
</style>
""", unsafe_allow_html=True)

# --- 4. DATA ENGINES (Your original functions) ---
def fetch_live_market_data():
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, "price_history.csv")
    if not os.path.exists(file_path): return pd.DataFrame()
    try:
        df = pd.read_csv(file_path)
        df.columns = [c.strip().lower() for c in df.columns]
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', format='mixed')
        df = df.dropna(subset=['timestamp'])
        df['price'] = df['price'].apply(lambda x: float(str(x).replace(',', '').strip()) if pd.notnull(x) else np.nan)
        return df.dropna(subset=['price'])
    except: return pd.DataFrame()

def process_latest_items(df):
    if df.empty: return []
    latest_items = []
    for item_name in df['item'].unique():
        item_history = df[df['item'] == item_name].sort_values('timestamp')
        current_price = item_history.iloc[-1]['price']
        change_pct = 0.0
        if len(item_history) > 1:
            prev_price = item_history.iloc[-2]['price']
            if prev_price != 0: change_pct = ((current_price - prev_price) / prev_price) * 100
        latest_items.append({"item": item_name, "price": current_price, "change": round(change_pct, 2), "source": item_history.iloc[-1].get('source', 'Market')})
    return latest_items

# --- 5. SYSTEM FLOW ---

# PAGE A: THE PALANTIR HOMEPAGE + LOGIN
if not st.session_state.authenticated:
    st.markdown("""
        <div class="hero-wrapper">
            <div class="hero-logo">MONOLITH</div>
            <div class="hero-tagline">Intelligence for the Modern Grid</div>
        </div>
    """, unsafe_allow_html=True)

    _, login_col, _ = st.columns([1.2, 1, 1.2])
    with login_col:
        with st.form("gatekeeper"):
            st.markdown("<p style='text-align:center; color:#8b949e; font-size:0.8rem; letter-spacing:2px;'>SECURE OPERATOR LOGIN</p>", unsafe_allow_html=True)
            u_name = st.text_input("Operator ID")
            u_pass = st.text_input("Access Key", type="password")
            if st.form_submit_button("INITIALIZE SYSTEM"):
                if u_name == "admin" and u_pass == "MONOLITH-2026": # Demo Creds
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("ACCESS DENIED")

    st.markdown("<br><br>", unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)
    with f1: st.markdown('<div class="p-feature-card"><h4>01 / INGESTION</h4><p style="color:#8b949e;">Automated neural engines monitoring 24/7 market fluctuations across national hubs.</p></div>', unsafe_allow_html=True)
    with f2: st.markdown('<div class="p-feature-card"><h4>02 / FORECAST</h4><p style="color:#8b949e;">Polynomial trend analysis predicting material trajectories with historical accuracy.</p></div>', unsafe_allow_html=True)
    with f3: st.markdown('<div class="p-feature-card"><h4>03 / LOGISTICS</h4><p style="color:#8b949e;">Enterprise-grade geospatial routing for 10-Ton fleet optimization and recovery.</p></div>', unsafe_allow_html=True)

# PAGE B: THE COMMAND CENTER (Logged In)
else:
    # Trigger refresh only when logged in
    st_autorefresh(interval=30000, key="datarefresh")
    
    # --- Sidebar ---
    with st.sidebar:
        st.markdown("### 🏢 PLATFORM")
        st.markdown("<div style='color:#106BA3; font-weight:bold;'>📊 COMMAND_CENTER</div>", unsafe_allow_html=True)
        user_tier = st.radio("Access Level:", ["Free Account", "Premium ($7k/mo)"])
        is_premium = (user_tier == "Premium ($7k/mo)")
        if st.button("TERMINATE SESSION"):
            st.session_state.authenticated = False
            st.rerun()

    # --- Header ---
    st.markdown("<h1 style='font-size:24px; font-weight:700;'>MONOLITH // COMMAND CENTER</h1>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-family:monospace; font-size:10px; color:#5C7080;'>STATUS: NOMINAL // OPERATOR: ADMIN // {datetime.now().strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)
    st.markdown("---")

    # --- Your Grid Logic ---
    df_raw = fetch_live_market_data()
    live_items = process_latest_items(df_raw)

    if not live_items:
        st.warning("Awaiting Data Sync...")
    else:
        # Metrics Row
        m1, m2, m3 = st.columns(3)
        m1.metric("Grid Coverage", f"{len(live_items)} Units", "Live")
        m2.metric("Engine Latency", "1.2ms", "-0.1ms")
        m3.metric("System Load", "NOMINAL")

        # Workspace (Feed + Logistics)
        col_feed, col_tools = st.columns([1, 1.5])
        
        with col_feed:
            st.markdown('<div class="dashboard-card" style="height:500px; overflow-y:auto;">', unsafe_allow_html=True)
            st.markdown("#### 📡 LIVE FEED")
            for item in live_items:
                color = "#0F9960" if item['change'] >= 0 else "#DB3737"
                st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #202B33;">
                        <span>{item['item']}</span>
                        <span style="color:{color}; font-family:monospace;">Rs.{item['price']:,.0f} ({item['change']:+.2f}%)</span>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_tools:
            st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
            t1, t2 = st.tabs(["🧮 Procurement", "📈 Neural Forecast"])
            
            with t1:
                sel = st.selectbox("Resource", [i['item'] for i in live_items])
                qty = st.number_input("Quantity", min_value=1, value=100)
                price = next(i['price'] for i in live_items if i['item'] == sel)
                
                if is_premium:
                    st.success("Premium Logistics Enabled")
                    loc = st.selectbox("Site", ["Colombo", "Kandy", "Galle", "Jaffna"])
                    # Logistics math here...
                else:
                    st.warning("Logistics Locked (Premium Only)")
                
                st.markdown(f"### Total: Rs. {price * qty:,.2f}")
            st.markdown('</div>', unsafe_allow_html=True)






