import pandas as pd
import streamlit as st
import numpy as np
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="MONOLITH | INTELLIGENCE GRID", page_icon="🏗️", layout="wide")
st_autorefresh(interval=30000, key="datarefresh")

# --- 2. STYLING (CSS) ---
st.markdown("""
    <style>
    .stApp {background-color: #0E1117;}
    .dashboard-card {background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 20px; margin-bottom: 15px;}
    h1 {font-size: 32px; font-weight: 800; color: #FFFFFF;}
    .feed-row {display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #21262D;}
    .feed-price {color: #FFFFFF; font-family: 'Roboto Mono', monospace; font-weight: 600; font-size: 1.1em;}
    .live-indicator {color: #FF4B4B; animation: blinker 1.5s linear infinite;}
    @keyframes blinker { 50% { opacity: 0; } }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATA UTILITIES ---
def get_category(item_name):
    name = str(item_name).lower()
    if any(x in name for x in ['steel', 'tmt', 'iron']): return "Steel"
    if 'cement' in name: return "Cement"
    if any(x in name for x in ['sand', 'metal', 'brick', 'block']): return "Aggregates"
    return "Others"

def fetch_live_market_data():
    # Use absolute path to ensure Streamlit Cloud finds the file
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, "price_history.csv")
    
    # Sidebar Debug (Only shows if file is missing)
    if not os.path.exists(file_path):
        st.sidebar.error(f"Missing: {file_path}")
        return []

    try:
        # Load and clean headers
        df = pd.read_csv(file_path)
        df.columns = [c.strip().lower() for c in df.columns]
        
        # Ensure timestamp is datetime for correct sorting
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        latest_items = []
        for item_name in df['item'].unique():
            # Get history for this item
            item_history = df[df['item'] == item_name].sort_values('timestamp')
            latest_row = item_history.iloc[-1]
            
            # Clean Price Conversion
            try:
                raw_price = str(latest_row['price']).replace(',', '').strip()
                current_price = float(raw_price)
            except:
                continue 

            # Calculate Price Change if possible
            change_pct = 0.0
            if len(item_history) > 1:
                try:
                    prev_price = float(str(item_history.iloc[-2]['price']).replace(',', '').strip())
                    if prev_price != 0:
                        change_pct = ((current_price - prev_price) / prev_price) * 100
                except:
                    pass

            latest_items.append({
                "item": item_name, 
                "price": current_price, 
                "change": round(change_pct, 2), 
                "source": latest_row.get('source', 'Market'),
                "category": get_category(item_name)
            })
        return latest_items
    except Exception as e:
        st.sidebar.warning(f"Data Read Error: {e}")
        return []

# --- 4. MAIN UI ---
st.markdown("<h1><span class='live-indicator'>●</span> MARKET INTELLIGENCE GRID</h1>", unsafe_allow_html=True)

raw_data = fetch_live_market_data()

if not raw_data:
    st.warning("⚠️ Waiting for data sync... Ensure price_history.csv is pushed to GitHub.")
    # Show debug info to the user
    if st.checkbox("Show System Debug"):
        st.write("Files in directory:", os.listdir("."))
else:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="dashboard-card"><h4>LIVE PRICE FEED</h4>', unsafe_allow_html=True)
        for item in raw_data:
            # Dynamic styling based on price movement
            arrow = "▲" if item['change'] > 0 else "▼" if item['change'] < 0 else "—"
            color = "#2EA043" if item['change'] > 0 else "#DA3633" if item['change'] < 0 else "#8B949E"
            
            st.markdown(f"""
                <div class="feed-row">
                    <div style="color:#C9D1D9;">📦 <b>{item['item']}</b> <br><small>{item['source']}</small></div>
                    <div style="text-align:right;">
                        <div class="feed-price">Rs. {item['price']:,}</div>
                        <div style="color:{color}; font-size:12px; font-weight:bold;">{arrow} {abs(item['change'])}%</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="dashboard-card"><h4>📊 ANALYTICS</h4>', unsafe_allow_html=True)
        st.metric("Total Tracked Items", len(raw_data))
        st.write("---")
        st.info("💡 **Tip:** Data updates automatically every 24 hours via GitHub Actions.")
        
        # Download button for professional feel
        csv_download = pd.DataFrame(raw_data).to_csv(index=False)
        st.download_button("📩 Export Market Report", csv_download, "market_report.csv", "text/csv")
        st.markdown('</div>', unsafe_allow_html=True)