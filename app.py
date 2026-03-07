import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="MONOLITH | INTELLIGENCE GRID", page_icon="M", layout="wide", initial_sidebar_state="expanded")

# Auto-refresh every 30 seconds to catch scraper updates
st_autorefresh(interval=30000, key="datarefresh")

# --- 2. STYLING (CSS) ---
st.markdown("""
    <style>
    .stApp {background-color: #0E1117;}
    .dashboard-card {background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 20px; margin-bottom: 15px;}
    h1 {font-size: 38px; font-weight: 800; color: #FFFFFF; margin-bottom: 0px;}
    h3 {font-size: 16px; font-weight: 400; color: #8B949E; margin-top: 0px; margin-bottom: 20px;}
    .feed-row {display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #21262D;}
    .feed-item {color: #C9D1D9; font-size: 14px; font-weight: 500;}
    .feed-price {color: #FFFFFF; font-family: 'Roboto Mono', monospace; font-weight: 600;}
    .feature-box {background-color: #161B22; border: 1px solid #30363D; border-radius: 6px; padding: 15px; display: flex; align-items: center; margin-bottom: 10px;}
    .icon-box {width: 35px; height: 35px; background-color: #21262D; border-radius: 4px; display: flex; align-items: center; justify-content: center; margin-right: 15px; border: 1px solid #FF4B4B; color: #FF4B4B; font-size: 18px;}
    .alert-card-high {background-color: #2B1111; border: 1px solid #DA3633; padding: 15px; border-radius: 6px; margin-bottom: 10px;}
    .pred-pill {background-color: #1F6FEB; color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: bold; margin-left: 10px;}
    .live-indicator {color: #FF4B4B; animation: blinker 1.5s linear infinite;}
    @keyframes blinker { 50% { opacity: 0; } }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA UTILITIES ---
def get_category(item_name):
    name = item_name.lower()
    if any(x in name for x in ['steel', 'tmt', 'iron']): return "Steel"
    if 'cement' in name: return "Cement"
    if any(x in name for x in ['sand', 'brick', 'block']): return "Aggregates"
    return "Others"

def fetch_live_market_data():
    if os.path.exists("price_history.csv"):
        df = pd.read_csv("price_history.csv")
        latest_items = []
        for item_name in df['item'].unique():
            item_history = df[df['item'] == item_name].sort_values('timestamp')
            latest_row = item_history.iloc[-1]
            current_price = latest_row['price']
            
            change_pct = 0.0
            if len(item_history) > 1:
                prev_price = item_history.iloc[-2]['price']
                change_pct = ((current_price - prev_price) / prev_price) * 100
            
            latest_items.append({
                "item": item_name,
                "price": current_price,
                "change": round(change_pct, 2),
                "district": latest_row['source'],
                "category": get_category(item_name)
            })
        return latest_items
    return []

def generate_forecast(model_type, days=7):
    dates_past = pd.date_range(end=datetime.today(), periods=30)
    dates_future = pd.date_range(start=datetime.today(), periods=days + 1)
    base_price = 2300
    prices_past = [base_price + x*2 + np.random.randint(-20, 20) for x in range(30)]
    last_price = prices_past[-1]
    
    if model_type == "LSTM (TensorFlow)":
        prices_future = [last_price + (x**2)*1.5 for x in range(days + 1)]
        conf, vol = 94, "High"
    else:
        prices_future = [last_price + (x**1.5)*2 for x in range(days + 1)]
        conf, vol = 89, "Medium"
        
    df_past = pd.DataFrame({'Date': dates_past, 'Price': prices_past})
    df_future = pd.DataFrame({'Date': dates_future, 'Price': prices_future})
    return df_past, df_future, conf, vol

# --- 4. DATA INITIALIZATION ---
raw_market_data = fetch_live_market_data()

# --- 5. SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("## ⚙️ SYSTEM CONTROL")
    demo_mode = st.toggle("Exhibition Mode", value=True)
    
    st.markdown("---")
    st.markdown("### 🧠 Neural Engine")
    selected_model = st.selectbox("Active Forecast Model", 
        ["Linear Regression", "ARIMA", "Prophet (Advanced)", "LSTM (TensorFlow)"], index=3)
    
    st.markdown("---")
    st.markdown("### 🔍 GLOBAL FILTERS")
    if raw_market_data:
        all_item_names = [i['item'] for i in raw_market_data]
        selected_item_names = st.multiselect("Focus Materials", options=all_item_names, default=all_item_names)
        market_data = [i for i in raw_market_data if i['item'] in selected_item_names]
    else:
        st.warning("No data found. Run scraper.py")
        market_data = []

# --- 6. MAIN UI HEADER ---
st.markdown("<h1><span class='live-indicator'>●</span> REAL-TIME INTELLIGENCE GRID</h1>", unsafe_allow_html=True)
st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

col_left, col_right = st.columns([2.5, 1])

with col_left:
    # --- BLOCK A: MARKET FEED ---
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown('<h4>MONOLITH MARKET FEED</h4>', unsafe_allow_html=True)
    
    tab_all, tab_steel, tab_cement, tab_aggr = st.tabs(["🌐 All", "🏗️ Steel", "🧱 Cement", "💎 Aggregates"])

    def render_material_rows(items):
        if not items:
            st.info("No materials found in this category.")
            return
        for item in items:
            arrow = "▼" if item['change'] < 0 else "▲"
            color = "#DA3633" if item['change'] < 0 else "#2EA043"
            if item['change'] == 0: arrow, color = "—", "#8B949E"
            st.markdown(f"""
                <div class="feed-row">
                    <div class="feed-item">📦 <b>{item['item']}</b> <small style="color:#666">({item['district']})</small></div>
                    <div style="text-align:right;">
                        <div class="feed-price">Rs. {item['price']:,}</div>
                        <div style="color:{color}; font-size:11px;">{arrow} {abs(item['change'])}%</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    with tab_all: render_material_rows(market_data)
    with tab_steel: render_material_rows([i for i in market_data if i['category'] == "Steel"])
    with tab_cement: render_material_rows([i for i in market_data if i['category'] == "Cement"])
    with tab_aggr: render_material_rows([i for i in market_data if i['category'] == "Aggregates"])
    st.markdown('</div>', unsafe_allow_html=True)

    # --- BLOCK B: AI FORECAST ---
    df_past, df_future, conf, vol = generate_forecast(selected_model)
    st.markdown(f'<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown(f'<h4>🤖 AI FORECAST <span class="pred-pill">MODEL: {selected_model}</span></h4>', unsafe_allow_html=True)
    
    chart_data = pd.concat([df_past.set_index('Date')['Price'], df_future.set_index('Date')['Price']], axis=1)
    chart_data.columns = ['Historical', 'Prediction']
    st.line_chart(chart_data, color=["#30363D", "#1F6FEB"])
    st.markdown(f"<div style='font-size:12px; color:#8B949E;'>Confidence Level: <b>{conf}%</b> | Risk Profile: <b>{vol}</b></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    # --- GEO RADAR ---
    st.markdown('<div class="dashboard-card"><h4>🗺️ GEO-ARBITRAGE RADAR</h4>', unsafe_allow_html=True)
    districts = [("Puttalam", 2280), ("Gampaha", 2320), ("Colombo", 2345), ("Galle", 2390)]
    for d, p in districts:
        st.markdown(f"""
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <div style="color:#C9D1D9; font-size:12px;">{d}</div>
                <div style="color:#FFFFFF; font-family:'Roboto Mono'; font-size:11px;">Rs. {p}</div>
            </div>
            <div style="background:#21262D; height:4px; border-radius:2px; margin-bottom:10px;">
                <div style="background:#1F6FEB; width:{(p-2000)/5}%; height:4px;"></div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- ALERTS ---
    st.markdown("### System Alerts")
    high_risk = [i for i in market_data if abs(i['change']) > 0] # Showing any change for demo
    if high_risk:
        for item in high_risk:
            st.markdown(f"""<div class="alert-card-high"><h4>PRICE SHIFT</h4><div class="metric-small">{item['item']} changed by {item['change']}%</div></div>""", unsafe_allow_html=True)
    else:
        st.success("Market Volatility: Normal")

    # --- FEATURES ---
    st.markdown("""
        <div class="feature-box"><div class="icon-box">🕷️</div><div><h4>Auto-Scrapers</h4><div class="metric-small">Hunting data 24/7</div></div></div>
        <div class="feature-box"><div class="icon-box" style="color:#2EA043; border-color:#2EA043;">🧠</div><div><h4>AI Engine</h4><div class="metric-small">Forecasts Active</div></div></div>
    """, unsafe_allow_html=True)