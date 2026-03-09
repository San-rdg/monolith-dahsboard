import pandas as pd
import streamlit as st
import numpy as np
import os
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="MONOLITH | INTELLIGENCE GRID", page_icon="🏗️", layout="wide")
st_autorefresh(interval=30000, key="datarefresh")

# --- 2. TACTICAL STYLING (PALANTIR-INSPIRED) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&family=IBM+Plex+Mono:wght@500&display=swap');

    :root {
        --bg-deep: #0e1217;
        --bg-surface: #15191e;
        --border-muted: #2a2f35;
        --accent-primary: #3d8bff;
        --accent-success: #2ea043;
        --accent-warning: #d29922;
        --text-main: #c9d1d9;
        --text-dim: #8b949e;
    }

    .stApp {
        background-color: var(--bg-deep);
        color: var(--text-main);
        font-family: 'IBM Plex Sans', sans-serif;
    }

    /* System Grid Overlay */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background-image: 
            linear-gradient(var(--border-muted) 1px, transparent 1px),
            linear-gradient(90deg, var(--border-muted) 1px, transparent 1px);
        background-size: 40px 40px;
        opacity: 0.03;
        pointer-events: none;
        z-index: 0;
    }

    /* Sharp Industrial Cards */
    .dashboard-card {
        background: var(--bg-surface);
        border: 1px solid var(--border-muted);
        border-radius: 2px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        position: relative;
        transition: border-color 0.2s ease;
        animation: tacticalEntry 0.3s ease-out backwards;
    }

    .dashboard-card:hover {
        border-color: var(--accent-primary);
    }

    @keyframes tacticalEntry {
        from { opacity: 0; transform: translateY(4px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* System Status Header */
    .sys-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 15px;
        background: #1c2128;
        border-bottom: 2px solid var(--accent-primary);
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        color: var(--text-dim);
        margin-bottom: 24px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    h1 {
        font-size: 28px;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.5px;
        margin-bottom: 30px !important;
        padding-left: 10px;
        border-left: 4px solid var(--accent-primary);
    }

    .card-header {
        color: var(--text-main);
        font-weight: 600;
        font-size: 0.85rem;
        border-bottom: 1px solid var(--border-muted);
        padding-bottom: 12px;
        margin-bottom: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .status-tag {
        background: rgba(61, 139, 255, 0.1);
        color: var(--accent-primary);
        padding: 2px 8px;
        font-size: 0.65rem;
        font-family: 'IBM Plex Mono', monospace;
        border: 1px solid var(--accent-primary);
        border-radius: 2px;
    }

    /* High Density Feed */
    .feed-row {
        display: grid;
        grid-template-columns: 1fr auto;
        padding: 10px 8px;
        border-bottom: 1px solid #1c2128;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.85rem;
    }

    .feed-row:hover {
        background: rgba(255, 255, 255, 0.02);
    }

    .feed-item-name { color: var(--accent-primary); font-weight: 600; }
    .feed-price { color: #ffffff; font-weight: 600; }
    .feed-id { color: var(--text-dim); font-size: 0.7rem; }

    /* Tactical Value Display */
    .total-display {
        border-left: 2px solid var(--accent-success);
        background: #0d1117;
        padding: 20px;
        margin-top: 15px;
    }

    .total-label {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        color: var(--text-dim);
        margin-bottom: 5px;
    }

    .total-value {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 2.2rem;
        color: var(--accent-success);
        font-weight: 700;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-thumb { background: var(--border-muted); }

    .live-indicator {
        width: 8px;
        height: 8px;
        background: var(--accent-success);
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
        box-shadow: 0 0 8px var(--accent-success);
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA UTILITIES & FORECASTING ---
def fetch_live_market_data():
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, "price_history.csv")
    if not os.path.exists(file_path): return pd.DataFrame() # Return empty dataframe
    try:
        df = pd.read_csv(file_path)
        df.columns = [c.strip().lower() for c in df.columns]
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])
        
        # Clean prices into floats
        df['price'] = df['price'].apply(lambda x: float(str(x).replace(',', '').strip()) if pd.notnull(x) else np.nan)
        df = df.dropna(subset=['price'])
        return df
    except Exception as e:
        st.sidebar.error(f"System Alert: {e}")
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
            if prev_price != 0:
                change_pct = ((current_price - prev_price) / prev_price) * 100
                
        latest_items.append({
            "item": item_name, 
            "price": current_price, 
            "change": round(change_pct, 2), 
            "source": item_history.iloc[-1].get('source', 'Market')
        })
    return latest_items

def generate_forecast(df, item_name, days_ahead=7):
    """Lightweight Linear Regression Forecast"""
    item_df = df[df['item'] == item_name].sort_values('timestamp').copy()
    
    if len(item_df) < 2:
        return None, "Not enough historical data to generate a forecast."
        
    # Convert dates to numbers for math
    item_df['date_num'] = (item_df['timestamp'] - item_df['timestamp'].min()).dt.days
    
    # Calculate trend line (y = mx + b)
    z = np.polyfit(item_df['date_num'], item_df['price'], 1)
    p = np.poly1d(z)
    
    # Generate future dates
    last_date = item_df['timestamp'].max()
    future_dates = [last_date + timedelta(days=i) for i in range(1, days_ahead + 1)]
    future_nums = [(d - item_df['timestamp'].min()).days for d in future_dates]
    
    # Predict future prices
    future_prices = p(future_nums)
    
    # Combine into a clean dataframe for the chart
    historical_chart = pd.DataFrame({'Date': item_df['timestamp'], 'Actual Price': item_df['price']}).set_index('Date')
    future_chart = pd.DataFrame({'Date': future_dates, 'Predicted Trend': future_prices}).set_index('Date')
    
    return pd.concat([historical_chart, future_chart]), z[0] # Return chart data and the slope (trend direction)

# --- 4. MAIN UI ---
st.markdown(f"""
    <div class="sys-header">
        <div>SYSTEM: MONOLITH-GRID // SECTOR: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        <div>LATENCY: 1.2MS // UPTIME: 99.9% // STATUS: NOMINAL</div>
    </div>
""", unsafe_allow_html=True)

st.markdown("<h1>MONOLITH COMMAND</h1>", unsafe_allow_html=True)

df_raw = fetch_live_market_data()
live_items = process_latest_items(df_raw)

if not live_items:
    st.warning("⚠️ Neural Engine offline. Awaiting data sync from GitHub Actions...")
else:
    # Main Split Layout
    col_feed, col_tools = st.columns([1.2, 1.8])
    
    # LEFT COLUMN: Live Feed
    with col_feed:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-header">DATA INTERROGATION <span class="status-tag">REAL-TIME</span></div>', unsafe_allow_html=True)
        for idx, item in enumerate(live_items):
            arrow = "▲" if item['change'] > 0 else "▼" if item['change'] < 0 else "—"
            color = "var(--accent-success)" if item['change'] > 0 else "var(--danger)" if item['change'] < 0 else "var(--text-dim)"
            st.markdown(f"""
                <div class="feed-row" style="animation-delay: {idx * 0.05}s;">
                    <div>
                        <div class="feed-item-name">{item['item']}</div>
                        <div class="feed-id">HASH: {abs(hash(item['item'])) % 10000} // SRC: {item.get('source', 'AUTO')}</div>
                    </div>
                    <div style="text-align:right;">
                        <div class="feed-price">L {item['price']:,.2f}</div>
                        <div style="color:{color}; font-size:0.7rem;">{arrow} {abs(item['change'])}%</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # RIGHT COLUMN: Tools (Tabs for Estimator & Forecast)
    with col_tools:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        
        # Create Tabs to save space and look professional
        tab_est, tab_forecast = st.tabs(["🧮 Dynamic Estimator", "📈 Market Forecast Engine"])
        
        # --- TAB 1: ESTIMATOR ---
        with tab_est:
            st.write("Calculate real-time project costs based on current market rates.")
            item_names = [i['item'] for i in live_items]
            selected_material = st.selectbox("Select Material", item_names, key="est_mat")
            current_price = next(i['price'] for i in live_items if i['item'] == selected_material)
            
            quantity = st.number_input("Quantity (Units)", min_value=1.0, value=100.0, step=10.0)
            total_cost = current_price * quantity
            
            st.markdown(f"""
                <div class="total-display">
                    <div class="total-label">Estimated Total Cost</div>
                    <div class="total-value">Rs. {total_cost:,.2f}</div>
                    <div style="color: #8b949e; font-size: 0.8rem; margin-top: 10px;">Live Unit Rate: Rs. {current_price:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)

        # --- TAB 2: FORECASTING ---
        with tab_forecast:
            st.write("Predictive algorithm estimating 7-day price trajectories.")
            forecast_material = st.selectbox("Select Material to Analyze", item_names, key="for_mat")
            
            chart_data, trend_slope = generate_forecast(df_raw, forecast_material)
            
            if chart_data is None:
                st.info(trend_slope) # Shows the "Not enough data" message
            else:
                # Display the Chart
                st.line_chart(chart_data, color=["#58a6ff", "#ff7b72"])
                
                # Dynamic text based on the math
                st.markdown('<div style="margin-top:20px; padding:10px; border:1px solid var(--border-muted); background:rgba(255,255,255,0.02);">', unsafe_allow_html=True)
                if trend_slope > 0.5:
                    st.markdown("<div style='color:var(--accent-warning); font-family:\"IBM Plex Mono\", monospace; font-size:0.8rem;'>[!] RISK LEVEL: SIGNIFICANT INFLATION</div>", unsafe_allow_html=True)
                    st.error("🚨 Algorithm predicts price inflation next week. Recommend bulk purchasing now.")
                elif trend_slope < -0.5:
                    st.markdown("<div style='color:var(--accent-success); font-family:\"IBM Plex Mono\", monospace; font-size:0.8rem;'>[+] RISK LEVEL: LOW (DOWNWARD TREND)</div>", unsafe_allow_html=True)
                    st.success("📉 Prices are trending downward. Delaying purchases may save capital.")
                else:
                    st.markdown("<div style='color:var(--accent-primary); font-family:\"IBM Plex Mono\", monospace; font-size:0.8rem;'>[/] RISK LEVEL: NOMINAL</div>", unsafe_allow_html=True)
                    st.info("⚖️ Market shows high stability. Price fluctuation unlikely next week.")
                st.markdown('</div>', unsafe_allow_html=True)
                    
        st.markdown('</div>', unsafe_allow_html=True)



