from pathlib import Path
import threading
from datetime import datetime

import pandas as pd
import streamlit as st

from dashboard.dashboard_controller import DashboardController
from dashboard import charts
from dashboard import comparison
from dashboard import live_metrics
# =====================================================================
# 1. Page Configuration & Styling
# =====================================================================

st.set_page_config(
    page_title="Honeywell Eco-Loop | BMS",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom BMS-style CSS
st.markdown("""
<style>
    /* Global Background and Text */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Hide top header line */
    header {visibility: hidden;}

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #2C3E6B;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        color: #8899AA;
        font-weight: 500;
        font-size: 1rem;
    }
    .stTabs [aria-selected="true"] {
        color: #3498DB !important;
        border-bottom: 2px solid #3498DB !important;
    }

    /* Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        font-weight: 600;
        border: 1px solid #2C3E6B;
        background-color: #1E2530;
        color: #FAFAFA;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        border-color: #3498DB;
        color: #3498DB;
    }
    
    /* Primary Run Button */
    .stButton>button[kind="primary"] {
        background-color: #3498DB;
        color: white;
        border: none;
    }
    .stButton>button[kind="primary"]:hover {
        background-color: #2980B9;
        color: white;
    }

    /* Expander / Headers */
    .streamlit-expanderHeader {
        font-weight: 600 !important;
        color: #FAFAFA !important;
    }
    
    /* Tooltip styling adjustments */
    div[data-baseweb="tooltip"] {
        background-color: #1E2530;
        color: #FAFAFA;
        border: 1px solid #2C3E6B;
    }
    
    /* Footer */
    .bms-footer {
        margin-top: 50px;
        padding-top: 20px;
        border-top: 1px solid #2C3E6B;
        text-align: center;
        color: #8899AA;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# 2. Session State Initialization
# =====================================================================

if "optimization_running" not in st.session_state:
    st.session_state.optimization_running = False
if "optimization_complete" not in st.session_state:
    st.session_state.optimization_complete = False

# Report Caches
if "report_data" not in st.session_state:
    st.session_state.report_data = None
if "report_md" not in st.session_state:
    st.session_state.report_md = None
if "report_csv" not in st.session_state:
    st.session_state.report_csv = None

if "optimization_logs" not in st.session_state:
    st.session_state.optimization_logs = None
if "confirm_reset" not in st.session_state:
    st.session_state.confirm_reset = False
if "run_history" not in st.session_state:
    st.session_state.run_history = []
if "last_run_max_iters" not in st.session_state:
    st.session_state.last_run_max_iters = 3
if "optimization_error" not in st.session_state:
    st.session_state.optimization_error = None

# =====================================================================
# 3. Dashboard Controller
# =====================================================================

@st.cache_resource
def get_controller():
    return DashboardController()

controller = get_controller()

# Attempt to load reports on startup if they exist but aren't cached
if st.session_state.report_data is None and controller.has_reports():
    st.session_state.report_data = controller.load_report_json()
    st.session_state.report_md = controller.load_report_markdown()
    st.session_state.report_csv = controller.load_report_csv()
    st.session_state.optimization_complete = True

# =====================================================================
# Helper Functions
# =====================================================================

def empty_state_placeholder():
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px; background-color: #1E2530; 
                border: 1px dashed #2C3E6B; border-radius: 10px; margin-top: 20px;">
        <h3 style="color: #8899AA; font-weight: 400;">No optimization data available.</h3>
        <p style="color: #667788; font-size: 0.9rem;">
            Click <strong>▶ Run Optimization</strong> in the sidebar to begin a new closed-loop HVAC optimization.
        </p>
    </div>
    """, unsafe_allow_html=True)

def update_run_history(report: dict, runtime: float, status: str):
    run_num = len(st.session_state.run_history) + 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    iters = report.get("optimization", {}).get("iterations", 0)
    
    # Calculate Energy Reduction
    imp = report.get("improvements", {})
    hvac_red = imp.get("total_hvac_energy_reduction_pct", 0.0)
    hvac_red_str = f"{hvac_red:.2f}%"
    
    st.session_state.run_history.append({
        "Run": run_num,
        "Time": timestamp,
        "Runtime": f"{runtime:.1f} s",
        "Iterations": iters,
        "HVAC Reduction": hvac_red_str,
        "Status": status
    })

# =====================================================================
# 4. Sidebar Layout
# =====================================================================

with st.sidebar:
    st.markdown("""
    <h2 style="color: #FAFAFA; margin-bottom: 0px;">Honeywell Eco-Loop</h2>
    <p style="color: #3498DB; font-weight: 500; font-size: 0.9rem; margin-top: 0px;">Building Agents</p>
    <p style="color: #8899AA; font-size: 0.8rem;">Closed-Loop HVAC Optimization</p>
    <hr style="border-color: #2C3E6B; margin: 10px 0px;">
    """, unsafe_allow_html=True)
    
    st.markdown("**Technology Stack**")
    st.markdown("- EnergyPlus\n- Groq Llama 3.3\n- Streamlit")
    
    st.markdown("<hr style='border-color: #2C3E6B; margin: 15px 0px;'>", unsafe_allow_html=True)
    st.markdown("**Controls**")
    
    # Run Button
    if st.button("▶ Run Optimization", type="primary", disabled=st.session_state.optimization_running):
        st.session_state.optimization_running = True
        st.session_state.optimization_error = None
        st.session_state.last_run_max_iters = st.session_state.get("max_iters_input", 3)
        st.rerun()

    # Continue Button
    can_continue, continue_reason = controller.can_continue()
    st.button("⏩ Continue", disabled=not can_continue, help=continue_reason)
    
    # Reset Button
    if not st.session_state.confirm_reset:
        if st.button("🔄 Reset Workspace"):
            st.session_state.confirm_reset = True
            st.rerun()
    else:
        st.warning("Confirm Reset?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, Execute"):
                controller.reset_workspace()
                st.session_state.report_data = None
                st.session_state.report_md = None
                st.session_state.report_csv = None
                st.session_state.optimization_logs = None
                st.session_state.optimization_complete = False
                st.session_state.optimization_error = None
                st.session_state.run_history = []
                st.session_state.confirm_reset = False
                st.rerun()
        with col2:
            if st.button("Cancel"):
                st.session_state.confirm_reset = False
                st.rerun()
                
    st.markdown("<hr style='border-color: #2C3E6B; margin: 15px 0px;'>", unsafe_allow_html=True)
    st.markdown("**Parameters**")
    
    max_iters = st.number_input("Maximum Allowed Iterations", min_value=1, max_value=20, value=3, step=1, disabled=st.session_state.optimization_running, key="max_iters_input")
    
    st.markdown("""
    <div style="margin-top: 10px;">
        <label style="font-size: 14px; color: #FAFAFA;">Convergence Threshold</label>
        <div style="background-color: #1E2530; padding: 8px 12px; border-radius: 4px; border: 1px solid #2C3E6B; color: #8899AA; font-size: 0.85rem;">
            0.5% (Managed by backend)
        </div>
    </div>
    <div style="margin-top: 15px;">
        <label style="font-size: 14px; color: #FAFAFA;">Weather File</label>
        <div style="background-color: #1E2530; padding: 8px 12px; border-radius: 4px; border: 1px solid #2C3E6B; color: #8899AA; font-size: 0.85rem; word-break: break-all;">
            {}
        </div>
    </div>
    """.format(controller.get_weather_file_name()), unsafe_allow_html=True)

# =====================================================================
# Execution Logic
# =====================================================================

if st.session_state.optimization_running:
    with st.spinner("Executing Closed-Loop Optimization... Please wait."):
        # Run optimization through controller
        res = controller.run_optimization(max_iterations=max_iters)
        
        # Reload reports from disk to session state
        st.session_state.report_data = controller.load_report_json()
        st.session_state.report_md = controller.load_report_markdown()
        st.session_state.report_csv = controller.load_report_csv()
        st.session_state.optimization_logs = res.get("logs", "")
        
        # Update Run History
        if res["status"] == "success" and st.session_state.report_data:
            opt = st.session_state.report_data.get("optimization", {})
            runtime = opt.get("runtime_seconds", 0.0)
            status_text = "Converged" if opt.get("convergence_reason") else "Completed"
            update_run_history(st.session_state.report_data, runtime, status_text)
        else:
            st.session_state.optimization_error = res.get("error", "Unknown backend error")
            update_run_history(st.session_state.report_data or {}, 0.0, "Failed")
            
        st.session_state.optimization_running = False
        st.session_state.optimization_complete = True
        st.rerun()

# =====================================================================
# 5. Main UI (Tabs)
# =====================================================================

tab_overview, tab_optim, tab_analytics, tab_reports = st.tabs([
    "Overview", "Optimization", "Analytics", "Reports"
])

report = st.session_state.report_data

# ---------------------------------------------------------------------
# Tab 1: Overview
# ---------------------------------------------------------------------
with tab_overview:
    st.markdown("<h2 style='margin-bottom: 20px;'>Optimization Overview</h2>", unsafe_allow_html=True)
    
    if st.session_state.get("optimization_error"):
        st.error(f"**Optimization Failed:**\n\n{st.session_state.optimization_error}")
        
    if not report:
        empty_state_placeholder()
    else:
        # System Information Panel
        opt = report.get("optimization", {})
        sys_info = report.get("system_information", {})
        runtime = opt.get("runtime_seconds", 0)
        iters = opt.get("iterations", 0)
        conv_reason = opt.get("convergence_reason", "")
        status = "Converged" if conv_reason else "Completed"
        
        status_html = f"✓ {status}" if conv_reason else status
        
        st.markdown(f"""
        <div style="background-color: #1E2530; border: 1px solid #2C3E6B; border-radius: 8px; padding: 15px 20px; margin-bottom: 25px; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 15px;">
            <div><span style="color: #8899AA; font-size: 0.8rem; text-transform: uppercase;">Engine</span><br><span style="font-weight: 600; color: #FAFAFA;">{sys_info.get('simulation_engine', 'EnergyPlus')}</span></div>
            <div><span style="color: #8899AA; font-size: 0.8rem; text-transform: uppercase;">LLM</span><br><span style="font-weight: 600; color: #3498DB;">{sys_info.get('llm_model', 'Groq Llama 3.3')}</span></div>
            <div><span style="color: #8899AA; font-size: 0.8rem; text-transform: uppercase;">Max Allowed Iters</span><br><span style="font-weight: 600; color: #FAFAFA;">{st.session_state.last_run_max_iters}</span></div>
            <div><span style="color: #8899AA; font-size: 0.8rem; text-transform: uppercase;">Iters Executed</span><br><span style="font-weight: 600; color: #FAFAFA;">{iters}</span></div>
            <div><span style="color: #8899AA; font-size: 0.8rem; text-transform: uppercase;">Status</span><br><span style="font-weight: 600; color: #2ECC71;">{status_html}</span></div>
            <div><span style="color: #8899AA; font-size: 0.8rem; text-transform: uppercase;">Runtime</span><br><span style="font-weight: 600; color: #FAFAFA;">{runtime} s</span></div>
        </div>
        """, unsafe_allow_html=True)
        
        # KPI Cards using Comparison Tool
        st.markdown("<h3 style='font-size: 1.2rem; color: #8899AA; margin-bottom: 15px;'>Key Performance Indicators</h3>", unsafe_allow_html=True)
        
        # We will render custom KPI cards using Streamlit metrics with tooltips
        imp = report.get("improvements", {})
        
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        
        def render_kpi(col, label, value, tooltip, is_cooling=False):
            if value is None:
                val_str, color, arrow = "Not Available", "#8899AA", ""
            else:
                val_str = f"{abs(value):.2f}%"
                if is_cooling:
                    # For cooling, positive value means change (increase), negative means reduction
                    is_good = value <= 0
                    arrow = "▼" if is_good else "▲"
                else:
                    # For reductions, positive value is good
                    is_good = value >= 0
                    arrow = "▲" if is_good else "▼"
                color = "#2ECC71" if is_good else "#E74C3C"
                
            with col:
                st.markdown(f"""
                <div title="{tooltip}" style="background-color: #161B22; border: 1px solid #2C3E6B; border-radius: 8px; padding: 15px; text-align: center; height: 100%;">
                    <div style="color: #8899AA; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 8px;">{label}</div>
                    <div style="color: {color}; font-size: 1.5rem; font-weight: 700;">{arrow} {val_str}</div>
                </div>
                """, unsafe_allow_html=True)
        
        render_kpi(c1, "HVAC Energy Red.", imp.get("total_hvac_energy_reduction_pct"), "Overall reduction in HVAC energy consumption compared with the baseline simulation.")
        render_kpi(c2, "Heating Energy Red.", imp.get("heating_energy_reduction_pct"), "Percentage reduction in heating energy consumption.")
        render_kpi(c3, "Cooling Energy Chg.", imp.get("cooling_energy_change_pct"), "Signed percentage change in cooling energy. Positive values indicate increased cooling demand. Negative values indicate reduced cooling demand.", is_cooling=True)
        render_kpi(c4, "Comfort Change", imp.get("comfort_change_pct"), "Difference in thermal comfort percentage between baseline and optimized simulation.")
        
        # Peak demand might be reduction or change
        pk_val = imp.get("peak_demand_reduction_pct", imp.get("peak_demand_change_pct"))
        render_kpi(c5, "Peak Demand Red.", pk_val, "Reduction in peak HVAC power demand during the optimization period.")
        
        with c6:
            st.markdown(f"""
            <div title="Total number of optimization iterations performed." style="background-color: #161B22; border: 1px solid #2C3E6B; border-radius: 8px; padding: 15px; text-align: center; height: 100%;">
                <div style="color: #8899AA; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 8px;">Iterations</div>
                <div style="color: #FAFAFA; font-size: 1.5rem; font-weight: 700;">{iters}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Comparison Cards
        st.markdown("<h3 style='font-size: 1.2rem; color: #8899AA; margin-bottom: 15px;'>Baseline vs Optimized</h3>", unsafe_allow_html=True)
        comparison.render_comparison_cards(report)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Run History Table
        st.markdown("<h3 style='font-size: 1.2rem; color: #8899AA; margin-bottom: 15px;'>Session Run History</h3>", unsafe_allow_html=True)
        if st.session_state.run_history:
            df_history = pd.DataFrame(st.session_state.run_history)
            st.dataframe(df_history, hide_index=True, use_container_width=True)
        else:
            st.info("No runs recorded in current session.")


# ---------------------------------------------------------------------
# Tab 2: Optimization
# ---------------------------------------------------------------------
with tab_optim:
    st.markdown("<h2 style='margin-bottom: 20px;'>Optimization Progress</h2>", unsafe_allow_html=True)
    
    if not report:
        empty_state_placeholder()
    else:
        iters = report.get("optimization", {}).get("iterations", 0)
        
        # Progress Bar
        live_metrics.render_progress_bar(iters, iters, "Completed")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Status Panel
        live_metrics.render_status_panel(report)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        records = report.get("iteration_records", [])
        
        with col1:
            st.markdown("<h3 style='font-size: 1.1rem; color: #8899AA;'>Iteration Results</h3>", unsafe_allow_html=True)
            live_metrics.render_iteration_assessment(records)
            
        with col2:
            st.markdown("<h3 style='font-size: 1.1rem; color: #8899AA;'>LLM Decisions</h3>", unsafe_allow_html=True)
            live_metrics.render_iteration_decisions(records)
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h3 style='font-size: 1.1rem; color: #8899AA;'>Console Logs</h3>", unsafe_allow_html=True)
        live_metrics.render_log_window(st.session_state.optimization_logs)


# ---------------------------------------------------------------------
# Tab 3: Analytics
# ---------------------------------------------------------------------
with tab_analytics:
    st.markdown("<h2 style='margin-bottom: 20px;'>Optimization Analytics</h2>", unsafe_allow_html=True)
    
    if not report:
        empty_state_placeholder()
    else:
        st.markdown("<h3 style='font-size: 1.2rem; color: #8899AA; border-bottom: 1px solid #2C3E6B; padding-bottom: 10px;'>Energy</h3>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            fig_h = charts.render_heating_energy_chart(report)
            if fig_h: st.plotly_chart(fig_h, use_container_width=True)
            else: st.info("Heating Energy data not available.")
        with c2:
            fig_c = charts.render_cooling_energy_chart(report)
            if fig_c: st.plotly_chart(fig_c, use_container_width=True)
            else: st.info("Cooling Energy data not available.")
            
        fig_t = charts.render_total_hvac_energy_chart(report)
        if fig_t: st.plotly_chart(fig_t, use_container_width=True)
        else: st.info("Total HVAC Energy data not available.")
        
        st.markdown("<br><h3 style='font-size: 1.2rem; color: #8899AA; border-bottom: 1px solid #2C3E6B; padding-bottom: 10px;'>Control</h3>", unsafe_allow_html=True)
        fig_sp = charts.render_setpoint_progression_chart(report)
        if fig_sp: st.plotly_chart(fig_sp, use_container_width=True)
        else: st.info("Setpoint Progression data not available.")
        
        st.markdown("<br><h3 style='font-size: 1.2rem; color: #8899AA; border-bottom: 1px solid #2C3E6B; padding-bottom: 10px;'>Comfort</h3>", unsafe_allow_html=True)
        fig_com = charts.render_comfort_chart(report)
        if fig_com: st.plotly_chart(fig_com, use_container_width=True)
        else: st.info("Comfort data not available.")
        
        st.markdown("<br><h3 style='font-size: 1.2rem; color: #8899AA; border-bottom: 1px solid #2C3E6B; padding-bottom: 10px;'>Summary</h3>", unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3:
            fig_pie = charts.render_energy_breakdown_pie(report)
            if fig_pie: st.plotly_chart(fig_pie, use_container_width=True)
            else: st.info("Energy Breakdown data not available.")
        with c4:
            fig_tl = charts.render_optimization_timeline(report)
            if fig_tl: st.plotly_chart(fig_tl, use_container_width=True)
            else: st.info("Runtime-per-iteration data is not available.")





# ---------------------------------------------------------------------
# Tab 5: Reports
# ---------------------------------------------------------------------
with tab_reports:
    st.markdown("<h2 style='margin-bottom: 20px;'>Optimization Reports</h2>", unsafe_allow_html=True)
    
    if not report:
        empty_state_placeholder()
    else:
        st.markdown("<h3 style='font-size: 1.2rem; color: #8899AA; margin-bottom: 15px;'>Comparison Table</h3>", unsafe_allow_html=True)
        comparison.render_comparison_table(report)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h3 style='font-size: 1.2rem; color: #8899AA; margin-bottom: 15px;'>Generated Artifacts</h3>", unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns(4)
        has_json = st.session_state.report_data is not None
        has_md = st.session_state.report_md is not None
        has_csv = st.session_state.report_csv is not None
        has_idf = controller.has_optimized_idf()
        
        import json
        json_data = json.dumps(st.session_state.report_data, indent=2) if has_json else ""
        
        with c1:
            st.download_button(
                label="📄 Download JSON",
                data=json_data,
                file_name="optimization_report.json",
                mime="application/json",
                disabled=not has_json,
                use_container_width=True
            )
        with c2:
            st.download_button(
                label="📝 Download Markdown",
                data=st.session_state.report_md or "",
                file_name="optimization_report.md",
                mime="text/markdown",
                disabled=not has_md,
                use_container_width=True
            )
        with c3:
            st.download_button(
                label="📊 Download CSV",
                data=st.session_state.report_csv or "",
                file_name="optimization_summary.csv",
                mime="text/csv",
                disabled=not has_csv,
                use_container_width=True
            )
        with c4:
            idf_bytes = controller.load_optimized_idf_bytes()
            st.download_button(
                label="🏢 Download Optimized IDF",
                data=idf_bytes or b"",
                file_name="optimized.idf",
                mime="application/octet-stream",
                disabled=not has_idf,
                use_container_width=True
            )
            
        st.markdown("<br><h3 style='font-size: 1.2rem; color: #8899AA; margin-bottom: 15px;'>Executive Summary</h3>", unsafe_allow_html=True)
        st.markdown(f"<div style='background-color: #1E2530; padding: 20px; border-radius: 8px; border: 1px solid #2C3E6B;'>{st.session_state.report_md}</div>", unsafe_allow_html=True)


# =====================================================================
# Footer
# =====================================================================

st.markdown("""
<div class="bms-footer">
    <strong>Honeywell Eco-Loop Building Agents</strong><br>
    Closed-Loop Autonomous HVAC Optimization<br>
    <span style="color: #667788; font-size: 0.75rem;">EnergyPlus • Groq Llama 3.3 • Streamlit</span>
</div>
""", unsafe_allow_html=True)
