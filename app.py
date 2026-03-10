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

# --- 2. ULTRA-PREMIUM STYLING (CSS) ---
st.markdown("""
    <style>
    /* Global futuristic vibe */
    .stApp { background: radial-gradient(circle at top right, #1a1f25, #0d1117); color: #e6edf3; }
    
    /* Glassmorphism Cards */
    .dashboard-card {
        background: rgba(22, 27, 34, 0.7); backdrop-filter: blur(10px);
        border: 1px solid rgba(88, 166, 255, 0.2); border-radius: 16px;
        padding: 24px; margin-bottom: 20px; transition: all 0.4s ease;
    }
    .dashboard-card:hover {
        border-color: #58a6ff; box-shadow: 0 0 20px rgba(88, 166, 255, 0.15); transform: translateY(-3px);
    }
    
    /* Typography & Animations */
    .main-title {
        background: linear-gradient(90deg, #ffffff, #58a6ff, #ffffff); background-size: 200% auto;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        animation: shine 3s linear infinite; font-size: 42px; font-weight: 900; letter-spacing: 2px;
    }
    @keyframes shine { to { background-position: 200% center; } }
    
    [data-testid="stMetricValue"] { font-family: 'Courier New', monospace; text-shadow: 0 0 10px rgba(88, 166, 255, 0.5); }
    .card-header { color: #58a6ff; font-weight: 700; font-size: 1.2rem; margin-bottom: 15px; border-bottom: 1px solid #30363d; padding-bottom: 10px; }
    
    /* Feed Rows */
    .feed-row { display: flex; justify-content: space-between; padding: 15px 10px; border-bottom: 1px solid rgba(48, 54, 61, 0.5); }
    .feed-item-name { font-size: 1.1rem; font-weight: 600; }
    .feed-price { font-family: 'Courier New', monospace; font-weight: 700; font-size: 1.25rem; }
    
    /* Logistics & Estimator UI */
    .total-display {
        background: rgba(0, 0, 0, 0.4); border-radius: 12px; padding: 25px;
        border-left: 5px solid #3fb950; box-shadow: inset 0 0 15px rgba(63, 185, 80, 0.1); margin-top: 20px;
    }
    .premium-badge { color: #3fb950; font-weight: bold; text-shadow: 0 0 8px rgba(63,185,80,0.5); font-size: 0.8rem; letter-spacing: 1px; }
    .upgrade-box {
        background: rgba(255, 123, 114, 0.1); border: 1px solid #ff7b72; border-radius: 8px;
        padding: 15px; text-align: center; margin-top: 15px;
    }
    .live-indicator { color: #ff7b72; animation: blinker 1.5s linear infinite; }
    @keyframes blinker { 50% { opacity: 0; } }
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
# Simulation Toggle for Exhibition
st.sidebar.markdown("### ⚙️ Presentation Controls")
user_tier = st.sidebar.radio("Simulate User Tier:", ["Free Account", "Premium ($7k/mo)"])
is_premium = (user_tier == "Premium ($7k/mo)")

st.markdown("<h1 class='main-title'><span class='live-indicator'>●</span> MONOLITH COMMAND</h1>", unsafe_allow_html=True)

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
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-header">📡 LIVE INTELLIGENCE FEED</div>', unsafe_allow_html=True)
        for item in live_items:
            color = "#3fb950" if item['change'] >= 0 else "#f85149"
            st.markdown(f"""
                <div class="feed-row">
                    <div>
                        <div class="feed-item-name">{item['item']}</div>
                        <div style="font-size:0.7rem; color:#8b949e;">SRC: {item['source'].upper()}</div>
                    </div>
                    <div style="text-align:right;">
                        <div class="feed-price">Rs.{item['price']:,.0f}</div>
                        <div style="color:{color}; font-size:0.8rem; font-weight:bold;">{item['change']:+.2f}%</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
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
                st.markdown("<span class='premium-badge'>● PRO LOGISTICS ACTIVE</span>", unsafe_allow_html=True)
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
                        <div style="font-size: 1.5rem; margin-bottom: 5px;">🔒</div>
                        <div style="color: #ff7b72; font-weight: bold;">ENTERPRISE FEATURE</div>
                        <div style="font-size: 0.85rem; color: #c9d1d9;">Upgrade to the Rs. 7,000/mo tier to unlock automated fleet routing, live distance calculations, and transport cost prediction.</div>
                    </div>
                """, unsafe_allow_html=True)

            # Final Checkout Display
            grand_total = material_cost + transport_cost
            st.markdown(f"""
                <div class="total-display">
                    <div style="display: flex; justify-content: space-between; color: #8b949e; font-size: 0.9rem; margin-bottom: 5px;">
                        <span>Material Subtotal:</span> <span>Rs. {material_cost:,.2f}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; color: #8b949e; font-size: 0.9rem; margin-bottom: 15px; border-bottom: 1px solid #30363d; padding-bottom: 10px;">
                        <span>Transport Surcharge:</span> <span>Rs. {transport_cost:,.2f}</span>
                    </div>
                    <div style="color:#e6edf3; font-size:0.85rem; letter-spacing: 1px; margin-bottom: 5px;">TOTAL PROJECT ESTIMATE</div>
                    <div style="color:#3fb950; font-size:2.5rem; font-weight:800; font-family:'Courier New', monospace;">Rs. {grand_total:,.2f}</div>
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

