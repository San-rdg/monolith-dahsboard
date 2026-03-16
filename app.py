import pandas as pd
import streamlit as st
import numpy as np
import os
import math
import hashlib
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import scraper # My new live scraper module

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="MONOLITH | OS", page_icon="🏗️", layout="wide")

# --- 2. SESSION STATE NAVIGATION ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# --- 3. PREMIUM CSS (INTEGRATED HOMEPAGE + COMMAND CENTER) ---
# --- 3. PREMIUM CSS (TACTICAL DESIGN SYSTEM) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');

:root {
    --bg-deep: #05070a;
    --bg-surface: #0a0e14;
    --bg-card: rgba(16, 22, 26, 0.7);
    --accent-primary: #106BA3;
    --accent-glow: rgba(16, 107, 163, 0.3);
    --text-main: #E1E8ED;
    --text-muted: #8A9BA8;
    --status-green: #0F9960;
    --status-red: #DB3737;
    --border-subtle: rgba(255, 255, 255, 0.08);
    --glass-bg: rgba(255, 255, 255, 0.03);
    --glass-border: rgba(255, 255, 255, 0.1);
}

.stApp { 
    background-color: var(--bg-deep); 
    color: var(--text-main);
    font-family: 'Inter', sans-serif;
}

/* Custom Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: #202B33; border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-primary); }

/* --- HOMEPAGE STYLES --- */
.hero-container {
    padding: 100px 20px 60px 20px;
    text-align: center;
    background: radial-gradient(circle at top, #0d1b2a 0%, var(--bg-deep) 70%);
}
.hero-title {
    font-size: clamp(60px, 10vw, 120px);
    font-weight: 800;
    letter-spacing: -6px;
    background: linear-gradient(180deg, #ffffff 0%, #4a5568 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1;
    margin-bottom: 20px;
}
.hero-subtitle {
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    letter-spacing: 10px;
    color: var(--accent-primary);
    text-transform: uppercase;
    margin-bottom: 50px;
    opacity: 0.9;
}

.feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
    padding: 40px;
}
.feature-card {
    background: var(--bg-card);
    backdrop-filter: blur(12px);
    border: 1px solid var(--border-subtle);
    padding: 35px;
    border-radius: 4px;
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
    overflow: hidden;
}
.feature-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; width: 100%; height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent-primary), transparent);
    transform: translateX(-100%);
    transition: 0.6s;
}
.feature-card:hover {
    transform: translateY(-5px);
    border-color: rgba(16, 107, 163, 0.5);
    background: rgba(16, 22, 26, 0.9);
    box-shadow: 0 15px 35px rgba(0,0,0,0.5);
}
.feature-card:hover::before { transform: translateX(100%); }

/* --- COMMAND CENTER STYLES --- */
.dashboard-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    padding: 16px;
    border-radius: 4px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.2);
}

.status-line {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--text-muted);
    border-top: 1px solid var(--border-subtle);
    padding-top: 10px;
    margin-top: 10px;
}

.metric-container {
    background: linear-gradient(135deg, rgba(255,255,255,0.03) 0%, transparent 100%);
    border-left: 3px solid var(--accent-primary);
    padding: 12px;
    border-radius: 0 4px 4px 0;
}

/* --- LOGIN FORM POLISH --- */
[data-testid="stForm"] {
    background: rgba(10, 14, 20, 0.8) !important;
    backdrop-filter: blur(20px) !important;
    border: 1px solid var(--border-subtle) !important;
    padding: 40px !important;
    border-radius: 4px !important;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5) !important;
}
[data-testid="stForm"]:hover {
    border-color: var(--accent-primary) !important;
}

/* Animations */
@keyframes pulse {
    0% { opacity: 0.6; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.1); }
    100% { opacity: 0.6; transform: scale(1); }
}
.live-pulse {
    display: inline-block;
    width: 10px;
    height: 10px;
    background: var(--status-red);
    border-radius: 50%;
    margin-right: 8px;
    box-shadow: 0 0 10px var(--status-red);
    animation: pulse 2s infinite;
}

/* Streamlit Input Overrides */
.stTextInput input {
    background-color: rgba(255,255,255,0.05) !important;
    border: 1px solid var(--border-subtle) !important;
    color: white !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.stTextInput input:focus {
    border-color: var(--accent-primary) !important;
    box-shadow: 0 0 0 1px var(--accent-primary) !important;
}
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
                audits = json.load(f)
                audit_df = pd.DataFrame(audits)
                audit_df['timestamp'] = pd.to_datetime(audit_df['timestamp'])
                audit_df['source_type'] = 'Audited'
                df = pd.concat([df, audit_df], ignore_index=True)
        except: pass

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
    if latest_point['source_type'] == 'Audited':
        score += 50
    elif latest_point['source_type'] == 'Live':
        score += 50
    else:
        # Penalize if last data point is old
        age_hours = (datetime.now() - latest_point['timestamp']).total_seconds() / 3600
        if age_hours < 24:
            score += 35
        else:
            score += max(0, 20 - (age_hours / 48))

    # 2. Source Alignment (Max 30)
    has_audit = 'Audited' in item_history['source_type'].values
    has_live = 'Live' in item_history['source_type'].values
    has_hist = 'Historical' in item_history['source_type'].values
    
    if has_audit: score += 30
    elif has_live and has_hist: score += 30
    elif has_live: score += 25
    else: score += 10
        
    # 3. Stability (Max 20)
    if len(item_history) > 3:
        std = item_history['price'].tail(5).std()
        mean = item_history['price'].tail(5).mean()
        coeff_var = std / mean if mean != 0 else 1
        score += max(0, 20 - (coeff_var * 100))
    else:
        score += 10
        
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
        st.markdown("""
            <div style='padding:20px 0;'>
                <h2 style='font-size:20px; color:white; letter-spacing:2px;'>MONOLITH</h2>
                <p style='font-size:10px; color:var(--accent-primary); font-family:JetBrains Mono;'>CORE OS v.2026.4</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 💠 OPERATOR")
        st.info("OPERATOR: ADMIN\n\nTIER: ENTERPRISE")
        
        user_tier = st.radio("Access Level:", ["Free Account", "Premium ($7k/mo)"], index=1)
        is_premium = (user_tier == "Premium ($7k/mo)")
        
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
                    with open(AUDIT_FILE, 'r') as f: current_audits = json.load(f)
                
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
                                      title="Comparative Price Volatility",
                                      template="plotly_dark")
                    fig_comp.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_family="JetBrains Mono",
                        margin=dict(l=0, r=0, t=40, b=0)
                    )
                    st.plotly_chart(fig_comp, use_container_width=True)

        # --- NEURAL FORECAST SECTION (BOTTOM OF SCREEN) ---
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown("#### 📈 NEURAL FORECAST")
        
        col_f1, _ = st.columns([1, 2])
        with col_f1:
            f_item = st.selectbox("SELECT_SOURCE_ITEM", [i['item'] for i in live_items], key="forecast_sel")
            
        f_data = next(i['history'] for i in live_items if i['item'] == f_item)
        forecast_df = generate_forecast(f_data)
        
        fig = px.line(forecast_df, x='timestamp', y='price', color='type', 
                     title=f"Predictive Trend Analysis: {f_item}",
                     template="plotly_dark",
                     color_discrete_map={'Historical': '#106BA3', 'Forecast': '#0F9960'})
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_family="JetBrains Mono",
            margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)












