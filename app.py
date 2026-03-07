import pandas as pd
import streamlit as st
import numpy as np
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="MONOLITH | INTELLIGENCE GRID", page_icon="🏗️", layout="wide")
st_autorefresh(interval=30000, key="datarefresh")

# --- 2. STYLING ---
st.markdown("""
    <style>
    .stApp {background-color: #0E1117;}
    .dashboard-card {background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 20px; margin-bottom: 15px;}
    h1 {font-size: 32px; font-weight: 800; color: #FFFFFF;}
    .feed-row {display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #21262D;}
    .feed-price {color: #FFFFFF; font-family: 'Roboto Mono', monospace; font-weight: 600;}
    .live-indicator {color: #FF4B4B; animation: blinker 1.5s linear infinite;}
    @keyframes blinker { 50% { opacity: 0; } }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA UTILITIES ---
def get_category(item_name):
    name = item_name.lower()
    if any(x in name for x in ['steel', 'tmt', 'iron']): return "Steel"
    if 'cement' in name: return "Cement"
    if any(x in name for x in ['sand', 'metal', 'brick', 'block']): return "Aggregates"
    return "Others"

def fetch_live_market_data():
    # This finds the EXACT folder where your app is running
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "price_history.csv")
    
    if os.path.exists(file_path):
        try:
            # Force pandas to re-read the file without using old cache
            df = pd.read_csv(file_path).drop_duplicates()
            if df.empty: return []
            
            # ... (rest of your existing logic)
            latest_items = []
            for item_name in df['item'].unique():
                item_history = df[df['item'] == item_name].sort_values('timestamp')
                latest_row = item_history.iloc[-1]
                current_price = float(latest_row['price'])
                change_pct = 0.0
                if len(item_history) > 1:
                    prev_price = float(item_history.iloc[-2]['price'])
                    if prev_price != 0:
                        change_pct = ((current_price - prev_price) / prev_price) * 100
                latest_items.append({
                    "item": item_name, "price": current_price, 
                    "change": round(change_pct, 2), "source": latest_row.get('source', 'Market'),
                    "category": get_category(item_name)
                })
            return latest_items
        except:
            return []
    return []

# --- 4. UI LOGIC ---
st.markdown("<h1><span class='live-indicator'>●</span> MARKET INTELLIGENCE GRID</h1>", unsafe_allow_html=True)

raw_data = fetch_live_market_data()

if not raw_data:
    st.warning("⚠️ No data detected in price_history.csv. Run scraper or upload data to GitHub.")
else:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="dashboard-card"><h4>LIVE PRICE FEED</h4>', unsafe_allow_html=True)
        for item in raw_data:
            color = "#2EA043" if item['change'] >= 0 else "#DA3633"
            st.markdown(f"""
                <div class="feed-row">
                    <div style="color:#C9D1D9;">📦 <b>{item['item']}</b> <br><small>{item['source']}</small></div>
                    <div style="text-align:right;">
                        <div class="feed-price">Rs. {item['price']:,}</div>
                        <div style="color:{color}; font-size:12px;">{item['change']}%</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="dashboard-card"><h4>📊 ANALYTICS</h4>', unsafe_allow_html=True)
        if len(raw_data) > 0:
            st.metric("Total Tracked Items", len(raw_data))
            st.info("Neural Engine active. Data syncing with GitHub Actions.")
        st.markdown('</div>', unsafe_allow_html=True)

