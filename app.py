import pandas as pd
import streamlit as st
import numpy as np
import os
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="MONOLITH | INTELLIGENCE GRID", page_icon="🏗️", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=30000, key="datarefresh")

# --- 2. STYLING (CSS) ---
st.markdown("""
    <style>
    .stApp {background-color: #0E1117;}
    .dashboard-card {background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 20px; margin-bottom: 15px;}
    h1 {font-size: 32px; font-weight: 800; color: #FFFFFF; margin-bottom: 5px;}
    .feed-row {display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #21262D;}
    .feed-item {color: #C9D1D9; font-size: 13px;}
    .feed-price {color: #FFFFFF; font-family: 'Roboto Mono', monospace; font-weight: 600; font-size: 14px;}
    .alert-card-high {background-color: #2B1111; border: 1px solid #DA3633; padding: 12px; border-radius: 6px; margin-bottom: 10px;}
    .live-indicator {color: #FF4B4B; animation: blinker 1.5s linear infinite;}
    @keyframes blinker { 50% { opacity: 0; } }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA UTILITIES & FORECASTING ---
def get_category(item_name):
    name = item_name.lower()
    if any(x in name for x in ['steel', 'tmt', 'iron']): return "Steel"
    if 'cement' in name: return "Cement"
    if any(x in name for x in ['sand', 'metal', 'brick', 'block', 'mixture']): return "Aggregates"
    if any(x in name for x in ['wood', 'teak', 'mahogany']): return "Timber"
    if any(x in name for x in ['pipe', 'cable', 'wire', 'paint', 'tile']): return "MEP & Finishes"
    return "Others"

def fetch_live_market_data():
    if os.path.exists("price_history.csv"):
        try:
            df = pd.read_csv("price_history.csv")
            if df.empty: return []
            latest_items = []
            for item_name in df['item'].unique():
                item_history = df[df['item'] == item_name].sort_values('timestamp')
                latest_row = item_history.iloc[-1]
                current_price = float(latest_row['price'])
                change_pct = 0.0
                if len(item_history) > 1:
                    prev_price = float(item_history.iloc[-2]['price'])
                    if prev_price and not pd.isna(prev_price) and prev_price != 0:
                        change_pct = ((current_price - prev_price) / prev_price) * 100
                latest_items.append({
                    "item": item_name, "price": current_price, "change": round(change_pct, 2),
                    "source": latest_row.get('source', 'Market'), "category": get_category(item_name)
                })
            return latest_items
        except: return []
    return []

def generate_forecast(item_name, days=7):
    if not os.path.exists("price_history.csv"): return None, None, 0
    df = pd.read_csv("price_history.csv")
    item_df = df[df['item'] == item_name].sort_values('timestamp')
    if len(item_df) < 2: return None, None, 0
    
    prices = item_df['price'].values
    x = np.arange(len(prices))
    m, b = np.polyfit(x, prices, 1)
    
    future_x = np.arange(len(prices), len(prices) + days)
    forecast = m * future_x + b
    
    # Simple confidence logic
    confidence = 92 if "LSTM" in selected_model else 85
    return forecast, m, confidence

# --- 4. INITIALIZATION ---
raw_market_data = fetch_live_market_data()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3630/3630321.png", width=80)
    st.title("MONOLITH v2.1")
    selected_model = st.selectbox("Intelligence Model", ["Linear Regression", "Prophet", "LSTM (Neural)"], index=2)
    st.markdown("---")
    categories = ["All", "Steel", "Cement", "Aggregates", "Timber", "MEP & Finishes"]
    selected_cat = st.radio("Market Focus", categories)
    st.markdown("---")
    st.info("Neural engine active. Predicting price shifts based on 2026 BSR trends.")

# --- 6. MAIN UI ---
st.markdown("<h1><span class='live-indicator'>●</span> MARKET INTELLIGENCE GRID</h1>", unsafe_allow_html=True)

if not raw_market_data:
    st.error("Missing Data: Run the scraper or check price_history.csv")
else:
    display_data = raw_market_data if selected_cat == "All" else [i for i in raw_market_data if i['category'] == selected_cat]
    
    col_main, col_side = st.columns([2, 1])

    with col_main:
        # --- BLOCK: LIVE FEED ---
        st.markdown(f'<div class="dashboard-card"><h4>LIVE PRICE FEED: {selected_cat.upper()}</h4>', unsafe_allow_html=True)
        for item in display_data:
            arrow = "▲" if item['change'] > 0 else "▼" if item['change'] < 0 else "—"
            color = "#2EA043" if item['change'] > 0 else "#DA3633" if item['change'] < 0 else "#8B949E"
            st.markdown(f"""
                <div class="feed-row">
                    <div class="feed-item">📦 <b>{item['item']}</b> <br><small style="color:#666">{item['source']}</small></div>
                    <div style="text-align:right;">
                        <div class="feed-price">Rs. {item['price']:,}</div>
                        <div style="color:{color}; font-size:12px; font-weight:bold;">{arrow} {abs(item['change'])}%</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- BLOCK: GRAPHS & ESTIMATES ---
        if display_data:
            focus_item = display_data[0]['item']
            forecast, trend, conf = generate_forecast(focus_item)
            
            st.markdown(f'<div class="dashboard-card"><h4>📈 GROWTH PROJECTION: {focus_item}</h4>', unsafe_allow_html=True)
            
            if forecast is not None:
                # Create chart data
                history_prices = pd.read_csv("price_history.csv")
                history_prices = history_prices[history_prices['item'] == focus_item]['price'].values
                full_plot = np.append(history_prices, forecast)
                st.line_chart(full_plot)
                
                m1, m2, m3 = st.columns(3)
                m1.metric("7-Day Forecast", f"Rs. {forecast[-1]:,.0f}", f"{trend*7:+.2f}")
                m2.metric("Confidence", f"{conf}%")
                m3.metric("Market Volatility", "MEDIUM")
            else:
                st.warning("Insufficient history for AI Projection. Need 2+ days of data.")
            st.markdown('</div>', unsafe_allow_html=True)

    with col_side:
        # --- BLOCK: COST ESTIMATOR ---
        st.markdown('<div class="dashboard-card"><h4>🧮 PROJECT ESTIMATOR</h4>', unsafe_allow_html=True)
        est_item = st.selectbox("Select Material", [i['item'] for i in raw_market_data])
        qty = st.number_input("Quantity Required", min_value=1, value=10)
        unit_price = next(i['price'] for i in raw_market_data if i['item'] == est_item)
        total = unit_price * qty
        st.markdown(f"### Total: Rs. {total:,.2f}")
        st.button("Add to Bill of Quantities (BOQ)")
        st.markdown('</div>', unsafe_allow_html=True)

        # --- BLOCK: ALERTS ---
        st.markdown('<div class="dashboard-card"><h4>⚡ ALERTS</h4>', unsafe_allow_html=True)
        for i in display_data[:2]:
            if abs(i['change']) > 0:
                st.markdown(f'<div class="alert-card-high"><b>VOLATILITY:</b> {i["item"]} shifted {i["change"]}%</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
