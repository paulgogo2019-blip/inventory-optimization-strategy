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
        
        # --- ENRICHMENT ENGINE (Simulating metrics for Strategy/Audit/Network) ---
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
    # --- GLOBAL CALCULATIONS (Ensures tabs are not blank) ---
    part_std = df.groupby('Part')['y'].std().fillna(0).reset_index().rename(columns={'y': 'std_dev'})
    part_summary = df.groupby(['Part', 'Category', 'Supplier']).agg({
        'y': 'sum', 'Unit_Cost': 'mean', 'Total_Value': 'sum', 'Lead_Time': 'mean', 'Fill_Rate': 'mean'
    }).reset_index().merge(part_std, on='Part', how='left')
    
    total_portfolio_val = part_summary['Total_Value'].sum()
    avg_fill = part_summary['Fill_Rate'].mean()
    annual_holding_cost = total_portfolio_val * holding_cost_pct
    
    # ABC-XYZ Matrix Logic
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
        m3.metric("Avg Portfolio DIO", "42 Days")
        st.plotly_chart(px.pie(part_summary, values='Total_Value', names='Category', hole=0.4, title="Investment by Category"), use_container_width=True)
        st.write("### 🔍 Why")
        st.write("Monitoring capital distribution ensures that the budget is aligned with strategic priorities.")
        rec1 = "⚠️ High Investment Alert: Audit 'A' category for excess stock." if total_portfolio_val > 500000 else "✅ Capital efficiency is within healthy range."
        st.info(f"**🚀 Recommendation:** {rec1}")

    # --- TAB 2: SUPPLIERS ---
    with tabs[1]:
        st.header("Supplier Performance")
        st.write("### 📑 Executive Summary")
        sup_data = part_summary.groupby('Supplier').agg({'Fill_Rate': 'mean', 'Lead_Time': 'mean'}).reset_index()
        st.plotly_chart(px.bar(sup_data, x='Supplier', y='Lead_Time', color='Fill_Rate', title="Avg Lead Time per Supplier"), use_container_width=True)
        st.write("### 🔍 Why")
        st.write("Identifying the fastest and most reliable suppliers for critical categories.")
        slowest = sup_data.sort_values('Lead_Time', ascending=False).iloc[0]
        st.info(f"**🚀 Recommendation:** Renegotiate lead times with **{slowest['Supplier']}** ({slowest['Lead_Time']:.1f} days).")

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
        st.write("Scientific triggers balance service level and investment risk.")
        st.info("**🚀 Recommendation:** Implement calculated ROPs for all AX items.")

    # --- TAB 4: ABC-XYZ ---
    with tabs[3]:
        st.header("ABC-XYZ Value & Volatility")
        st.write("### 📑 Executive Summary")
        matrix = pd.crosstab(part_summary['ABC'], part_summary['XYZ'])
        st.table(matrix)
        st.plotly_chart(px.treemap(part_summary, path=['ABC', 'XYZ', 'Category'], values='Total_Value'), use_container_width=True)
        st.write("### 🔍 Why")
        st.write("Targeted management strategies based on value (ABC) and predictability (XYZ).")
        rec4 = "⚠️ Action: Review high-value/volatile Z items." if not part_summary[(part_summary['ABC']=='A') & (part_summary['XYZ']=='Z')].empty else "✅ Smooth: Inventory shows stable demand."
        st.success(f"**🚀 Recommendation:** {rec4}")

    # --- TAB 5: STRATEGY ---
    with tabs[4]:
        st.header("Supply Chain Strategy")
        st.write("### 📑 Executive Summary")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Service Level Curve")
            sl_range = np.linspace(0.8, 0.99, 10)
            st.line_chart(pd.DataFrame({'SL': sl_range, 'Investment': [total_portfolio_val * (1 + (i-0.8)*5) for i in sl_range]}).set_index('SL'))
        with c2:
            st.subheader("Top Dead Stock Risk")
            st.table(part_summary.nsmallest(5, 'y')[['Part', 'Total_Value']])
        st.write("### 🔍 Why")
        st.write("Visualizing the financial investment required to achieve service goals.")
        rec5 = "⚠️ Reallocate capital from dead stock items to critical 'A' category parts."
        st.info(f"**🚀 Recommendation:** {rec5}")

    # --- TAB 6: ADVISOR (THE AI BRAIN) ---
    with tabs[5]:
        st.header("🤖 GICI Strategic AI Agent")
        
        # 1. THE CHAT BOX (This is the box you want!)
        user_input = st.chat_input("Ask the Advisor (e.g., 'What is the risk with Alpha Logistics?')")

        if user_input:
            if "GEMINI_API_KEY" not in st.secrets:
                st.error("API Key missing! Check your .streamlit/secrets.toml file.")
            else:
                with st.spinner("Analyzing data..."):
                    try:
                        from langchain_google_genai import ChatGoogleGenerativeAI
                        # This calls the secret key we force-pushed earlier
                        llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash", 
    google_api_key=st.secrets["GEMINI_API_KEY"],
    version="v1"
)
                        response = llm.invoke(f"You are a supply chain expert. Answer: {user_input}")
                        st.markdown("### 🧠 Advisor Insights")
                        st.write(response.content)
                    except Exception as e:
                        st.error(f"Brain connection error: {e}")

        st.markdown("---")
        
        # 2. YOUR ORIGINAL TABLE
        st.write("### 📑 Executive Summary")
        below_target = part_summary[part_summary['Fill_Rate'] < service_level_target]
        if not below_target.empty:
            st.dataframe(below_target[['Part', 'Category', 'Fill_Rate', 'Supplier']])
        else:
            st.success("All items are currently healthy.")
        
        st.write("### 🔍 Why")
        st.write("Daily action items for parts failing service targets.")
        rec6 = f"Expedite {len(below_target)} risky parts." if not below_target.empty else "Strategy: Maintain current buffers."
        st.success(f"**🚀 Recommendation:** {rec6}")

    # --- TAB 7: STRESS-TEST ---
    with tabs[6]:
        st.header("Supply Chain Stress-Testing")
        st.write("### 📑 Executive Summary")
        surge = st.select_slider("Simulate Demand Surge (%)", options=[0, 10, 20, 30, 40, 50])
        st.metric("Risk Exposure", f"${total_portfolio_val * (surge/100):,.0f}")
        st.write("### 🔍 Why")
        st.write("To simulate financial resilience during unexpected demand spikes.")
        rec7 = "🔴 Warning: Insufficient safety stock for 30%+ surge." if surge > 25 else "🟢 Resilient: Portfolio can handle current surge level."
        st.info(f"**🚀 Recommendation:** {rec7}")

    # --- TAB 8: NETWORK ---
    with tabs[7]:
        st.header("Multi-Echelon Network Flow")
        st.write("### 📑 Executive Summary")
        
        # --- SANKEY DIAGRAM DATA PREP ---
        # Flow: Category -> Supplier -> Part (Top 15 items for clarity)
        top_parts = part_summary.nlargest(15, 'Total_Value')
        cat_labels = list(top_parts['Category'].unique())
        sup_labels = list(top_parts['Supplier'].unique())
        part_labels = list(top_parts['Part'].unique())
        all_labels = cat_labels + sup_labels + part_labels
        
        sources, targets, values = [], [], []
        # Cat to Supplier
        for _, row in top_parts.iterrows():
            sources.append(all_labels.index(row['Category']))
            targets.append(all_labels.index(row['Supplier']))
            values.append(row['Total_Value'])
        # Supplier to Part
        for _, row in top_parts.iterrows():
            sources.append(all_labels.index(row['Supplier']))
            targets.append(all_labels.index(row['Part']))
            values.append(row['Total_Value'])
            
        fig_sankey = go.Figure(go.Sankey(
            node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5), label=all_labels, color="blue"),
            link=dict(source=sources, target=targets, value=values)
        ))
        st.plotly_chart(fig_sankey, use_container_width=True)
        
        st.write("### 🔍 Why")
        st.write("Mapping the supply chain echelons to identify capital concentration nodes.")
        st.info("**🚀 Recommendation:** Shift replenishment nodes for Category C parts to centralized regional DCs.")

    # --- TAB 9: AUDIT ---
    with tabs[8]:
        st.header("Inventory Audit & Compliance")
        st.write("### 📑 Executive Summary")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Weekly Tasks")
            st.write("1. Cycle count AX items\n2. Update Lead Times")
            st.subheader("Monthly Tasks")
            st.write("1. Dead Stock review\n2. Re-ABC Classify")
        with col2:
            st.metric("Portfolio Health Score", f"{int(avg_fill*100)}/100")
        st.write("### 🔍 Why")
        st.write("Standardized governance to maintain 100% data accuracy.")
        rec9 = "⚠️ Conduct physical audit for Hydraulics Category." if avg_fill < 0.9 else "✅ Governance schedule is on track."
        st.warning(f"**🚀 Recommendation:** {rec9}")

    # --- TAB 10: REPORT ---
    with tabs[9]:
        st.header("Monthly Executive Report")
        st.subheader("💰 Financial Health")
        st.write(f"- Total Portfolio Value: **${total_portfolio_val:,.2f}**")
        st.write(f"- Dead Stock Potential: **${total_portfolio_val * 0.12:,.2f}**")
        st.subheader("⚙️ Performance")
        st.write(f"- Portfolio Fill Rate: **{avg_fill*100:.1f}%**")
        st.subheader("🎯 Strategic Directive")
        st.write(f"- Bullwhip Signal: **{'UNSTABLE' if (df['y'].var()/df['y'].mean()) > 5 else 'STABLE'}**")
        report_csv = pd.DataFrame({"Metric": ["Portfolio Value", "Fill Rate"], "Value": [total_portfolio_val, avg_fill]}).to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Monthly Summary (CSV)", data=report_csv, file_name="GICI_Executive_Report.csv")

else:
    st.error("Error: Please check your 'Demand Forecast.xlsx' file.")
