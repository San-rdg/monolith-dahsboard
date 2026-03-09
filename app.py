import pandas as pd
import streamlit as st
import numpy as np
import os
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="MONOLITH | INTELLIGENCE GRID", page_icon="🏗️", layout="wide")
st_autorefresh(interval=30000, key="datarefresh")

# --- 2. PREMIUM STYLING (CSS) ---
st.markdown("""
    <style>
    .stApp {background-color: #0d1117;}
    .dashboard-card {
        background-color: #161b22; border: 1px solid #30363d; 
        border-radius: 12px; padding: 24px; margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    h1 {font-size: 36px; font-weight: 900; color: #ffffff; letter-spacing: 1px;}
    .card-header {color: #58a6ff; font-weight: 700; font-size: 1.2rem; margin-bottom: 15px; border-bottom: 1px solid #30363d; padding-bottom: 10px;}
    .feed-row {display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #21262d;}
    .feed-item-name {color: #e6edf3; font-size: 1.1rem; font-weight: 600;}
    .feed-price {color: #ffffff; font-family: 'Courier New', monospace; font-weight: 700; font-size: 1.25rem;}
    .total-display {background: linear-gradient(145deg, #1f242c, #161b22); border: 1px solid #30363d; border-radius: 8px; padding: 20px; text-align: center; margin-top: 20px;}
    .total-label {color: #8b949e; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px;}
    .total-value {color: #3fb950; font-size: 2.5rem; font-weight: 800; font-family: 'Courier New', monospace;}
    .live-indicator {color: #ff7b72; animation: blinker 1.5s linear infinite;}
    @keyframes blinker { 50% { opacity: 0; } }
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
st.markdown("<h1><span class='live-indicator'>●</span> MONOLITH COMMAND CENTER</h1>", unsafe_allow_html=True)

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
        st.markdown('<div class="card-header">📡 LIVE MARKET FEED</div>', unsafe_allow_html=True)
        for item in live_items:
            arrow = "▲" if item['change'] > 0 else "▼" if item['change'] < 0 else "—"
            color = "#3fb950" if item['change'] > 0 else "#f85149" if item['change'] < 0 else "#8b949e"
            st.markdown(f"""
                <div class="feed-row">
                    <div>
                        <div class="feed-item-name">📦 {item['item']}</div>
                    </div>
                    <div style="text-align:right;">
                        <div class="feed-price">Rs. {item['price']:,.2f}</div>
                        <div style="color:{color}; font-size:0.9rem; font-weight:bold; margin-top: 4px;">{arrow} {abs(item['change'])}%</div>
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
                if trend_slope > 0.5:
                    st.error("🚨 **Warning:** Algorithm predicts price inflation next week. Recommend bulk purchasing now.")
                elif trend_slope < -0.5:
                    st.success("📉 **Favorable:** Prices are trending downward. Delaying purchases may save capital.")
                else:
                    st.info("⚖️ **Stable:** Market shows high stability. Price fluctuation unlikely next week.")
                    
        st.markdown('</div>', unsafe_allow_html=True)

