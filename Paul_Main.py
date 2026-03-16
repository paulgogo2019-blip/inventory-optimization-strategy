import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
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
        
        # --- ENRICHMENT ENGINE (Simulating metrics for Strategy/Audit tabs) ---
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
        m3.metric("Avg Fill Rate", f"{avg_fill*100:.1f}%")
        
        fig_pie = px.pie(part_summary, values='Total_Value', names='Category', title="Investment by Category", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
        
        st.write("### 🔍 Why")
        st.write("To understand capital allocation and identify the high-cost categories draining liquidity.")
        rec1 = "⚠️ High Capital Alert: Investment exceeds $500k. Review A-class items." if total_portfolio_val > 500000 else "✅ Capital Allocation: Within target budget."
        st.info(f"**🚀 Recommendation:** {rec1}")

    # --- TAB 2: SUPPLIERS ---
    with tabs[1]:
        st.header("Supplier Performance")
        sup_data = part_summary.groupby('Supplier').agg({'Fill_Rate': 'mean', 'Lead_Time': 'mean'}).reset_index()
        fig_sup = px.bar(sup_data, x='Supplier', y='Lead_Time', color='Fill_Rate', title="Supplier Lead Time vs Reliability")
        st.plotly_chart(fig_sup, use_container_width=True)
        
        slowest = sup_data.sort_values('Lead_Time', ascending=False).iloc[0]
        rec2 = f"Mitigate risk for **{slowest['Supplier']}** due to {slowest['Lead_Time']:.1f} day lead time."
        st.info(f"**🚀 Recommendation:** {rec2}")

    # --- TAB 3: SOP ---
    with tabs[2]:
        st.header("SOP Engine")
        sop_data = part_summary.copy()
        sop_data['Safety_Stock'] = sop_data['std_dev'] * 1.65
        sop_data['ROP'] = (sop_data['y']/30 * sop_data['Lead_Time']) + sop_data['Safety_Stock']
        sop_data['EOQ'] = np.sqrt((2 * sop_data['y'] * 100) / (sop_data['Unit_Cost'] * holding_cost_pct + 0.01))
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            sop_data[['Part', 'y', 'Category', 'Fill_Rate', 'Safety_Stock', 'ROP', 'EOQ', 'Total_Value']].to_excel(writer, index=False)
        st.download_button("📥 Download SOP Plan (Excel)", data=output.getvalue(), file_name="GICI_SOP_Plan.xlsx")
        st.info("**🚀 Recommendation:** Implement calculated ROPs for all 'AX' items.")

    # --- TAB 6: ADVISOR ---
    with tabs[5]:
        st.header("Gogo Intelligence Advisor")
        below_target = part_summary[part_summary['Fill_Rate'] < service_level_target]
        st.subheader(f"Parts Below Service Target ({service_level_target*100}%)")
        if not below_target.empty:
            st.dataframe(below_target[['Part', 'Category', 'Fill_Rate', 'Supplier']])
            rec6 = f"Expedite {len(below_target)} parts immediately to prevent stockouts."
        else:
            st.success("All parts are meeting service targets.")
            rec6 = "Maintain current replenishment strategy."
        st.success(f"**🚀 Recommendation:** {rec6}")

    # --- TAB 10: MONTHLY REPORT ---
    with tabs[9]:
        st.header("Monthly Executive Category Report")
        
        # Dynamic Signal Logic
        bullwhip_val = df['y'].var() / df['y'].mean() if df['y'].mean() > 0 else 0
        bw_signal = "UNSTABLE" if bullwhip_val > 5 else "STABLE"
        underperforming_cat = part_summary.groupby('Category')['Fill_Rate'].mean().idxmin()

        # Display Sections
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("💰 Financial Health")
            st.write(f"- Total Portfolio Value: **${total_portfolio_val:,.0f}**")
            st.write(f"- Annual Carrying Cost: **${annual_holding_cost:,.0f}**")
            st.write(f"- Dead Stock Recovery: **${total_portfolio_val * 0.12:,.0f}**")
        
        with col_b:
            st.subheader("⚙️ Operational Performance")
            st.write(f"- Avg Fill Rate: **{avg_fill*100:.1f}%**")
            st.write(f"- Underperforming Cat: **{underperforming_cat}**")
            st.write(f"- Bullwhip Signal: **{bw_signal}**")

        # GENERATE REPORT CONTENT
        report_data = {
            "Metric": ["Portfolio Value", "Fill Rate", "Bullwhip Status", "Underperforming Category", "VMI Priority"],
            "Result": [f"${total_portfolio_val:,.0f}", f"{avg_fill*100:.1f}%", bw_signal, underperforming_cat, "HIGH"]
        }
        report_df = pd.DataFrame(report_data)
        
        csv = report_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Executive Report (CSV)", data=csv, file_name="GICI_Monthly_Report.csv", mime='text/csv')
        
        # ADAPTABLE RECOMMENDATION
        rec10 = f"Strategy: Transition {underperforming_cat} to VMI to stabilize the {bw_signal} signal."
        st.info(f"**🚀 Recommendation:** {rec10}")

else:
    st.error("Error: Please check 'Demand Forecast.xlsx'.")
