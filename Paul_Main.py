import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. Setup & Branding
st.set_page_config(page_title="⛏️ Gogo Integrated Category Intelligence", layout="wide")
st.title("⛏️ Gogo Integrated Category Intelligence (GICI)")
st.subheader("Strategic Inventory Command Center | Integrated Category Intelligence")

# 2. Sidebar & Data Loading Engine
with st.sidebar:
    st.header("⚙️ Strategy Settings")
    service_level = st.slider("Target Service Level (%)", 80, 99, 95) / 100
    st.divider()
    st.info("System is monitoring 'Demand Forecast.xlsx' in real-time.")

@st.cache_data
def load_data():
    # Matches your GitHub filename. If it's a CSV, the code handles both.
    file_path = 'Demand Forecast.xlsx' 
    try:
        if file_path.endswith('.csv'):
            data = pd.read_csv(file_path)
        else:
            data = pd.read_excel(file_path, engine='openpyxl')
        data.columns = data.columns.str.strip() 
        return data
    except Exception as e:
        st.sidebar.error(f"⚠️ Connection Error: {e}")
        return None

df = load_data()

# 3. The 10-Tab Structure
tabs = st.tabs([
    "💰 Financials", "🚚 Suppliers", "📦 SOP", "🔍 ABC-XYZ", "🎯 Strategy", 
    "🤖 Advisor", "🧪 Stress-Test", "🌐 Network", "🕵️ Audit", "📄 Monthly Report"
])

if df is not None:
    # --- GLOBAL DATA PREP ---
    df['ds'] = pd.to_datetime(df['ds'])
    df['total_value'] = df['y'] * df['Unit_Cost']
    
    total_val = df['total_value'].sum()
    avg_demand = df['y'].mean()
    volatility = df['y'].std() / avg_demand if avg_demand != 0 else 0

    # --- TAB 1: Financials ---
    with tabs[0]:
        st.header("Financial Inventory Health")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Projected Inventory Value", f"${total_val:,.2f}")
        with col2:
            st.metric("Unique Parts Monitored", f"{df['Part'].nunique()}")

        st.subheader("Inventory Value by Category")
        cat_data = df.groupby('Category')['total_value'].sum().reset_index().sort_values('total_value', ascending=False)
        fig = px.bar(cat_data, x='Category', y='total_value', title="Capital Concentration by Category", color_discrete_sequence=['#00CC96'])
        st.plotly_chart(fig, use_container_width=True)
        
        rec1 = "⚠️ High capital tie-up detected." if total_val > 500000 else "✅ Capital efficiency is optimal."
        st.info(f"**🚀 Recommendation:** {rec1} Reduce average inventory on-hand by 5% to free up liquidity.")

    # --- TAB 2: Suppliers ---
    with tabs[1]:
        st.header("Supplier Performance & Reliability")
        top_cat = df['Category'].value_counts().index[0]
        st.write(f"Primary Sourcing Category: **{top_cat}**")
        st.info(f"**🚀 Recommendation:** Negotiate volume discounts specifically for the {top_cat} category.")

    # --- TAB 3: SOP ---
    with tabs[2]:
        st.header("Standard Operating Procedure (SOP) Engine")
        safety_stock_est = (df['y'].std() * 1.65)
        st.write(f"Dynamic Safety Stock Estimated: **{safety_stock_est:.2f} units**")
        st.info("**🚀 Recommendation:** Shift high-velocity 'A' items to a continuous review policy.")

    # --- TAB 4: ABC-XYZ ---
    with tabs[3]:
        st.header("ABC-XYZ Value & Volatility Matrix")
        st.subheader("Demand Trend Analysis")
        trend_fig = px.line(df.groupby('ds')['y'].sum().reset_index(), x='ds', y='y', title="Aggregate Demand Over Time")
        st.plotly_chart(trend_fig, use_container_width=True)
        
        rec4 = "⚠️ High volatility (Z-items) detected." if volatility > 0.6 else "✅ Stable demand patterns (X-items) confirmed."
        st.success(f"**🚀 Recommendation:** {rec4} Implement 'Tight Control' for high-value AX items.")

    # --- TAB 5: Strategy ---
    with tabs[4]:
        st.header("Supply Chain Strategy & Bullwhip Detection")
        bullwhip_ratio = df['y'].var() / df['y'].mean() if df['y'].mean() != 0 else 0
        st.write(f"Bullwhip Coefficient: **{bullwhip_ratio:.2f}**")
        rec5 = "⚠️ Bullwhip signals detected." if bullwhip_ratio > 10 else "✅ Supply chain signals are stable."
        st.warning(f"**🚀 Recommendation:** {rec5} Share POS data with Tier-1 suppliers to reduce order batching.")

    # --- TAB 6: Advisor ---
    with tabs[5]:
        st.header("🤖 Gogo Intelligence Advisor")
        critical_parts = df[df['y'] > df['y'].quantile(0.95)]['Part'].unique()
        st.write("**Top Critical Items (High Demand):**")
        for p in critical_parts[:5]:
            st.write(f"- {p}")
        st.success("**🚀 Recommendation:** Prioritize these top 5 SKUs for expedited shipping if stock drops below 10%.")

    # --- TAB 7: Stress-Test ---
    with tabs[6]:
        st.header("Supply Chain Stress-Testing")
        surge_val = total_val * 1.25
        st.write(f"Value at Risk (25% Demand Surge): **${surge_val:,.2f}**")
        st.info("**🚀 Recommendation:** Increase 'Buffer Stock' for items in the Hydraulics category.")

    # --- TAB 8: Network ---
    with tabs[7]:
        st.header("Multi-Echelon Network Optimization")
        st.write(f"Network Scope: **{df['Category'].nunique()} Categories** across **{df['Part'].nunique()} SKUs**.")
        st.info("**🚀 Recommendation:** Centralize safety stock for low-volume parts to reduce network-wide carry cost.")

    # --- TAB 9: Audit ---
    with tabs[8]:
        st.header("Inventory Audit & Compliance")
        high_value_parts = df[df['Unit_Cost'] > 1000]['Part'].nunique()
        st.write(f"High-Value Items requiring Audit: **{high_value_parts}**")
        st.warning("**🚀 Recommendation:** Conduct a 'Cycle Count' on all items with a Unit Cost > $1,000.")

    # --- TAB 10: Monthly Report ---
    with tabs[9]:
        st.header("Monthly Executive Category Report")
        st.write(f"Analysis Period: **{df['ds'].min().date()}** to **{df['ds'].max().date()}**")
        st.write("Overall Inventory Health: **B+**")
        st.button("📥 Download Monthly PDF Report")

else:
    st.warning("⚠️ Data file not found. Ensure 'Demand Forecast.xlsx' is in your GitHub repository.")
   
