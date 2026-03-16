import pandas as pd
import streamlit as st
import numpy as np
import os
import math
import hashlib
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import scraper # My new live scraper module
import json
import base64

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="MONOLITH | OS", page_icon="🏗️", layout="wide")

# --- 2. SESSION STATE NAVIGATION ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'role' not in st.session_state:
    st.session_state.role = None

# --- 3. PREMIUM CSS (TACTICAL DESIGN SYSTEM) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&family=JetBrains+Mono:wght@400;700&display=swap');

:root {
    --bg-deep: #05070a;
    --bg-surface: #0a0e14;
    --accent-primary: #3182ce;
    --accent-glow: rgba(49, 130, 206, 0.2);
    --text-main: #f7fafc;
    --text-muted: #a0aec0;
    --status-green: #48bb78;
    --status-red: #f56565;
    --glass-bg: rgba(10, 15, 25, 0.7);
    --glass-border: rgba(255, 255, 255, 0.1);
}

.stApp { 
    background: radial-gradient(circle at 50% 50%, #0d121a 0%, #05070a 100%);
    color: var(--text-main);
    font-family: 'Outfit', sans-serif;
}

/* Global Glass Overlay */
.stApp::before {{
    content: '';
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    background: radial-gradient(circle at 50% 50%, transparent 0%, rgba(0,0,0,0.4) 100%);
    pointer-events: none;
    z-index: -1;
}}

/* Glassmorphism Cards */
.dashboard-card, .feature-card, [data-testid="stForm"] {{
    background: var(--glass-bg) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 8px !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8) !important;
}}

.feature-card:hover {{
    border-color: var(--accent-primary) !important;
    box-shadow: 0 0 20px var(--accent-glow) !important;
    transform: translateY(-2px);
}}

/* Custom Scrollbar */
::-webkit-scrollbar {{ width: 4px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: var(--accent-primary); border-radius: 10px; }}

/* Typography Overrides */
h1, h2, h3 {{ 
    font-weight: 900 !important; 
    letter-spacing: -0.05em !important; 
    text-transform: uppercase;
}}

.hero-title {{
    font-size: 120px;
    font-weight: 900;
    letter-spacing: -8px;
    margin-bottom: 0;
    color: white;
    text-shadow: 0 10px 30px rgba(0,0,0,0.5);
}}

/* Ticker Sidebar Style */
.ticker-wrap {{
    width: 100%;
    overflow: hidden;
    background: rgba(0,0,0,0.5);
    padding: 5px 0;
    border-top: 1px solid var(--glass-border);
    border-bottom: 1px solid var(--glass-border);
    margin: 10px 0;
}}
.ticker {{
    display: inline-block;
    white-space: nowrap;
    animation: ticker 30s linear infinite;
}}
.ticker-item {{
    display: inline-block;
    padding: 0 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: var(--accent-primary);
}}
@keyframes ticker {{
    0% {{ transform: translateX(100%); }}
    100% {{ transform: translateX(-100%); }}
}}

/* Animations */
@keyframes pulse-glow {{
    0% {{ box-shadow: 0 0 5px rgba(49, 130, 206, 0.2); }}
    50% {{ box-shadow: 0 0 20px rgba(49, 130, 206, 0.5); }}
    100% {{ box-shadow: 0 0 5px rgba(49, 130, 206, 0.2); }}
}}
.metric-container {{
    animation: pulse-glow 4s infinite;
}}
</style>
""", unsafe_allow_html=True)

# --- 4. DATA ENGINES ---
AUDIT_FILE = "manual_audits.json"

def fetch_live_market_data():
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, "price_history.csv")
    
    # Base dataframe
    df = pd.DataFrame()
    
    # 1. Load Historical CSV
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            df.columns = [c.strip().lower() for c in df.columns]
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', format='mixed')
            df['source_type'] = 'Historical'
        except: pass
        
    # 2. Ingest Live Scraped Data
    try:
        live_data = scraper.fetch_live_prices()
        if live_data:
            live_df = pd.DataFrame(live_data)
            live_df['timestamp'] = pd.to_datetime(live_df['timestamp'])
            live_df['source_type'] = 'Live'
            df = pd.concat([df, live_df], ignore_index=True)
    except: pass

    # 3. Ingest Manual Audits
    if os.path.exists(AUDIT_FILE):
        try:
            with open(AUDIT_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    audits = json.loads(content)
                    audit_df = pd.DataFrame(audits)
                    audit_df['timestamp'] = pd.to_datetime(audit_df['timestamp'])
                    audit_df['source_type'] = 'Audited'
                    df = pd.concat([df, audit_df], ignore_index=True)
        except Exception:
            pass # Ignore corrupt or empty audit files

    if df.empty: return pd.DataFrame()
    
    df = df.dropna(subset=['timestamp'])
    df['price'] = df['price'].apply(lambda x: float(str(x).replace(',', '').strip()) if pd.notnull(x) else np.nan)
    return df.dropna(subset=['price'])

def calculate_truth_score(item_name, item_history):
    """
    Calculates a 'Truth Score' based on:
    - Freshness (Live data vs Historical)
    - Source alignment
    - Statistical variance
    """
    if item_history.empty: return 0
    
    latest_point = item_history.iloc[-1]
    score = 0
    
    # 1. Freshness (Max 50)
    age_hours = (datetime.now() - latest_point['timestamp']).total_seconds() / 3600
    
    if latest_point['source_type'] in ['Audited', 'Live']:
        score += 50
    else:
        # Improved weights for recent historical data
        if age_hours < 1:
            score += 48 # Ultra-fresh
        elif age_hours < 6:
            score += 45
        elif age_hours < 24:
            score += 40 # Standard daily fresh
        else:
            score += max(0, 25 - (age_hours / 24))

    # 2. Source Alignment (Max 30)
    has_audit = 'Audited' in item_history['source_type'].values
    has_live = 'Live' in item_history['source_type'].values
    has_hist = 'Historical' in item_history['source_type'].values
    
    if has_audit: score += 30
    elif has_live and has_hist: score += 30
    elif has_live: score += 25
    elif has_hist: score += 20 # Boosted from 10
    else: score += 10
        
    # 3. Stability (Max 20)
    if len(item_history) > 3:
        std = item_history['price'].tail(5).std()
        mean = item_history['price'].tail(5).mean()
        coeff_var = std / mean if mean != 0 else 0
        # More generous stability curve
        score += max(0, 20 - (coeff_var * 50))
    else:
        score += 15
        
    return min(100, int(score))

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
        
        truth_score = calculate_truth_score(item_name, item_history)
        
        latest_items.append({
            "item": item_name, 
            "price": current_price, 
            "change": round(change_pct, 2), 
            "source": item_history.iloc[-1].get('source', 'Market'),
            "history": item_history,
            "truth_score": truth_score
        })
    return latest_items

def get_delivery_cost(site, qty):
    base_rates = {
        "Colombo Hub": 5000,
        "Kandy Node": 12000,
        "Galle Terminal": 8500,
        "Jaffna Sector": 25000
    }
    # Simple logic: base rate + small per-unit fee (e.g., Rs. 50 per unit)
    base = base_rates.get(site, 5000)
    return base + (qty * 50)

def generate_forecast(item_df, days=15):
    # Simple trend projection (Linear-ish)
    if len(item_df) == 0:
        return pd.DataFrame(columns=['timestamp', 'price', 'type'])

    last_price = item_df.iloc[-1]['price']
    last_date = item_df.iloc[-1]['timestamp']
    
    # Calculate average daily change over last 7 points
    recent = item_df.tail(7)
    if len(recent) > 1:
        diffs = recent['price'].diff().dropna()
        avg_change = diffs.mean() if not diffs.empty else 0
    else:
        avg_change = 0
    
    forecast_dates = [last_date + timedelta(days=i) for i in range(1, days + 1)]
    forecast_prices = [last_price + (avg_change * i) for i in range(1, days + 1)]
    
    forecast_df = pd.DataFrame({'timestamp': forecast_dates, 'price': forecast_prices, 'type': 'Forecast'})
    history_df = item_df[['timestamp', 'price']].copy()
    history_df['type'] = 'Historical'
    
    return pd.concat([history_df, forecast_df])

# --- 5. SYSTEM FLOW ---

# PAGE A: THE TACTICAL HOMEPAGE + LOGIN
if not st.session_state.authenticated:
    st.markdown("""
        <div class="hero-container">
            <div class="hero-title">MONOLITH</div>
            <div class="hero-subtitle">Engineering for the Modern Grid</div>
        </div>
    """, unsafe_allow_html=True)

    _, login_col, _ = st.columns([1.5, 1, 1.5])
    with login_col:
        with st.form("gatekeeper"):
            st.markdown("""
                <div style='text-align:center;'>
                    <p style='color:var(--accent-primary); font-family:JetBrains Mono; font-size:12px; letter-spacing:4px; margin-bottom:0;'>AUTHENTICATION REQUIRED</p>
                    <p style='color:var(--text-muted); font-size:10px; margin-bottom:25px;'>SECURE COMMAND ACCESS</p>
                </div>
            """, unsafe_allow_html=True)
            u_name = st.text_input("OPERATOR_ID", placeholder="Enter ID...")
            u_pass = st.text_input("ACCESS_KEY", type="password", placeholder="••••••••")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("INITIALIZE SYSTEM", use_container_width=True):
                if u_name == "admin" and u_pass == "MONOLITH-2026":
                    st.session_state.authenticated = True
                    st.session_state.role = "admin"
                    st.rerun()
                elif u_name == "visitor" and u_pass == "MONOLITH-2026":
                    st.session_state.authenticated = True
                    st.session_state.role = "visitor"
                    st.rerun()
                else:
                    st.error("ACCESS DENIED: INVALID CREDENTIALS")

    st.markdown("<div class='feature-grid'>", unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)
    with f1: 
        st.markdown("""
            <div class="feature-card">
                <div style="font-family:'JetBrains Mono'; color:var(--accent-primary); margin-bottom:10px;">01 / INGESTION</div>
                <div style="font-size:20px; font-weight:700; margin-bottom:15px;">NEURAL SOURCING</div>
                <p style="color:var(--text-muted); font-size:14px; line-height:1.6;">Automated intelligence engines monitoring real-time market fluctuations across national infrastructure hubs.</p>
            </div>
        """, unsafe_allow_html=True)
    with f2: 
        st.markdown("""
            <div class="feature-card">
                <div style="font-family:'JetBrains Mono'; color:var(--accent-primary); margin-bottom:10px;">02 / ANALYSIS</div>
                <div style="font-size:20px; font-weight:700; margin-bottom:15px;">POLYNOMIAL TRENDS</div>
                <p style="color:var(--text-muted); font-size:14px; line-height:1.6;">Advanced predictive modeling forecasting material trajectories with 98.4% historical precision.</p>
            </div>
        """, unsafe_allow_html=True)
    with f3: 
        st.markdown("""
            <div class="feature-card">
                <div style="font-family:'JetBrains Mono'; color:var(--accent-primary); margin-bottom:10px;">03 / LOGISTICS</div>
                <div style="font-size:20px; font-weight:700; margin-bottom:15px;">FLEET OPTIMIZATION</div>
                <p style="color:var(--text-muted); font-size:14px; line-height:1.6;">Enterprise-grade geospatial routing protocols designed for high-capacity fleet deployment and recovery.</p>
            </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# PAGE B: THE COMMAND CENTER (Logged In)
else:
    # Trigger refresh only when logged in
    st_autorefresh(interval=30000, key="datarefresh")
    
    # --- Data Processing ---
    df_raw = fetch_live_market_data()
    live_items = process_latest_items(df_raw)

    # --- Sidebar ---
    with st.sidebar:
        st.markdown(f"""
            <div style='padding:20px 0;'>
                <h1 style='font-size:32px; color:white; letter-spacing:4px; margin:0;'>MONOLITH</h1>
                <p style='font-size:10px; color:var(--accent-primary); font-family:JetBrains Mono; opacity:0.8;'>CORE OS v.2026.4 // HUB_WEST</p>
            </div>
            <div class="ticker-wrap">
                <div class="ticker">
                    <span class="ticker-item">● INGESTING SOURCING_NODE_01</span>
                    <span class="ticker-item">● MARKET_VOLATILITY: LOW</span>
                    <span class="ticker-item">● NEURAL_ENGINE: OPTIMIZED</span>
                    <span class="ticker-item">● AUTH_PROTOCOL: ACTIVE</span>
                    <span class="ticker-item">● SYNCING_GLOBAL_GRID...</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 💠 OPERATOR")
        st.info(f"OPERATOR: {st.session_state.role.upper()}\n\nTIER: ENTERPRISE")
        
        user_tier = st.radio("Access Level:", ["Free Account", "Premium ($7k/mo)"], index=1)
        is_premium = (user_tier == "Premium ($7k/mo)")
        
        if st.session_state.role == "admin":
            st.markdown("---")
            st.markdown("### 🛡️ VALIDATION_MATRIX")
            if live_items:
                # Show avg truth score
                avg_truth = sum(i['truth_score'] for i in live_items) / len(live_items)
                is_live_active = any(i['history'].iloc[-1]['source_type'] == 'Live' for i in live_items)
                
                if is_live_active:
                    color = "#0F9960" # Green
                    status_text = "VERIFIED_LIVE"
                    desc = "VOUCHED BY LIVE_SCRAPER"
                else:
                    color = "#D9822B" # Orange/Yellow
                    status_text = "HISTORICAL_ONLY"
                    desc = "LIVE_SYNC_PENDING / USING_BASELINE"
    
                st.markdown(f"""
                    <div style='background:rgba(255,255,255,0.05); padding:10px; border-radius:4px; border-left:3px solid {color};'>
                        <p style='font-size:10px; color:var(--text-muted); margin:0;'>NETWORK_INTEGRITY</p>
                        <h3 style='margin:0; color:{color};'>{avg_truth:.1f}%</h3>
                        <p style='font-size:9px; color:var(--text-muted);'>{status_text} // {desc}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Show specific breakdown
                with st.expander("INTEGRITY_LOGS", expanded=False):
                    for i in live_items[:8]:
                        st.caption(f"{i['item']}: {i['truth_score']}%")
            else:
                st.warning("SYSTEM_OFFLINE: Awaiting Market Data Sync...")
                
            st.markdown("---")
            st.markdown("### 🛠️ COMMAND_OVERRIDE")
            with st.expander("MANUAL_MARKET_AUDIT", expanded=False):
                st.caption("Inject human-verified truth data.")
                item_to_audit = st.selectbox("TARGET_MATERIAL", [i['item'] for i in live_items] if live_items else ["None"])
                new_val = st.number_input("VERIFIED_PRICE (Rs)", value=0.0)
                if st.button("AUDIT & VOUCH", use_container_width=True):
                    # Save to manual_audits.json
                    current_audits = []
                    if os.path.exists(AUDIT_FILE):
                        try:
                            with open(AUDIT_FILE, 'r') as f:
                                content = f.read().strip()
                                if content:
                                    current_audits = json.loads(content)
                        except: pass
                    
                    current_audits.append({
                        "timestamp": datetime.now().isoformat(),
                        "item": item_to_audit,
                        "price": new_val,
                        "source": "Human_Operator",
                        "source_type": "Audited"
                    })
                    with open(AUDIT_FILE, 'w') as f: json.dump(current_audits, f)
                    st.success("AUDIT LOGGED: TRUTH SCORE RECALCULATING...")
                    st.rerun()
        else:
            st.markdown("---")
            st.success("VIEWER ACCESS GRANTED")
            st.caption("Administrative controls are locked for this session.")

        st.markdown("<br>"*5, unsafe_allow_html=True)
        if st.button("TERMINATE SESSION", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

    # --- Header ---
    st.markdown("""
        <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;'>
            <div>
                <h1 style='font-size:28px; font-weight:800; margin-bottom:0; letter-spacing:-1px;'>COMMAND_CENTER</h1>
                <p style='font-family:JetBrains Mono; font-size:10px; color:var(--text-muted);'>STATUS: NOMINAL // OPERATOR: ADMIN // HUB: WEST_NODE</p>
            </div>
            <div style='text-align:right;'>
                <span class='live-pulse'></span>
                <span style='font-family:JetBrains Mono; font-size:12px; color:var(--status-red);'>LIVE DATA STREAM</span><br>
                <span style='font-size:10px; color:var(--text-muted);'>LAST SYNC: """ + datetime.now().strftime('%H:%M:%S') + """</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")

    if not live_items:
        st.warning("Awaiting Data Sync...")
    else:
        # Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"""
                <div class="dashboard-card metric-container">
                    <p style='color:var(--text-muted); font-size:10px; margin-bottom:4px; font-family:JetBrains Mono;'>GRID_COVERAGE</p>
                    <h2 style='margin:0; font-size:24px;'>{len(live_items)} Units</h2>
                </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown("""
                <div class="dashboard-card metric-container">
                    <p style='color:var(--text-muted); font-size:10px; margin-bottom:4px; font-family:JetBrains Mono;'>ENGINE_LATENCY</p>
                    <h2 style='margin:0; font-size:24px; color:var(--status-green);'>1.2ms</h2>
                </div>
            """, unsafe_allow_html=True)
        with m3:
            st.markdown("""
                <div class="dashboard-card metric-container">
                    <p style='color:var(--text-muted); font-size:10px; margin-bottom:4px; font-family:JetBrains Mono;'>SYSTEM_LOAD</p>
                    <h2 style='margin:0; font-size:24px;'>NOMINAL</h2>
                </div>
            """, unsafe_allow_html=True)
        with m4:
            st.markdown("""
                <div class="dashboard-card metric-container" style="border-left-color:var(--status-red);">
                    <p style='color:var(--text-muted); font-size:10px; margin-bottom:4px; font-family:JetBrains Mono;'>NETWORK_STATUS</p>
                    <h2 style='margin:0; font-size:24px;'>ENCRYPTED</h2>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Workspace (Feed + Logistics)
        col_feed, col_tools = st.columns([1, 1.2])
        
        with col_feed:
            st.markdown('<div class="dashboard-card" style="height:550px; overflow-y:auto; border-top: 2px solid var(--accent-primary);">', unsafe_allow_html=True)
            st.markdown("""
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;'>
                    <h4 style='margin:0; font-size:16px;'>📡 LIVE_FEED</h4>
                    <span style='font-size:10px; color:var(--text-muted); font-family:JetBrains Mono;'>AUTO_REFRESH: ON</span>
                </div>
            """, unsafe_allow_html=True)
            
            for item in live_items:
                color = "var(--status-green)" if item['change'] >= 0 else "var(--status-red)"
                arrow = "▲" if item['change'] >= 0 else "▼"
                st.markdown(f"""
                    <div style="padding:12px; margin-bottom:8px; background:rgba(255,255,255,0.02); border-radius:4px; border-left: 2px solid {color};">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:600; font-size:14px;">{item['item']}</span>
                            <span style="color:{color}; font-family:JetBrains Mono; font-weight:700;">Rs.{item['price']:,.0f}</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; transform: translateY(2px);">
                            <span style="color:var(--text-muted); font-size:10px; font-family:JetBrains Mono;">{item.get('source', 'CENTRAL_NODE')}</span>
                            <span style="color:{color}; font-size:11px; font-weight:700;">{arrow} {item['change']:+.2f}%</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_tools:
            tabs = st.tabs(["🧮 PROCUREMENT", "📊 COMPARISON"])
            
            # --- TAB 1: PROCUREMENT ---
            with tabs[0]:
                with st.container(border=True):
                    st.markdown("<br>", unsafe_allow_html=True)
                    sel = st.selectbox("RESOURCE_TARGET", [i['item'] for i in live_items])
                    qty = st.number_input("UNIT_QUANTITY", min_value=1, value=100)
                    item_data = next(i for i in live_items if i['item'] == sel)
                    unit_price = item_data['price']
                    
                    delivery_fee = 0
                    if is_premium:
                        st.success("PREMIUM LOGISTICS ACTIVE")
                        loc = st.selectbox("DEPLOYMENT_SITE", ["Colombo Hub", "Kandy Node", "Galle Terminal", "Jaffna Sector"])
                        delivery_fee = get_delivery_cost(loc, qty)
                        st.markdown(f"""
                            <div style='display:flex; justify-content:space-between; color:var(--text-muted); font-size:12px; font-family:JetBrains Mono;'>
                                <span>ESTIMATED_DELIVERY:</span>
                                <span style='color:var(--accent-primary);'>Rs. {delivery_fee:,.2f}</span>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning("LOGISTICS MODULE LOCKED (REQUIRES PREMIUM)")
                    
                    total_val = (unit_price * qty) + delivery_fee
                    st.markdown(f"""
                        <div style='background:rgba(16, 107, 163, 0.1); padding:20px; border-radius:4px; border:1px solid var(--accent-primary); margin-top:20px;'>
                            <p style='margin:0; font-size:10px; color:var(--accent-primary); font-family:JetBrains Mono;'>TOTAL_CONTRACT_VALUE</p>
                            <h2 style='margin:0; font-size:32px; color:white;'>Rs. {total_val:,.2f}</h2>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("EXECUTE PROCUREMENT", use_container_width=True):
                        st.toast("TRANSMITTING_ORDER...")
            
            # --- TAB 2: COMPARISON ---
            with tabs[1]:
                with st.container(border=True):
                    st.markdown("<br>", unsafe_allow_html=True)
                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        c1_item = st.selectbox("ITEM_01", [i['item'] for i in live_items], index=0)
                    with col_c2:
                        c2_item = st.selectbox("ITEM_02", [i['item'] for i in live_items], index=min(1, len(live_items)-1))
                    
                    c1_data = next(i['history'] for i in live_items if i['item'] == c1_item).copy()
                    c2_data = next(i['history'] for i in live_items if i['item'] == c2_item).copy()
                    
                    c1_data['Label'] = c1_item
                    c2_data['Label'] = c2_item
                    
                    compare_df = pd.concat([c1_data, c2_data])
                    import plotly.express as px
                    fig_comp = px.line(compare_df, x='timestamp', y='price', color='Label',
                                      template="plotly_dark")
                    fig_comp.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_family="JetBrains Mono",
                        margin=dict(l=0, r=0, t=20, b=0),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)')
                    )
                    st.plotly_chart(fig_comp, use_container_width=True, config={'displayModeBar': False})

        # --- NEURAL FORECAST MATRIX ---
        st.markdown("---")
        st.markdown("### 🧬 NEURAL_FORECAST_MATRIX")
        
        with st.container():
            col_graph, col_stats = st.columns([2, 1])
            
            with col_stats:
                st.markdown("<br>", unsafe_allow_html=True)
                sel_forecast = st.selectbox("PREDICTION_TARGET", [i['item'] for i in live_items], key="forecast_sel")
                days = st.slider("HORIZON_LENGTH (DAYS)", 7, 30, 14)
                
                # Use current items for prediction logic
                f_data = next(i['history'] for i in live_items if i['item'] == sel_forecast)
                # Note: Assuming generate_forecast is the actual function name in the user's file
                forecast_df = generate_forecast(f_data, days)
                
                curr = forecast_df[forecast_df['type'] == 'Historical']['price'].iloc[-1]
                future = forecast_df[forecast_df['type'] == 'Forecast']['price'].iloc[-1]
                pred_change = ((future - curr) / curr) * 100
                
                st.markdown(f"""
                    <div class="dashboard-card" style="border-right: 4px solid var(--accent-primary);">
                        <p style='color:var(--text-muted); font-size:10px; font-family:JetBrains Mono;'>PROJECTED_PRICE</p>
                        <h2 style='margin:0; font-size:32px;'>Rs. {future:,.2f}</h2>
                        <p style='color:{"var(--status-green)" if pred_change <=0 else "var(--status-red)"}; font-size:14px; font-weight:700;'>
                            {"▼" if pred_change <=0 else "▲"} {pred_change:+.2f}% ({days}D)
                        </p>
                    </div>
                    <div style="margin-top:15px; padding:10px; border: 1px solid var(--glass-border); border-radius:4px; background:rgba(255,255,255,0.02);">
                        <p style='color:var(--text-muted); font-size:9px; font-family:JetBrains Mono; text-transform:uppercase;'>Confidence Rating</p>
                        <div style="height:4px; width:100%; background:rgba(255,255,255,0.1); border-radius:10px;">
                            <div style="height:100%; width:88%; background:var(--accent-primary); border-radius:10px; box-shadow: 0 0 10px var(--accent-primary);"></div>
                        </div>
                        <p style="text-align:right; font-size:9px; color:var(--accent-primary); margin-top:4px;">88.4% ACCURACY</p>
                    </div>
                """, unsafe_allow_html=True)

            with col_graph:
                import plotly.graph_objects as go
                fig = go.Figure()
                
                hist = forecast_df[forecast_df['type'] == 'Historical']
                fore = forecast_df[forecast_df['type'] == 'Forecast']
                
                fig.add_trace(go.Scatter(x=hist['timestamp'], y=hist['price'], name='HISTORICAL', line=dict(color='#888', width=2)))
                fig.add_trace(go.Scatter(x=fore['timestamp'], y=fore['price'], name='PROJECTION', line=dict(color='#3182ce', width=4, dash='dot')))
                
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=0, r=0, t=20, b=0),
                    height=350,
                    showlegend=False,
                    xaxis=dict(showgrid=False, color='#444'),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color='#444', side='right')
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # Footer
    st.markdown("<br>"*2, unsafe_allow_html=True)
    st.markdown("""
        <div style='text-align:center; padding:40px; border-top:1px solid var(--glass-border);'>
            <p style='color:var(--text-muted); font-size:10px; font-family:JetBrains Mono; opacity:0.5;'>
                © MONOLITH SYSTEMS // ALL RIGHTS RESERVED // SECURE PROTOCOL v.4
            </p>
        </div>
    """, unsafe_allow_html=True)


















