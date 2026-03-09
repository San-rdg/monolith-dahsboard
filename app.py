import pandas as pd
import streamlit as st
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="MONOLITH | INTELLIGENCE GRID", page_icon="🏗️", layout="wide")
st_autorefresh(interval=30000, key="datarefresh") # Refreshes every 30 seconds

# --- 2. PREMIUM STYLING (CSS) ---
st.markdown("""
    <style>
    /* Global App Background */
    .stApp {background-color: #0d1117;}
    
    /* Sleek Dashboard Cards */
    .dashboard-card {
        background-color: #161b22; 
        border: 1px solid #30363d; 
        border-radius: 12px; 
        padding: 24px; 
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: border-color 0.3s ease;
    }
    .dashboard-card:hover {
        border-color: #58a6ff;
    }
    
    /* Headers & Text */
    h1 {font-size: 36px; font-weight: 900; color: #ffffff; letter-spacing: 1px;}
    .card-header {color: #58a6ff; font-weight: 700; font-size: 1.2rem; margin-bottom: 15px; border-bottom: 1px solid #30363d; padding-bottom: 10px;}
    
    /* Live Feed Rows */
    .feed-row {display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #21262d;}
    .feed-row:last-child {border-bottom: none;}
    .feed-item-name {color: #e6edf3; font-size: 1.1rem; font-weight: 600;}
    .feed-price {color: #ffffff; font-family: 'Courier New', Courier, monospace; font-weight: 700; font-size: 1.25rem;}
    
    /* Estimator Highlight */
    .total-display {
        background: linear-gradient(145deg, #1f242c, #161b22);
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        margin-top: 20px;
    }
    .total-label {color: #8b949e; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px;}
    .total-value {color: #3fb950; font-size: 2.5rem; font-weight: 800; font-family: 'Courier New', Courier, monospace;}
    
    /* Blinking Live Dot */
    .live-indicator {color: #ff7b72; animation: blinker 1.5s linear infinite;}
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
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, "price_history.csv")
    
    if not os.path.exists(file_path): return []

    try:
        df = pd.read_csv(file_path)
        df.columns = [c.strip().lower() for c in df.columns]
        
        # Safely parse timestamps, dropping invalid rows
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])

        latest_items = []
        for item_name in df['item'].unique():
            item_history = df[df['item'] == item_name].sort_values('timestamp')
            if item_history.empty: continue
                
            latest_row = item_history.iloc[-1]
            
            try:
                # Clean and extract price
                current_price = float(str(latest_row['price']).replace(',', '').strip())
                
                # Calculate percent change
                change_pct = 0.0
                if len(item_history) > 1:
                    prev_price = float(str(item_history.iloc[-2]['price']).replace(',', '').strip())
                    if prev_price != 0:
                        change_pct = ((current_price - prev_price) / prev_price) * 100
                
                latest_items.append({
                    "item": item_name, 
                    "price": current_price, 
                    "change": round(change_pct, 2), 
                    "source": latest_row.get('source', 'Market'),
                    "category": get_category(item_name)
                })
            except Exception:
                continue 
                
        return latest_items
    except Exception as e:
        st.sidebar.error(f"System Alert: {e}")
        return []

# --- 4. MAIN UI ---
st.markdown("<h1><span class='live-indicator'>●</span> MONOLITH COMMAND CENTER</h1>", unsafe_allow_html=True)

raw_data = fetch_live_market_data()

if not raw_data:
    st.warning("⚠️ Neural Engine offline. Awaiting data sync from GitHub Actions...")
else:
    # Top Row: Quick Metrics
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    m1.metric("Items Actively Tracked", len(raw_data))
    
    # Calculate average market movement
    avg_change = sum(item['change'] for item in raw_data) / len(raw_data) if raw_data else 0
    m2.metric("Avg Market Movement", f"{avg_change:+.2f}%")
    m3.metric("Data Engine Status", "Online & Syncing", "Nominal")
    st.markdown('</div>', unsafe_allow_html=True)

    # Main Split Layout
    col_feed, col_tools = st.columns([1.5, 1])
    
    # LEFT COLUMN: Live Feed
    with col_feed:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-header">📡 LIVE MARKET FEED</div>', unsafe_allow_html=True)
        
        for item in raw_data:
            arrow = "▲" if item['change'] > 0 else "▼" if item['change'] < 0 else "—"
            color = "#3fb950" if item['change'] > 0 else "#f85149" if item['change'] < 0 else "#8b949e"
            
            st.markdown(f"""
                <div class="feed-row">
                    <div>
                        <div class="feed-item-name">📦 {item['item']}</div>
                        <div style="color:#8b949e; font-size: 0.85rem; margin-top: 4px;">Source: {item['source']}</div>
                    </div>
                    <div style="text-align:right;">
                        <div class="feed-price">Rs. {item['price']:,.2f}</div>
                        <div style="color:{color}; font-size:0.9rem; font-weight:bold; margin-top: 4px;">{arrow} {abs(item['change'])}%</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # RIGHT COLUMN: Estimator
    with col_tools:
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-header">🧮 DYNAMIC ESTIMATOR</div>', unsafe_allow_html=True)
        st.write("Calculate real-time project costs based on current market rates.")
        
        # Extract item names for the dropdown
        item_names = [i['item'] for i in raw_data]
        selected_material = st.selectbox("Select Material", item_names)
        
        # Find the selected item's data
        selected_data = next(i for i in raw_data if i['item'] == selected_material)
        current_price = selected_data['price']
        
        # Quantity Input
        quantity = st.number_input(f"Quantity (Units)", min_value=1.0, value=100.0, step=10.0)
        
        # The Math
        total_cost = current_price * quantity
        
        # Beautiful Total Display
        st.markdown(f"""
            <div class="total-display">
                <div class="total-label">Estimated Total Cost</div>
                <div class="total-value">Rs. {total_cost:,.2f}</div>
                <div style="color: #8b949e; font-size: 0.8rem; margin-top: 10px;">
                    Based on live unit rate: Rs. {current_price:,.2f}
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
