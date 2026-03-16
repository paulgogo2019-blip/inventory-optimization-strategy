import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# 1. Setup & Branding
st.set_page_config(page_title="⛏️ GICI Strategic Command", layout="wide")
st.title("⛏️ Gogo Integrated Category Intelligence (GICI)")
st.subheader("Strategic Inventory Command Center | Integrated Category Intelligence")

# 2. Sidebar & Global Parameters
with st.sidebar:
    st.header("⚙️ Strategy Settings")
    service_level_target = st.slider("Target Service Level (%)", 80, 99, 95) / 100
    holding_cost_pct = st.number_input("Annual Holding Cost (%)", value=20) / 100
    st.divider()
    st.success("✅ Analytics Engine: Online")

@st.cache_data
def load_and_enrich_data():
    file_path = 'Demand Forecast.xlsx'
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path, engine='openpyxl')
        
        df.columns = df.columns.str.strip()
        df['ds'] = pd.to_datetime(df['ds'])
        
        # --- ENRICHMENT ENGINE (Simulating metrics not in raw file for strategy) ---
        np.random.seed(42)
        parts = df['Part'].unique()
        part_master = pd.DataFrame({'Part': parts})
        part_master['Lead_Time'] = np.random.randint(5, 45, size=len(parts))
        part_master['Supplier'] = np.random.choice(['Alpha Logistics', 'Beta Global', 'Delta Corp', 'Omega Inc'], size=len(parts))
        part_master['Fill_Rate'] = np.random.uniform(0.70, 0.99, size=len(parts))
        
        df = df.merge(part_master, on='Part', how='left')
        df['Total_Value'] = df['y'] * df['Unit_Cost']
        return df
    except Exception as e:
        st.sidebar.error(f"Error: {e}")
        return None

df = load_and_enrich_data()

if df is not None:
    # --- GLOBAL CALCULATIONS ---
    part_std = df.groupby('Part')['y'].std().fillna(0).reset_index().rename(columns={'y': 'std_dev'})
    part_summary = df.groupby(['Part', 'Category', 'Supplier']).agg({
        'y': 'sum', 'Unit_Cost': 'mean', 'Total_Value': 'sum', 'Lead_Time': 'mean', 'Fill_Rate': 'mean'
    }).reset_index().merge(part_std, on='Part', how='left')
    
    total_portfolio_val = part_summary['Total_Value'].sum()
    avg_fill = part_summary['Fill_Rate'].mean()
    annual_holding_cost = total_portfolio_val * holding_cost_pct
    
    # Calculate Estimated DIO (Days Inventory Outstanding)
    # Estimated Stock = (Lead Time / 30 + Buffer) * Monthly Demand
    part_summary['Est_Stock_Value'] = part_summary['Total_Value'] * (part_summary['Lead_Time'] / 30 + 0.1)
    total_stock_val = part_summary['Est_Stock_Value'].sum()
    avg_dio = (total_stock_val / total_portfolio_val) * 365 if total_portfolio_val > 0 else 0

    # ABC-XYZ Matrix
    part_summary = part_summary.sort_values('Total_Value', ascending=False)
    part_summary['Cum_Value'] = part_summary['Total_Value'].cumsum() / total_portfolio_val
    part_summary['ABC'] = pd.cut(part_summary['Cum_Value'], bins=[0, 0.7, 0.9, 1.0], labels=['A', 'B', 'C'])
    avg_demand_per_part = df.groupby('Part')['y'].mean()
    cv = (part_std.set_index('Part')['std_dev'] / avg_demand_per_part).fillna(0)
    part_summary = part_summary.merge(cv.rename('CV'), on='Part')
    part_summary['XYZ'] = part_summary['CV'].apply(lambda x: 'X' if x < 0.5 else ('Y' if x < 1.0 else 'Z'))

    tabs = st.tabs(["💰 Financials", "🚚 Suppliers", "📦 SOP", "🔍 ABC-XYZ", "🎯 Strategy", "🤖 Advisor", "🧪 Stress-Test", "🌐 Network", "🕵️ Audit", "📄 Monthly Report"])

    # --- TAB 1: FINANCIALS ---
    with tabs[0]:
        st.header("Financial Inventory Health")
        st.write("### 📑 Executive Summary")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Investment", f"${total_portfolio_val:,.0f}")
        m2.metric("Annual Holding Cost", f"${annual_holding_cost:,.0f}")
        m3.metric("Avg Portfolio DIO", f"{avg_dio:.1f} Days")
        
        st.subheader("Category Distribution")
        fig_pie = px.pie(part_summary, values='Total_Value', names='Category', title="Investment Value by Category", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
        
        st.write("### 🔍 Why")
        st.write("To monitor the cost of capital tied up in inventory and identify the largest category drivers of investment.")
        rec1 = "⚠️ High DIO detected. Review procurement cycles to improve cash flow." if avg_dio > 60 else "✅ Healthy DIO: Inventory turnover matches industry benchmarks."
        st.info(f"**🚀 Recommendation:** {rec1}")

    # --- TAB 2: SUPPLIERS ---
    with tabs[1]:
        st.header("Supplier Performance")
        st.write("### 📑 Executive Summary")
        sup_data = part_summary.groupby('Supplier').agg({'Fill_Rate': 'mean', 'Lead_Time': 'mean'}).reset_index()
        
        st.subheader("Supplier Reliability & Lead Time")
        fig_sup = px.bar(sup_data, x='Supplier', y='Lead_Time', color='Fill_Rate', 
                         title="Average Lead Time per Supplier (Colored by Fill Rate)",
                         labels={'Lead_Time': 'Avg Lead Time (Days)'})
        st.plotly_chart(fig_sup, use_container_width=True)
        
        st.write("### 🔍 Why")
        st.write("Benchmarking suppliers to identify who is providing the fastest and most reliable replenishment.")
        slowest = sup_data.sort_values('Lead_Time', ascending=False).iloc[0]
        rec2 = f"Review lead time variability for **{slowest['Supplier']}** ({slowest['Lead_Time']:.1f} days)."
        st.info(f"**🚀 Recommendation:** {rec2}")

    # --- TAB 3: SOP ---
    with tabs[2]:
        st.header("SOP Engine")
        st.write("### 📑 Executive Summary")
        sop_data = part_summary.copy()
        sop_data['Safety_Stock'] = sop_data['std_dev'] * 1.65
        sop_data['ROP'] = (sop_data['y']/30 * sop_data['Lead_Time']) + sop_data['Safety_Stock']
        sop_data['EOQ'] = np.sqrt((2 * sop_data['y'] * 100) / (sop_data['Unit_Cost'] * holding_cost_pct + 0.01))
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            sop_data[['Part', 'y', 'Category', 'Fill_Rate', 'Safety_Stock', 'ROP', 'EOQ', 'Total_Value']].to_excel(writer, index=False)
        st.download_button("📥 Download SOP Plan (Excel)", data=output.getvalue(), file_name="GICI_SOP_Plan.xlsx")
        st.write("### 🔍 Why")
        st.write("Scientific calculation of stock triggers to balance service and cost.")
        st.info("**🚀 Recommendation:** Shift high-velocity 'A' items to a continuous review policy.")

    # --- TAB 4: ABC-XYZ ---
    with tabs[3]:
        st.header("ABC-XYZ Value & Volatility")
        st.write("### 📑 Executive Summary")
        matrix = pd.crosstab(part_summary['ABC'], part_summary['XYZ'])
        st.table(matrix)
        fig_tree = px.treemap(part_summary, path=['ABC', 'XYZ', 'Category'], values='Total_Value', title="Portfolio Matrix")
        st.plotly_chart(fig_tree, use_container_width=True)
        st.write("### 🔍 Why")
        st.write("Strategic segmentation to apply different controls based on value and demand stability.")
        st.success("**🚀 Recommendation:** Apply 'Tight Control' for AX items.")

    # --- TAB 5: STRATEGY ---
    with tabs[4]:
        st.header("Supply Chain Strategy")
        st.write("### 📑 Executive Summary")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Service Level Curve")
            sl_vals = np.linspace(0.8, 0.99, 10)
            inv_vals = [total_portfolio_val * (1 + (i-0.8)*5) for i in sl_vals]
            st.line_chart(pd.DataFrame({'SL': sl_vals, 'Investment': inv_vals}).set_index('SL'))
        with c2:
            st.subheader("Top Dead Stock Risk")
            st.table(part_summary.nsmallest(5, 'y')[['Part', 'Total_Value']])
        st.write("### 🔍 Why")
        st.write("Visualizing the investment needed to achieve higher service levels.")
        st.info("**🚀 Recommendation:** Reallocate capital from dead stock to critical items.")

    # --- TAB 6: ADVISOR ---
    with tabs[5]:
        st.header("Gogo Intelligence Advisor")
        st.write("### 📑 Executive Summary")
        # DYNAMIC LISTING OF ITEMS BELOW TARGET
        below_target = part_summary[part_summary['Fill_Rate'] < service_level_target]
        st.subheader(f"Items Below Target Service Level ({service_level_target*100}%)")
        if not below_target.empty:
            st.dataframe(below_target[['Part', 'Category', 'Fill_Rate', 'Supplier']].sort_values('Fill_Rate'))
        else:
            st.success("🎉 All items are meeting or exceeding the target service level.")
            
        st.write("### 🔍 Why")
        st.write("To identify specific parts failing service targets for immediate management intervention.")
        rec6 = f"Expedite {len(below_target)} parts to avoid stockout risks." if not below_target.empty else "Portfolio health is excellent."
        st.success(f"**🚀 Recommendation:** {rec6}")

    # --- TAB 7: STRESS-TEST ---
    with tabs[6]:
        st.header("Supply Chain Stress-Testing")
        st.write("### 📑 Executive Summary")
        surge = st.select_slider("Simulate Demand Surge (%)", options=[0, 10, 20, 30, 40, 50])
        st.metric("Risk Exposure", f"${total_portfolio_val * (surge/100):,.0f}")
        st.write("### 🔍 Why")
        st.write("Simulating surges to test the financial elasticity of the supply chain.")
        st.info("**🚀 Recommendation:** Increase 'Buffer Stock' for items with high lead times.")

    # --- TAB 8: NETWORK ---
    with tabs[7]:
        st.header("Multi-Echelon Network")
        st.write("### 📑 Executive Summary")
        fig_net = px.sunburst(part_summary, path=['Category', 'Part'], values='Total_Value', title="Network Structure")
        st.plotly_chart(fig_net)
        st.write("### 🔍 Why")
        st.write("Visualizing inventory depth across different network echelons.")
        st.info("**🚀 Recommendation:** Centralize 'C' item safety stocks.")

    # --- TAB 9: AUDIT ---
    with tabs[8]:
        st.header("Inventory Audit & Compliance")
        st.write("### 📑 Executive Summary")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Weekly Tasks")
            st.write("1. Cycle count AX\n2. Verify lead times")
            st.subheader("Monthly Tasks")
            st.write("1. Dead stock audit\n2. Category re-ABC")
        with col2:
            st.metric("Portfolio Health Score", f"{int(avg_fill*100)}/100")
        st.write("### 🔍 Why")
        st.write("Ensuring data integrity through regular governance tasks.")
        st.warning("**🚀 Recommendation:** Perform physical count for Hydraulics category.")

    # --- TAB 10: REPORT ---
    with tabs[9]:
        st.header("Monthly Executive Report")
        st.subheader("💰 Financial Health")
        st.write(f"- **Total Portfolio Value:** ${total_portfolio_val:,.2f}")
        st.write(f"- **Capital Recovery Potential:** ${total_portfolio_val*0.08:,.2f}")
        st.subheader("⚙️ Operational Performance")
        st.write(f"- **Average Fill Rate:** {avg_fill*100:.1f}%")
        st.subheader("🎯 Strategic Directive")
        bullwhip = "UNSTABLE" if (df['y'].var() / df['y'].mean()) > 5 else "STABLE"
        st.write(f"- **Bullwhip Signal:** {bullwhip} | VMI Priority: **HIGH**")
        st.button("📥 Download Monthly Report PDF")

else:
    st.error("Error: Please check 'Demand Forecast.xlsx'.")
