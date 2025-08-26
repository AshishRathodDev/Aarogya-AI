# dashboard.py

import streamlit as st
import pandas as pd
import requests
import os
import logging
from typing import Dict, Any

# ==============================================================================
# 1. APPLICATION CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="Aarogya-AI | Medical Intelligence",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- API Endpoint Configuration ---
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", 8000))
API_ENDPOINT = f"http://{API_HOST}:{API_PORT}/process_report/"

# --- Custom CSS for Styling ---
def inject_custom_css():
    st.markdown("""
    <style>
        /* (The beautiful CSS is preserved here) */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; color: #FFFFFF !important; }
        h1, h2, h3, h4, h5, h6 { color: #FFFFFF !important; font-family: 'Inter', sans-serif !important; font-weight: 600 !important; }
        #MainMenu, footer, header { visibility: hidden; }
        .stApp { background: linear-gradient(135deg, #0c0c1d 0%, #1a1a2e 50%, #16213e 100%); }
        .main .block-container { max-width: 1000px; padding: 2rem; background: rgba(22, 33, 62, 0.6); backdrop-filter: blur(12px); border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.1); margin-top: 2rem; }
        .app-header h1 { font-size: 3rem !important; background: linear-gradient(135deg, #00BFFF, #FFFFFF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .stTabs [aria-selected="true"] { background: rgba(0, 191, 255, 0.2) !important; border-color: #00BFFF !important; color: #00BFFF !important; }
        .stButton > button { background: linear-gradient(135deg, #00BFFF, #0080FF); color: white; border: none; border-radius: 25px; padding: 0.5rem 2rem; font-weight: 600; }
        .st-emotion-cache-1r6slb0 { border-color: rgba(255, 193, 7, 0.8) !important; } /* For st.warning border */
        .st-emotion-cache-l4x8s5 { border-color: rgba(0, 191, 255, 0.8) !important; } /* For st.info border */
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. CORE LOGIC FUNCTIONS
# ==============================================================================

@st.cache_data(show_spinner=False)
def analyze_report(uploaded_file) -> Dict[str, Any]:
    """Sends the file to the backend API and returns the analysis."""
    try:
        files = {'report_file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        response = requests.post(API_ENDPOINT, files=files, timeout=300)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": "ConnectionError", "detail": str(e)}

def display_patient_view(analysis: Dict[str, Any]):
    """Renders the patient-friendly summary view."""
    st.subheader("📋 Patient-Friendly Summary")
    summary = analysis.get('summary', 'Summary could not be generated.')
    st.markdown(summary)
    with st.expander("🔬 View Detailed Test Results"):
        st.dataframe(pd.DataFrame(analysis.get('structured_data', {}).get('test_results', [])), use_container_width=True)

def display_insurer_view(analysis: Dict[str, Any]):
    """
    [UPGRADED] Renders the investigator view with both Plausibility and Statistical flags.
    """
    st.subheader("🕵️‍♂️ Insurer & Investigator View")
    
    anomalies = analysis.get('anomaly_report', [])
    plausibility_flags = [a for a in anomalies if a.get('flag_type') == 'Plausibility']
    statistical_flags = [a for a in anomalies if a.get('flag_type') == 'Statistical']
    
    # --- The Verdict ---
    if anomalies:
        st.error(f"**Status: Suspicious Report** - Found {len(plausibility_flags)} plausibility flag(s) and {len(statistical_flags)} statistical outlier(s).")
    else:
        st.success("**Status: Report Appears Clean** - No anomalies were flagged.")
    st.markdown("---")
    
    # --- The Evidence ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("####  रूल-आधारित फ़्लैग (The Sentry)") # Rule-Based Flags
        if plausibility_flags:
            for flag in plausibility_flags:
                with st.container(border=True):
                    st.warning(f"**{flag.get('reason')}**")
                    st.metric(label=flag.get('test_name', 'N/A'), value=str(flag.get('result', 'N/A')))
                    st.caption(f"Details: {flag.get('details', 'N/A')}")
        else:
            st.write("No plausibility flags detected.")

    with col2:
        st.markdown("#### सांख्यिकीय आउटलायर (AI Detective)") # Statistical Outliers
        if statistical_flags:
            for flag in statistical_flags:
                with st.container(border=True):
                    st.info(f"**{flag.get('reason')}**")
                    st.metric(label=flag.get('test_name', 'N/A'), value=str(flag.get('result', 'N/A')))
                    st.caption(f"Details: {flag.get('details', 'N/A')}")
        else:
            st.write("No statistical outliers detected.")

    with st.expander("📄 View Full Extracted JSON"):
        st.json(analysis.get('structured_data', {}))

# ==============================================================================
# 3. MAIN APPLICATION UI
# ==============================================================================

def main():
    """Main function to run the dashboard."""
    inject_custom_css()
    
    st.markdown('<div class="app-header"><h1>🤖 Aarogya-AI</h1><p>Intelligent Medical Report Analysis</p></div>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload Your Medical Report", type=['pdf', 'png', 'jpg', 'jpeg'], label_visibility="collapsed")
    
    if uploaded_file:
        with st.spinner("🔄 Analyzing your report with AI... This may take a moment..."):
            api_data = analyze_report(uploaded_file)
        
        if "error" in api_data:
            st.error(f"**Analysis Failed:** Could not connect to the server.")
            st.caption(f"Details: {api_data['detail']}")
        else:
            st.success("✅ Analysis Complete!")
            analysis_payload = api_data.get('analysis', {})
            
            st.header("2. Your Report Analysis")
            patient_tab, insurer_tab = st.tabs(["👤 Patient View", "🏥 Insurer View"])
            with patient_tab:
                display_patient_view(analysis_payload)
            with insurer_tab:
                display_insurer_view(analysis_payload)
    else:
        st.info("Please upload a medical report to begin analysis.")

if __name__ == "__main__":
    main()
    
    
    