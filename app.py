import pandas as pd
import streamlit as st
import numpy as np
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="MONOLITH | INTELLIGENCE GRID", page_icon="🏗️", layout="wide", initial_sidebar_state="expanded")

# Auto-refresh every 30 seconds
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

# --- 3. DATA UTILITIES ---
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
        # Force refresh data from CSV
        df = pd.read_csv("price_history.csv")
        if df.empty: return []
        
        latest_items = []
        for item_name in df['item'].unique():
            item_history = df[df['item'] == item_name].sort_values('timestamp')
            latest_row = item_history.iloc[-1]
            current_price = latest_row['price']
            
            # --- SAFETY CHECK FOR PRICE CHANGE ---
            change_pct = 0.0
            if len(item_history) > 1:
                prev_price = item_history.iloc[-2]['price']
                if prev_price and prev_price != 0:
                    change_pct = ((current_price - prev_price) / prev_price) * 100
            
            latest_items.append({
                "item": item_name,
                "price": current_price,
                "change": round(change_pct, 2),
                "source": latest_row['source'],
                "category": get_category(item_name)
            })
        return latest_items
    return []

# --- 4. DATA INITIALIZATION ---
raw_market_data = fetch_live_market_data()

# --- 5. SIDEBAR CONTROLS ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3630/3630321.png", width=100)
    st.markdown("## MONOLITH v2.0")
    
    st.markdown("### 🧠 Forecasting")
    selected_model = st.selectbox("Active Model", ["Prophet", "LSTM (Deep Learning)", "ARIMA"], index=1)
    
    st.markdown("---")
    st.markdown("### 🔍 Category Filters")
    categories = ["All", "Steel", "Cement", "Aggregates", "Timber", "MEP & Finishes"]
    selected_cat = st.radio("Focus View", categories)

# --- 6. MAIN UI ---
st.markdown("<h1><span class='live-indicator'>●</span> MARKET INTELLIGENCE GRID</h1>", unsafe_allow_html=True)

if not raw_market_data:
    st.error("No data found in price_history.csv. Run your scraper first!")
else:
    # Filter data based on category
    if selected_cat == "All":
        display_data = raw_market_data
    else:
        display_data = [i for i in raw_market_data if i['category'] == selected_cat]

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f'<div class="dashboard-card"><h4>LIVE PRICE FEED: {selected_cat.upper()}</h4>', unsafe_allow_html=True)
        
        # Display as a clean list
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

    with col2:
        # --- TOP MOVERS ---
        st.markdown('<div class="dashboard-card"><h4>⚡ MARKET ALERTS</h4>', unsafe_allow_html=True)
        movers = sorted(raw_market_data, key=lambda x: abs(x['change']), reverse=True)[:3]
        for m in movers:
            if m['change'] != 0:
                st.markdown(f"""
                    <div class="alert-card-high">
                        <small>SHARP VOLATILITY</small><br>
                        <b>{m['item']}</b> moved {m['change']}%
                    </div>
                """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- EXPORT TOOL ---
        st.markdown('<div class="dashboard-card"><h4>💾 DATA EXPORT</h4>', unsafe_allow_html=True)
        st.download_button("Download Market Report (CSV)", 
                           pd.DataFrame(raw_market_data).to_csv(index=False), 
                           "market_report.csv", "text/csv")
        st.markdown('</div>', unsafe_allow_html=True)

