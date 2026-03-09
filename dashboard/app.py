"""Professional Streamlit dashboard for VisionGuard Safety AI."""

import sys
import os
import time
from datetime import datetime, timedelta

import cv2
import pandas as pd
import streamlit as st
import plotly.express as px
from PIL import Image
from streamlit_extras.stylable_container import stylable_container
from streamlit_option_menu import option_menu

# Ensure project root is on the path for local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.monitor import SafetyMonitor

# ───────────────────────── Page Config ─────────────────────────
jadeimage = Image.open("logo/jadeglobalsmall.png")
st.set_page_config(
    page_title="VisionGuard Safety AI",
    page_icon=jadeimage,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ───────────────────────── Session State ─────────────────────────
if "monitor" not in st.session_state:
    st.session_state.monitor = SafetyMonitor(use_snowflake=True)

if "violations_log" not in st.session_state:
    st.session_state.violations_log = []

monitor: SafetyMonitor = st.session_state.monitor

# ───────────────────────── Custom UI Styling ─────────────────────────
CUSTOM_CSS = """
<style>
    /* Global Styles */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
    }
    .stAppHeader { visibility: hidden; }
    footer { visibility: hidden; }

    /* Sidebar Image Centering */
    [data-testid=stSidebar] [data-testid=stImage]{
        text-align: center;
        display: block;
        margin-left: auto;
        margin-right: auto;
        width: 80%;
    }

    /* Expander / Details Styling */
    details > summary {
        font-weight: 600;
        background-color: #f5f5f5;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    details > summary:hover {
        background-color: #FAEABD !important;
        color: black !important;
        transform: scale(1.02);
    }

    /* Custom Button Styles */
    .stButton > button {
        border-radius: 8px !important;
        border: 2px solid #144774 !important;
        background-color: #175388 !important;
        color: white !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton > button:hover {
        background-color: #ecb713 !important;
        border-color: #c49e10 !important;
        color: white !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def render_banner(title, subtitle):
    """Renders the Jade-style gradient banner."""
    banner_html = f"""
    <style>
        .gradient-box {{
            padding: 25px;
            border-radius: 15px;
            width: 100%;
            background: linear-gradient(135deg, #175388 0%, #2A7B9B 100%);
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
            margin-bottom: 1.5rem;
            text-align: center;
        }}
        .solid-text {{
            font-size: 40px;
            font-weight: bold;
            color: #FFFFFF;
            margin: 0;
            line-height: 1.1;
        }}
        .subtext {{
            font-size: 18px;
            color: #E0F7FA;
            margin-top: 10px;
            font-weight: 500;
        }}
    </style>
    <div class="gradient-box">
        <div class="solid-text">{title}</div>
        <div class="subtext">{subtitle}</div>
    </div>
    """
    st.markdown(banner_html, unsafe_allow_html=True)

# ───────────────────────── Sidebar Navigation ─────────────────────────
with st.sidebar:
    st.image('logo/jadeglobal.png')
    st.markdown("""
    <div style='text-align: center; color: #175388;'>
        <h1 style='margin-bottom: 0; padding-bottom: 0;'>VisionGuard AI</h1>
        <h3 style='margin-top: 0px; padding-top: 0;'>Zero Harm Workplace</h3>
    </div>
    """, unsafe_allow_html=True)
    
    selected_page = option_menu(
        menu_title=None,
        options=['Dashboard', 'Live Monitor'],
        icons=['speedometer2', 'camera-video'],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "white", "font-size": "16px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "5px 0",
                "color": "white",
                "border-radius": "8px",
                "background-color": "#175388",
            },
            "nav-link-selected": {"background-color": "#ecb713"},
        }
    )
    
    st.divider()
    st.markdown(f"**👤 Operator:** {st.secrets.get('streamlit_username', 'Admin')}")
    st.markdown("**Status:** :green[Connected 🟢]")
    
    if st.button("❌ System Logout", width='stretch'):
        st.session_state["authenticated"] = False
        st.rerun()

# ───────────────────────── PAGE 1: DASHBOARD ─────────────────────────
if selected_page == 'Dashboard':
    render_banner("🦺 Safety Analytics", "Real-time compliance oversight and historical violation tracking.")
    
    # 1. Fetch Data
    query = "SELECT TIMESTAMP, LOCATION, VIOLATION_TYPE FROM ZERO_HARM_AI.SAFETY.VIOLATIONS ORDER BY TIMESTAMP DESC"
    try:
        df = monitor.db.fetch_data(query)
        if df is None or df.empty:
            df = pd.DataFrame([v.to_dict() for v in st.session_state.violations_log])
    except Exception as e:
        df = pd.DataFrame([v.to_dict() for v in st.session_state.violations_log])

    if df.empty:
        st.info("No safety data available yet. Please activate the Live Monitor to begin.")
    else:
        df.columns = [col.upper() for col in df.columns]
        df['TIMESTAMP'] = pd.to_datetime(df['TIMESTAMP'], errors='coerce')
        
        # Calculate Metrics
        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)
        
        today_df = df[df['TIMESTAMP'].dt.date == now.date()]
        # Filter strictly for 7 days
        week_df = df[df['TIMESTAMP'] >= seven_days_ago]
        
        today_count = len(today_df)
        week_count = len(week_df)
        total_count = len(df)

        # 🎯 TOP 3 DATA BOXES
        col1, col2, col3 = st.columns(3)
        
        box_css = """
        {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            border: 1px solid #e6e6e6;
            text-align: center;
        }
        """
        
        with col1:
            with stylable_container(key="metric_today", css_styles=box_css):
                st.markdown(f"<p style='color: #175388; font-weight: bold;'>Today's Violations</p>", unsafe_allow_html=True)
                st.markdown(f"<h2 style='color: #ecb713;'>{today_count}</h2>", unsafe_allow_html=True)

        with col2:
            with stylable_container(key="metric_week", css_styles=box_css):
                st.markdown(f"<p style='color: #175388; font-weight: bold;'>Weekly Total</p>", unsafe_allow_html=True)
                st.markdown(f"<h2 style='color: #ecb713;'>{week_count}</h2>", unsafe_allow_html=True)

        with col3:
            with stylable_container(key="metric_total", css_styles=box_css):
                st.markdown(f"<p style='color: #175388; font-weight: bold;'>System Events</p>", unsafe_allow_html=True)
                st.markdown(f"<h2 style='color: #ecb713;'>{total_count}</h2>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Charts
        c1, c2 = st.columns(2)
        with c1:
            with st.expander("📊 Today's Violation Breakdown", expanded=True):
                if not today_df.empty:
                    fig_today = px.pie(today_df, names="VIOLATION_TYPE", hole=0.5, 
                                      color_discrete_sequence=["#175388", "#ecb713", "#2A7B9B"])
                    st.plotly_chart(fig_today, width='stretch')
                else:
                    st.markdown("<h3 style='text-align: center; color: #28a745; padding: 40px;'>✅ All Good today</h3>", unsafe_allow_html=True)
        
        with c2:
            with st.expander("📈 7-Day Safety Trend", expanded=True):
                if not week_df.empty:
                    daily = week_df.groupby(week_df['TIMESTAMP'].dt.date).size().reset_index(name='COUNT')
                    fig2 = px.bar(daily, x="TIMESTAMP", y="COUNT", color_discrete_sequence=["#175388"])
                    st.plotly_chart(fig2, width='stretch')
                else:
                    st.write("No incidents in the last 7 days.")

        st.subheader("📋 Recent Safety Logs")
        st.dataframe(df.head(15), width='stretch')

# ───────────────────────── PAGE 2: LIVE MONITOR ─────────────────────────
elif selected_page == 'Live Monitor':
    render_banner("🎥 Live Surveillance", "Artificial Intelligence monitoring for Safety Headgear and Visual Protection.")
    
    col_cam, col_info = st.columns([2, 1])
    
    with col_info:
        with stylable_container(key="status_card", css_styles="{background-color: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #ddd;}"):
            st.subheader("Current Protection Status")
            status_ui = st.empty()
            st.divider()
            st.markdown("**Camera:** Workshop-1")
            st.markdown("**Stream Condition:** :green[Optimized]")

    with col_cam:
        video_ui = st.empty()

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        st.error("Error: Camera peripheral not detected.")
    else:
        try:
            while True:
                ret, frame = cap.read()
                if not ret: break
                
                output = monitor.process_frame(frame)
                video_ui.image(cv2.cvtColor(output["annotated_frame"], cv2.COLOR_BGR2RGB), channels="RGB", width='stretch')

                if output["persons"]:
                    p = output["persons"][0]
                    h = "✅ SECURE" if p.get("helmet") else "❌ NO HEADGEAR"
                    g = "✅ SECURE" if p.get("glasses") else "❌ NO EYEWEAR"
                    status_ui.markdown(f"**Safety Headgear:** {h}\n\n**Visual Protection:** {g}")
                else:
                    status_ui.info("Scanning for personnel...")

                if output["new_violations"]:
                    for v in output["new_violations"]:
                        st.session_state.violations_log.append(v.to_dict())
        finally:
            cap.release()