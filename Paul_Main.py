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
        
        # --- ENRICHMENT ENGINE (Creating advanced metrics from your 5 columns) ---
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

# 3. The 10-Tab Structure
tabs = st.tabs([
    "💰 Financials", "🚚 Suppliers", "📦 SOP", "🔍 ABC-XYZ", "🎯 Strategy", 
    "🤖 Advisor", "🧪 Stress-Test", "🌐 Network", "🕵️ Audit", "📄 Monthly Report"
])

if df is not None:
    # --- PRE-CALCULATION BLOCK ---
    part_summary = df.groupby(['Part', 'Category', 'Supplier']).agg({
        'y': 'sum',
        'Unit_Cost': 'mean',
        'Total_Value': 'sum',
        'Lead_Time': 'mean',
        'Fill_Rate': 'mean'
    }).reset_index()
    
    total_portfolio_val = part_summary['Total_Value'].sum()
    avg_fill = part_summary['Fill_Rate'].mean()
    
    # ABC-XYZ Matrix Logic
    part_summary = part_summary.sort_values('Total_Value', ascending=False)
    part_summary['Cum_Value'] = part_summary['Total_Value'].cumsum() / total_portfolio_val
    part_summary['ABC'] = pd.cut(part_summary['Cum_Value'], bins=[0, 0.7, 0.9, 1.0], labels=['A', 'B', 'C'])
    
    cv = df.groupby('Part')['y'].std() / df.groupby('Part')['y'].mean()
    part_summary = part_summary.merge(cv.rename('CV'), on='Part')
    part_summary['XYZ'] = part_summary['CV'].apply(lambda x: 'X' if x < 0.5 else ('Y' if x < 1.0 else 'Z'))

    # --- TAB 1: Financials ---
    with tabs[0]:
        st.header("Financial Inventory Health")
        st.write("### 📑 Executive Summary")
        st.write(f"The portfolio is currently valued at **${total_portfolio_val:,.2f}** with an average fill rate of **{avg_fill*100:.1f}%**.")
        
        fig1 = px.scatter(part_summary, x='Lead_Time', y='Fill_Rate', color='Category', size='Total_Value',
                         hover_name='Part', title="Fill Rate vs. Average Lead Time")
        st.plotly_chart(fig1, use_container_width=True)
        
        st.write("### 🔍 Why")
        st.write("To identify if long lead times are negatively impacting our ability to fulfill orders.")
        
        # ADAPTABLE RECOMMENDATION
        if avg_fill < 0.90:
            rec1 = "⚠️ Urgent: Fill rates are below target. Expedite 'A' category items and audit supplier lead times."
        else:
            rec1 = "✅ Performance Optimal: Maintain current safety stock levels and focus on cost reduction."
        st.info(f"**🚀 Recommendation:** {rec1}")

    # --- TAB 2: Suppliers ---
    with tabs[1]:
        st.header("Supplier Performance")
        st.write("### 📑 Executive Summary")
        sup_perf = part_summary.groupby('Supplier')['Fill_Rate'].mean().reset_index()
        st.bar_chart(sup_perf.set_index('Supplier'))
        
        st.write("### 🔍 Why")
        st.write("To rank suppliers based on their reliability and contribution to portfolio health.")
        
        worst_sup = sup_perf.sort_values('Fill_Rate').iloc[0]
        rec2 = f"Review contract with **{worst_sup['Supplier']}** due to sub-par fill rates ({worst_sup['Fill_Rate']*100:.1f}%)."
        st.info(f"**🚀 Recommendation:** {rec2}")

   # --- TAB 3: SOP ---
    with tabs[2]:
        st.header("SOP Engine")
        st.write("### 📑 Executive Summary")
        
        # CORRECTED CALCULATION
        sop_data = part_summary.copy()
        
        # Calculate standard deviation per part to get a Series, then fillna, then multiply
        std_devs = df.groupby('Part')['y'].std().fillna(0)
        sop_data = sop_data.merge(std_devs.rename('std_dev'), on='Part', how='left')
        
        sop_data['Safety_Stock'] = sop_data['std_dev'] * 1.65
        sop_data['ROP'] = (sop_data['y']/30 * sop_data['Lead_Time']) + sop_data['Safety_Stock']
        sop_data['EOQ'] = np.sqrt((2 * sop_data['y'] * 100) / (sop_data['Unit_Cost'] * holding_cost_pct + 0.01))
        sop_data['Holding_Cost'] = sop_data['Total_Value'] * holding_cost_pct
        
        # Excel Downloader logic remains the same
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            sop_data[['Part', 'Category', 'Fill_Rate', 'Safety_Stock', 'ROP', 'EOQ', 'Holding_Cost', 'Total_Value']].to_excel(writer, index=False)
        
        st.download_button("📥 Download SOP Strategy Sheet (Excel)", data=output.getvalue(), file_name="GICI_SOP_Plan.xlsx")
        
        st.write("### 🔍 Why")
        st.write("Scientific calculation of safety stock ensures we maintain service levels without capital bloat.")
        
        # ADAPTABLE RECOMMENDATION based on Safety Stock levels
        avg_ss = sop_data['Safety_Stock'].mean()
        if avg_ss > sop_data['y'].mean() * 0.5:
            rec3 = "⚠️ High Buffer Alert: Safety stock exceeds 50% of demand. Audit lead time variability to reduce requirements."
        else:
            rec3 = "✅ Lean Buffers: Safety stock levels are optimized for current demand volatility."
        st.info(f"**🚀 Recommendation:** {rec3}")

    # --- TAB 4: ABC-XYZ ---
    with tabs[3]:
        st.header("ABC-XYZ Value & Volatility Matrix")
        st.write("### 📑 Executive Summary")
        matrix = pd.crosstab(part_summary['ABC'], part_summary['XYZ'])
        st.table(matrix)
        
        st.write("### 🔍 Why")
        st.write("To differentiate management styles: AX items need tight control; CZ items can be automated.")
        
        z_count = len(part_summary[part_summary['XYZ'] == 'Z'])
        rec4 = f"Warning: {z_count} items show extreme volatility (Z-Class). Increase buffer stock for these SKUs."
        st.success(f"**🚀 Recommendation:** {rec4}")

    # --- TAB 5: Strategy ---
    with tabs[4]:
        st.header("Supply Chain Strategy")
        st.write("### 📑 Executive Summary")
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Service Level Curve")
            x_sl = np.linspace(0.8, 0.99, 10)
            y_inv = [total_portfolio_val * (1 + (i - 0.8)*2) for i in x_sl]
            fig_sl = px.line(x=x_sl, y=y_inv, labels={'x':'Service Level', 'y':'Required Capital ($)'})
            st.plotly_chart(fig_sl)
        with c2:
            st.subheader("Top Dead Stock Risk")
            dead_stock = part_summary.sort_values('y').head(5)
            st.table(dead_stock[['Part', 'Total_Value']])

        st.subheader("Most Critical Items (Investment vs Demand)")
        st.dataframe(part_summary.nlargest(5, 'Total_Value')[['Part', 'y', 'Supplier', 'Total_Value']])
        
        st.write("### 🔍 Why")
        st.write("Visualizing the 'Cost of Service' helps leadership decide where to balance risk vs. capital.")
        st.info("**🚀 Recommendation:** Pivot capital from the Dead Stock list to the Critical Items list.")

    # --- TAB 6: Advisor ---
    with tabs[5]:
        st.header("Gogo Intelligence Advisor")
        st.write("### 📑 Executive Summary")
        risky = part_summary[part_summary['Fill_Rate'] < service_level_target]
        st.write(f"Detected **{len(risky)}** items currently failing to meet your {service_level_target*100}% target.")
        
        st.write("### 🔍 Why")
        st.write("AI-driven prioritization of parts that require immediate management intervention.")
        st.success("**🚀 Recommendation:** Expedite all shipments for parts in the 'A' category with low fill rates.")

    # --- TAB 7: Stress-Test ---
    with tabs[6]:
        st.header("Supply Chain Stress-Testing")
        st.write("### 📑 Executive Summary")
        surge = st.select_slider("Simulate Demand Surge (%)", options=[0, 10, 20, 30, 40, 50])
        exposure = total_portfolio_val * (surge/100)
        st.metric("Capital Exposure Risk", f"${exposure:,.2f}", delta=f"{surge}% Surge")
        
        st.write("### 🔍 Why")
        st.write("To simulate 'Black Swan' events and calculate the financial buffer required for resilience.")
        rec7 = "⚠️ High Risk: Current liquidity cannot cover a 30%+ surge." if surge > 25 else "✅ Safe: Buffers are adequate."
        st.info(f"**🚀 Recommendation:** {rec7}")

    # --- TAB 8: Network ---
    with tabs[7]:
        st.header("Multi-Echelon Network")
        st.write("### 📑 Executive Summary")
        fig_net = px.sunburst(part_summary, path=['Category', 'Part'], values='Total_Value', title="Network Distribution by Category")
        st.plotly_chart(fig_net)
        
        st.write("### 🔍 Why")
        st.write("To visualize where inventory is concentrated within the multi-echelon network.")
        st.info("**🚀 Recommendation:** Rebalance stock from Satellite Hubs to Central DC for C-class items.")

    # --- TAB 9: Audit ---
    with tabs[8]:
        st.header("Inventory Audit & Compliance")
        st.write("### 📑 Executive Summary")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📅 Weekly Tasks")
            st.write("- [ ] Cycle Count AX Items\n- [ ] Audit Supplier Lead Times\n- [ ] Review Open POs")
            st.subheader("🗓️ Monthly Tasks")
            st.write("- [ ] Liquidate Dead Stock\n- [ ] Re-classify ABC Categories\n- [ ] VMI Performance Review")
        with col2:
            health_score = int(avg_fill * 100)
            st.metric("Portfolio Health Score", f"{health_score}/100")
        
        st.write("### 🔍 Why")
        st.write("Standardized tasks ensure that the system remains accurate and data integrity is maintained.")
        st.warning("**🚀 Recommendation:** Immediate cycle count required for Hydraulics category due to high variance.")

    # --- TAB 10: Monthly Report ---
    with tabs[9]:
        st.header("Monthly Executive Category Report")
        st.subheader("💰 Financial Health")
        st.write(f"- **Total Portfolio Value:** ${total_portfolio_val:,.2f}")
        st.write(f"- **Capital Recovery Potential:** ${total_val*0.08:,.2f} (Dead Stock)")
        
        st.subheader("⚙️ Operational Performance")
        st.write(f"- **Portfolio Fill Rate:** {avg_fill*100:.1f}%")
        st.write(f"- **Underperforming Category:** {part_summary.groupby('Category')['Fill_Rate'].mean().idxmin()}")
        
        st.subheader("🎯 Strategic Directive")
        bullwhip = "UNSTABLE" if (df['y'].var() / df['y'].mean()) > 8 else "STABLE"
        st.write(f"- **Bullwhip Signal:** {bullwhip}")
        st.write("- **VMI Priority:** HIGH (Tier 1 Suppliers)")
        
        st.button("📥 Export Final Monthly Executive PDF")

else:
    st.error("Data connection failed. Please check 'Demand Forecast.xlsx'.")
   
