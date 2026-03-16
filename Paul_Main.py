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
        
        # --- ENRICHMENT ENGINE ---
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
    # --- CALCULATIONS ---
    part_std = df.groupby('Part')['y'].std().fillna(0).reset_index().rename(columns={'y': 'std_dev'})
    
    part_summary = df.groupby(['Part', 'Category', 'Supplier']).agg({
        'y': 'sum',
        'Unit_Cost': 'mean',
        'Total_Value': 'sum',
        'Lead_Time': 'mean',
        'Fill_Rate': 'mean'
    }).reset_index()
    
    part_summary = part_summary.merge(part_std, on='Part', how='left')
    total_portfolio_val = part_summary['Total_Value'].sum()
    avg_fill = part_summary['Fill_Rate'].mean()

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
        st.write(f"Portfolio Value: **${total_portfolio_val:,.2f}** | Avg Fill Rate: **{avg_fill*100:.1f}%**")
        fig1 = px.scatter(part_summary, x='Lead_Time', y='Fill_Rate', color='Category', size='Total_Value', title="Fill Rate vs. Average Lead Time")
        st.plotly_chart(fig1, use_container_width=True)
        st.write("### 🔍 Why")
        st.write("Analyzing service levels against supply speed to identify bottleneck parts.")
        rec1 = "⚠️ Urgent: Low service level. Prioritize 'A' items." if avg_fill < 0.9 else "✅ Optimal: Targets met."
        st.info(f"**🚀 Recommendation:** {rec1}")

    # --- TAB 2: SUPPLIERS ---
    with tabs[1]:
        st.header("Supplier Performance")
        st.write("### 📑 Executive Summary")
        sup_perf = part_summary.groupby('Supplier')['Fill_Rate'].mean().reset_index()
        fig2 = px.bar(sup_perf, x='Supplier', y='Fill_Rate', title="Avg Fill Rate by Supplier")
        st.plotly_chart(fig2, use_container_width=True)
        st.write("### 🔍 Why")
        st.write("Identify which partners are currently impacting your service level targets.")
        rec2 = f"Review contracts for suppliers below {service_level_target*100}%."
        st.info(f"**🚀 Recommendation:** {rec2}")

    # --- TAB 3: SOP ---
    with tabs[2]:
        st.header("SOP Engine")
        st.write("### 📑 Executive Summary")
        sop_data = part_summary.copy()
        sop_data['Safety_Stock'] = sop_data['std_dev'] * 1.65
        sop_data['ROP'] = (sop_data['y']/30 * sop_data['Lead_Time']) + sop_data['Safety_Stock']
        sop_data['EOQ'] = np.sqrt((2 * sop_data['y'] * 100) / (sop_data['Unit_Cost'] * holding_cost_pct + 0.01))
        sop_data['Holding_Cost'] = sop_data['Total_Value'] * holding_cost_pct
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            sop_data[['Part', 'y', 'Category', 'Fill_Rate', 'Safety_Stock', 'ROP', 'EOQ', 'Holding_Cost', 'Total_Value']].to_excel(writer, index=False)
        st.download_button("📥 Download SOP Plan (Excel)", data=output.getvalue(), file_name="GICI_SOP_Plan.xlsx")
        
        st.write("### 🔍 Why")
        st.write("Scientific sizing of stock buffers reduces excess while preventing stockouts.")
        rec3 = "⚠️ High Buffers: Safety stock levels are elevated." if sop_data['Safety_Stock'].mean() > 50 else "✅ Lean: Safety stock is optimized."
        st.info(f"**🚀 Recommendation:** {rec3}")

    # --- TAB 4: ABC-XYZ ---
    with tabs[3]:
        st.header("ABC-XYZ Value & Volatility")
        st.write("### 📑 Executive Summary")
        matrix = pd.crosstab(part_summary['ABC'], part_summary['XYZ'])
        st.table(matrix)
        fig_tree = px.treemap(part_summary, path=['ABC', 'XYZ', 'Category'], values='Total_Value', title="Portfolio Matrix")
        st.plotly_chart(fig_tree, use_container_width=True)
        st.write("### 🔍 Why")
        st.write("Differentiation of parts for specific management tactics.")
        rec4 = "⚠️ Action: Review high-value Z items." if not part_summary[(part_summary['ABC']=='A') & (part_summary['XYZ']=='Z')].empty else "✅ Smooth Portfolio patterns."
        st.success(f"**🚀 Recommendation:** {rec4}")

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
        
        st.subheader("Critical Items Table")
        st.dataframe(part_summary.nlargest(5, 'Total_Value')[['Part', 'y', 'Supplier', 'Total_Value']])
        st.write("### 🔍 Why")
        st.write("Visualization of the trade-off between customer service and financial investment.")
        st.info("**🚀 Recommendation:** Reallocate capital from dead stock to critical items.")

    # --- TAB 6: ADVISOR ---
    with tabs[5]:
        st.header("Gogo Intelligence Advisor")
        st.write("### 📑 Executive Summary")
        risky = part_summary[part_summary['Fill_Rate'] < service_level_target]
        st.write(f"Detected **{len(risky)}** items failing service level targets.")
        st.write("### 🔍 Why")
        st.write("Prioritization engine for management intervention.")
        st.success("**🚀 Recommendation:** Expedite 'A' category parts with low fill rates.")

    # --- TAB 7: STRESS-TEST ---
    with tabs[6]:
        st.header("Supply Chain Stress-Testing")
        st.write("### 📑 Executive Summary")
        surge = st.select_slider("Simulate Demand Surge (%)", options=[0, 10, 20, 30, 40, 50])
        st.metric("Risk Exposure", f"${total_portfolio_val * (surge/100):,.0f}")
        st.write("### 🔍 Why")
        st.write("Stress-testing helps plan for business continuity during surges.")
        rec7 = "🔴 High Risk: Surge capacity is low." if surge > 20 else "🟢 Resilient: Portfolio can handle surge."
        st.info(f"**🚀 Recommendation:** {rec7}")

    # --- TAB 8: NETWORK ---
    with tabs[7]:
        st.header("Multi-Echelon Network")
        st.write("### 📑 Executive Summary")
        fig_net = px.sunburst(part_summary, path=['Category', 'Part'], values='Total_Value', title="Network Structure")
        st.plotly_chart(fig_net)
        st.write("### 🔍 Why")
        st.write("Visualization of inventory depth across different echelons.")
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
            st.write("1. Dead stock audit\n2. ABC re-classification")
        with col2:
            st.metric("Portfolio Health Score", f"{int(avg_fill*100)}/100")
        st.write("### 🔍 Why")
        st.write("Standardized maintenance for high data integrity.")
        st.warning("**🚀 Recommendation:** Physical audit needed for high-value Hydraulics.")

    # --- TAB 10: REPORT ---
    with tabs[9]:
        st.header("Monthly Executive Report")
        st.subheader("💰 Financial Health")
        st.write(f"- **Total Portfolio Value:** ${total_portfolio_val:,.2f}")
        # FIXED: Variable name updated from total_val to total_portfolio_val
        st.write(f"- **Capital Recovery Potential:** ${total_portfolio_val*0.08:,.2f} (Dead Stock)")
        
        st.subheader("⚙️ Operational Performance")
        st.write(f"- **Average Fill Rate:** {avg_fill*100:.1f}%")
        st.write(f"- **Underperforming Category:** {part_summary.groupby('Category')['Fill_Rate'].mean().idxmin()}")
        
        st.subheader("🎯 Strategic Directive")
        bullwhip = "UNSTABLE" if (df['y'].var() / df['y'].mean()) > 5 else "STABLE"
        st.write(f"- **Bullwhip Signal:** {bullwhip}")
        st.write("- **VMI Priority:** HIGH (Tier 1)")
        st.button("📥 Download Monthly PDF")

else:
    st.error("Error: Please check 'Demand Forecast.xlsx'.")
   
