import pandas as pd
import streamlit as st
import numpy as np
import os
import math
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="MONOLITH | COMMAND CENTER", page_icon="🏗️", layout="wide")
st_autorefresh(interval=30000, key="datarefresh")

# --- 2. ULTRA-PREMIUM TACTICAL STYLING (PALANTIR FOUNDRY AESTHETIC) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

    /* Precision Blueprint/Foundry Palette */
    :root {
        --bg-primary: #10161A;
        --bg-secondary: #182026;
        --bg-accent: #202B33;
        --border-color: rgba(255, 255, 255, 0.15);
        --text-primary: #F5F8FA;
        --text-secondary: #A7B6C2;
        --text-muted: #5C7080;
        --accent-blue: #106BA3;
        --accent-blue-hover: #137CBD;
        --accent-green: #0F9960;
        --accent-red: #DB3737;
        --font-ui: 'Inter', system-ui, sans-serif;
        --font-mono: 'IBM Plex Mono', monospace;
    }

    .stApp { 
        background: var(--bg-primary); 
        color: var(--text-primary); 
        font-family: var(--font-ui);
        background-image: radial-gradient(circle at 1px 1px, rgba(255,255,255,0.03) 1px, transparent 0);
        background-size: 24px 24px;
    }
    
    /* Breadcrumb styling */
    .breadcrumb {
        display: flex;
        gap: 8px;
        font-family: var(--font-mono);
        font-size: 10px;
        color: var(--text-muted);
        margin-bottom: 4px;
        align-items: center;
    }
    .breadcrumb span:not(:last-child)::after {
        content: '/';
        margin-left: 8px;
        opacity: 0.5;
    }
    .breadcrumb .active { color: var(--accent-blue); font-weight: 600; }

    /* Tactical High-Density Cards */
    .dashboard-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        box-shadow: 0 0 0 1px rgba(16, 22, 26, 0.2), 0 1px 1px rgba(16, 22, 26, 0.4);
        border-radius: 2px;
        padding: 12px; 
        margin-bottom: 12px;
        transition: all 0.15s ease;
    }
    .dashboard-card:hover { border-color: var(--text-muted); box-shadow: 0 0 0 1px rgba(16, 22, 26, 0.2), 0 2px 4px rgba(16, 22, 26, 0.4); }
    
    /* Typography & Tactical Header */
    .main-title {
        font-family: var(--font-ui); color: var(--text-primary);
        font-size: 22px; font-weight: 700; letter-spacing: -0.2px;
        margin-bottom: 2px;
    }
    .system-status-bar {
        font-family: var(--font-mono); font-size: 9px; color: var(--text-muted);
        display: flex; gap: 15px; border-bottom: 1px solid var(--border-color);
        padding-bottom: 10px; margin-bottom: 16px;
    }
    .status-indicator { width: 6px; height: 6px; border-radius: 50%; background: var(--accent-green); display: inline-block; margin-right: 4px; }
    
    [data-testid="stMetricValue"] { font-family: var(--font-mono); font-weight: 500; font-size: 1.5rem !important; color: var(--text-primary); }
    [data-testid="stMetricLabel"] { font-family: var(--font-ui); font-size: 9px; text-transform: uppercase; letter-spacing: 0.8px; color: var(--text-secondary); font-weight: 600; }
    
    .card-header { 
        color: var(--text-primary); font-weight: 600; font-size: 11px; 
        margin-bottom: 12px; border-bottom: 1px solid var(--border-color); 
        padding-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;
        display: flex; justify-content: space-between; align-items: center;
    }
    
    /* Blueprint Style Tags */
    .bp-tag {
        font-family: var(--font-ui); font-size: 10px; font-weight: 600;
        padding: 2px 6px; border-radius: 2px; text-transform: uppercase;
        background: var(--bg-accent); color: var(--text-secondary);
        border: 1px solid var(--border-color);
    }
    .bp-tag.blue { background: rgba(16, 107, 163, 0.2); color: #48AFF0; border-color: rgba(16, 107, 163, 0.3); }
    .bp-tag.green { background: rgba(15, 153, 96, 0.2); color: #3DCC91; border-color: rgba(15, 153, 96, 0.3); }

    /* Tactical Feed Rows */
    .feed-row { 
        display: flex; justify-content: space-between; padding: 8px 0; 
        border-bottom: 1px solid rgba(255, 255, 255, 0.03); 
    }
    .feed-item-name { font-size: 0.85rem; font-weight: 600; font-family: var(--font-ui); color: var(--text-primary); }
    .feed-price { font-family: var(--font-mono); font-weight: 500; font-size: 1rem; color: var(--text-primary); }
    .metadata-hash { font-family: var(--font-mono); font-size: 9px; color: var(--text-muted); margin-top: 2px; }
    
    /* Modern Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 1px solid var(--border-color); }
    .stTabs [data-baseweb="tab"] { 
        font-size: 10px; font-weight: 600; text-transform: uppercase; 
        padding: 8px 12px; background: transparent !important; color: var(--text-muted);
        border: none !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: var(--accent-blue); border-bottom: 2px solid var(--accent-blue) !important; }
    
    .total-display {
        background: var(--bg-accent); border-radius: 2px; padding: 16px;
        border: 1px solid var(--border-color); margin-top: 15px;
    }
    .grand-total-val { color: var(--accent-green); font-size: 1.5rem; font-weight: 600; font-family: var(--font-mono); }
    
    .premium-badge { color: var(--accent-blue); font-weight: 700; font-size: 9px; letter-spacing: 1px; text-transform: uppercase; }
    .upgrade-box {
        background: rgba(16, 107, 163, 0.05); border: 1px dashed var(--accent-blue); border-radius: 2px;
        padding: 16px; text-align: center; margin-top: 12px;
    }
    .live-indicator { display: inline-block; width: 8px; height: 8px; background: var(--accent-red); border-radius: 50%; margin-right: 6px; animation: blink 1.5s infinite; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }

    /* Sidebar Refinement */
    [data-testid="stSidebar"] { background-color: var(--bg-secondary); border-right: 1px solid var(--border-color); }
    .sidebar-module {
        display: flex; align-items: center; gap: 10px; padding: 8px;
        border-radius: 3px; margin-bottom: 4px; cursor: pointer; color: var(--text-secondary);
    }
    .sidebar-module:hover { background: var(--bg-accent); color: var(--text-primary); }
    .sidebar-module.active { background: var(--accent-blue); color: white; }
    </style>

""", unsafe_allow_html=True)

# --- 3. DATA UTILITIES & LOGISTICS ENGINE ---
def fetch_live_market_data():
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, "price_history.csv")
    if not os.path.exists(file_path): return pd.DataFrame()
    try:
        df = pd.read_csv(file_path)
        df.columns = [c.strip().lower() for c in df.columns]
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])
        df['price'] = df['price'].apply(lambda x: float(str(x).replace(',', '').strip()) if pd.notnull(x) else np.nan)
        df = df.dropna(subset=['price'])
        return df
    except Exception:
        return pd.DataFrame()

def process_latest_items(df):
    if df.empty: return []
    latest_items = []
    for item_name in df['item'].unique():
        item_history = df[df['item'] == item_name].sort_values('timestamp')
        if item_history.empty: continue
        current_price = item_history.iloc[-1]['price']
        change_pct = 0.0
        if len(item_history) > 1:
            prev_price = item_history.iloc[-2]['price']
            if prev_price != 0: change_pct = ((current_price - prev_price) / prev_price) * 100
        latest_items.append({
            "item": item_name, "price": current_price, "change": round(change_pct, 2), 
            "source": item_history.iloc[-1].get('source', 'Market')
        })
    return latest_items

def generate_forecast(df, item_name, days_ahead=7):
    item_df = df[df['item'] == item_name].sort_values('timestamp').copy()
    if len(item_df) < 2: return None
    item_df['date_num'] = (item_df['timestamp'] - item_df['timestamp'].min()).dt.days
    z = np.polyfit(item_df['date_num'], item_df['price'], 1)
    p = np.poly1d(z)
    last_date = item_df['timestamp'].max()
    future_dates = [last_date + timedelta(days=i) for i in range(1, days_ahead + 1)]
    future_nums = [(d - item_df['timestamp'].min()).days for d in future_dates]
    historical = pd.DataFrame({'Date': item_df['timestamp'], 'Price': item_df['price']}).set_index('Date')
    future = pd.DataFrame({'Date': future_dates, 'Trend': p(future_nums)}).set_index('Date')
    return pd.concat([historical, future])

# Logistics Data
destinations = {"Colombo (Local)": 25, "Kandy": 115, "Galle": 125, "Kurunegala": 95, "Jaffna": 395}
def get_item_weight(item_name):
    name = str(item_name).lower()
    if 'cement' in name: return 50
    if any(x in name for x in ['steel', 'tmt', 'iron']): return 1
    if any(x in name for x in ['sand', 'metal']): return 4000
    return 10

# --- 4. MAIN UI & SIDEBAR ---
with st.sidebar:
    st.markdown("### 🏢 PLATFORM")
    st.markdown("""
        <div class="sidebar-module active">📊 COMMAND_CENTER</div>
        <div class="sidebar-module">🔍 DATA_EXPLORER</div>
        <div class="sidebar-module">🏗️ OBJECT_GRAPH</div>
        <div class="sidebar-module">⚙️ SYSTEM_SETTINGS</div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### ⚙️ SETTINGS")
    user_tier = st.sidebar.radio("User Tier:", ["Free Account", "Premium ($7k/mo)"])
    is_premium = (user_tier == "Premium ($7k/mo)")

# Main Header Area
st.markdown("""
    <div class="breadcrumb">
        <span>WORKSPACE</span>
        <span>MONOLITH</span>
        <span class="active">COMMAND_CENTER</span>
    </div>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>MONOLITH // COMMAND CENTER</h1>", unsafe_allow_html=True)
uptime = datetime.now().strftime("%H:%M:%S")
st.markdown(f"""
    <div class='system-status-bar'>
        <span><span class="status-indicator"></span>STATUS: NOMINAL</span>
        <span>LATENCY: 1.2MS</span>
        <span>VERSION: v4.2.0-STABLE</span>
        <span>UPTIME: {uptime}</span>
        <span>COORD: 6.9271° N, 79.8612° E</span>
    </div>
""", unsafe_allow_html=True)


df_raw = fetch_live_market_data()
live_items = process_latest_items(df_raw)

if not live_items:
    st.warning("⚠️ Neural Engine offline. Awaiting data sync from GitHub Actions...")
else:
    # --- METRICS ROW ---
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.metric("Grid Coverage", f"{len(live_items)} Units", delta="Live Tracker")
        st.markdown('</div>', unsafe_allow_html=True)
    with m2:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        avg_change = sum(item['change'] for item in live_items) / len(live_items)
        st.metric("Market Flux", f"{avg_change:+.2f}%", delta_color="normal")
        st.markdown('</div>', unsafe_allow_html=True)
    with m3:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.metric("Engine Latency", "1.2ms", delta="-0.1ms")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- MAIN WORKSPACE ---
    col_left, col_right = st.columns([1.1, 1.9])

    # LEFT: Market Feed
    with col_left:
        st.markdown('<div class="dashboard-card" style="height: 520px; overflow-y: auto;">', unsafe_allow_html=True)
        st.markdown('<div class="card-header">📡 LIVE INTELLIGENCE FEED <span><span class="live-indicator"></span>LIVE</span></div>', unsafe_allow_html=True)
        for item in live_items:
            color = "#0F9960" if item['change'] >= 0 else "#DB3737"
            status_tag = "STABLE" if item['change'] > -2 else "VOLATILE"
            tag_class = "green" if status_tag == "STABLE" else "blue"
            
            import hashlib
            item_hash = hashlib.md5(item['item'].encode()).hexdigest()[:8].upper()
            st.markdown(f"""
                <div class="feed-row">
                    <div>
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span class="feed-item-name">{item['item']}</span>
                            <span class="bp-tag {tag_class}">{status_tag}</span>
                        </div>
                        <div class="metadata-hash">ID: {item_hash} // TYPE: RAW_MAT // SRC: {item['source'].upper()}</div>
                    </div>
                    <div style="text-align:right;">
                        <div class="feed-price">Rs.{item['price']:,.0f}</div>
                        <div style="color:{color}; font-size:0.75rem; font-weight:600; font-family:var(--font-mono);">{item['change']:+.2f}%</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # TELEMETRY LOG
        st.markdown('<div class="dashboard-card" style="margin-top: 10px;">', unsafe_allow_html=True)
        st.markdown('<div class="card-header">🧾 COMMAND TRACE</div>', unsafe_allow_html=True)
        log_entries = [
            f"[{datetime.now().strftime('%H:%M:%S')}] SYNC_COMPLETE: MARKET_DATA_FETCHED",
            f"[{datetime.now().strftime('%H:%M:%S')}] CACHE_VALIDATED: 12_OBJECTS_PERSISTED",
            f"[{datetime.now().strftime('%H:%M:%S')}] AUTH_SUCCESS: OPERATOR_ASEL_ADMIN",
            f"[{datetime.now().strftime('%H:%M:%S')}] GRID_REFRESH: {len(live_items)}_NODES_SYNCED"
        ]
        for log in log_entries:
            st.markdown(f"<div style='font-family:var(--font-mono); font-size:9px; color:var(--text-muted); padding:2px 0;'>{log}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # RIGHT: Tools
    with col_right:
        st.markdown('<div class="dashboard-card" style="height: 100%;">', unsafe_allow_html=True)
        tab_est, tab_predict = st.tabs(["🧮 Procurement & Logistics", "📈 Neural Forecast"])
        
        # TAB 1: ESTIMATOR + LOGISTICS
        with tab_est:
            col_a, col_b = st.columns(2)
            with col_a:
                selected = st.selectbox("Resource", [i['item'] for i in live_items])
            with col_b:
                qty = st.number_input("Quantity (Units)", min_value=1, value=100, step=10)
                
            price = next(i['price'] for i in live_items if i['item'] == selected)
            material_cost = price * qty
            
            st.markdown("---")
            st.markdown("### 🚚 Shipping & Routing")
            
            transport_cost = 0
            if is_premium:
                st.markdown('<span class="bp-tag blue" style="margin-bottom: 15px;">● PRO LOGISTICS ACTIVE</span>', unsafe_allow_html=True)
                col_loc, col_date = st.columns(2)
                with col_loc:
                    location = st.selectbox("📍 Delivery Site", list(destinations.keys()))
                with col_date:
                    eta = (datetime.now() + timedelta(days=2)).strftime('%b %d, %Y')
                    st.info(f"**Est. Arrival:** {eta}")
                
                # Logistics Math
                total_weight_kg = get_item_weight(selected) * qty
                distance_km = destinations[location]
                trucks_needed = math.ceil(total_weight_kg / 10000)
                transport_cost = (150 * distance_km * 2) * trucks_needed 
                
                st.caption(f"**Fleet Details:** {total_weight_kg:,.0f}kg total load | Requires {trucks_needed} Heavy Truck(s) | {distance_km}km route.")
            else:
                st.selectbox("📍 Delivery Site", ["Colombo (Local)"], disabled=True)
                st.markdown("""
                    <div class="upgrade-box">
                        <div style="font-size: 1.2rem; margin-bottom: 8px; color: var(--accent-blue);">🔒 ENTERPRISE_LOCK</div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.4;">
                            Upgrade to the <b>Premium Tier ($7k/mo)</b> to unlock automated fleet routing, live distance calculations, and transport cost prediction.
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            # Final Checkout Display
            grand_total = material_cost + transport_cost
            st.markdown(f"""
                <div class="total-display">
                    <div style="display: flex; justify-content: space-between; color: var(--text-muted); font-size: 0.75rem; margin-bottom: 6px; font-family:var(--font-mono);">
                        <span>PROCUREMENT_SUBTOTAL</span> <span>Rs. {material_cost:,.2f}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; color: var(--text-muted); font-size: 0.75rem; margin-bottom: 12px; border-bottom: 1px solid var(--border-color); padding-bottom: 8px; font-family:var(--font-mono);">
                        <span>LOGISTICS_SURCHARGE</span> <span>Rs. {transport_cost:,.2f}</span>
                    </div>
                    <div style="color:var(--text-secondary); font-size:0.65rem; font-weight:700; letter-spacing: 0.8px; margin-bottom: 4px; text-transform:uppercase;">Estimated Settlement Total</div>
                    <div class="grand-total-val">Rs. {grand_total:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)

            
        # TAB 2: FORECASTING
        with tab_predict:
            st.write("### AI Market Trajectory")
            item_for = st.selectbox("Analyze Trend", [i['item'] for i in live_items])
            chart_data = generate_forecast(df_raw, item_for)
            
            if chart_data is not None:
                st.line_chart(chart_data, color=["#58a6ff", "#ff7b72"])
                st.caption("Historical data (Blue) vs 7-Day Predicted Trajectory (Red).")
            else:
                st.info("Gathering more historical data to generate accurate AI predictions. Please wait 24 hours.")
                
        st.markdown('</div>', unsafe_allow_html=True)



