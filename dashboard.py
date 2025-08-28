

import streamlit as st
import pandas as pd
import requests
import os
import logging
import json
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


API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
API_ENDPOINT = f"{API_BASE_URL}/process_report/"

# --- Custom CSS for Styling ---
def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; color: #FFFFFF !important; }
        .stApp { background: linear-gradient(135deg, #0c0c1d 0%, #1a1a2e 50%, #16213e 100%); }
        #MainMenu, footer, header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. CORE LOGIC FUNCTIONS
# ==============================================================================

def analyze_report(uploaded_file) -> Dict[str, Any]:
    """Sends the file to the backend API and returns the analysis."""
    try:
        # Read file content with proper validation
        file_content = uploaded_file.getvalue()
        
        # Validate file content
        if not file_content or len(file_content) == 0:
            return {
                "error": "EmptyFile",
                "detail": "The uploaded file appears to be empty. Please try uploading a different file."
            }
        
        st.success(f"✅ File loaded: {len(file_content):,} bytes")
        
        # Log the API endpoint
        st.info(f"🔗 Connecting to: {API_ENDPOINT}")
        
        # Prepare files for multipart upload
        files = {
            'report_file': (
                uploaded_file.name,
                file_content,
                uploaded_file.type or 'application/pdf'
            )
        }
        
        # Send request with proper error handling
        with st.spinner("🔄 Uploading and processing file..."):
            response = requests.post(
                API_ENDPOINT,
                files=files,
                timeout=300
            )
        
        st.info(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            error_detail = response.json().get('detail', 'Bad request')
            return {
                "error": "BadRequest",
                "detail": f"File processing error: {error_detail}"
            }
        elif response.status_code == 422:
            error_detail = response.json().get('detail', 'Validation error')
            return {
                "error": "ValidationError", 
                "detail": f"Data validation failed: {error_detail}"
            }
        elif response.status_code == 500:
            return {
                "error": "ServerError",
                "detail": "Internal server error. The server encountered an issue processing your request."
            }
        else:
            return {
                "error": f"HTTP_{response.status_code}",
                "detail": f"Server returned {response.status_code}: {response.text[:200]}"
            }
            
    except requests.exceptions.ConnectionError as e:
        return {
            "error": "ConnectionError", 
            "detail": f"Could not connect to API server. Please check if the service is running."
        }
    except requests.exceptions.Timeout as e:
        return {
            "error": "TimeoutError",
            "detail": "Request timed out. The file might be too large or the server is busy. Please try again."
        }
    except Exception as e:
        return {
            "error": "UnexpectedError",
            "detail": f"An unexpected error occurred: {str(e)}"
        }

def display_patient_view(analysis: Dict[str, Any]):
    """Renders the patient-friendly summary view."""
    st.markdown("### 📋 Patient-Friendly Summary")
    
    # Get structured data
    structured_data = analysis.get('structured_data', {})
    patient_details = structured_data.get('patient_details', {})
    
    # Display patient info if available
    if patient_details:
        col1, col2, col3 = st.columns(3)
        if patient_details.get('name'):
            col1.metric("Patient Name", patient_details['name'])
        if patient_details.get('age'):
            col2.metric("Age", patient_details['age'])
        if patient_details.get('sex'):
            col3.metric("Gender", patient_details['sex'])
        st.divider()
    
    # Display AI summary
    summary = analysis.get('summary', 'Summary could not be generated.')
    st.markdown("**AI Analysis Summary:**")
    st.markdown(summary)
    
    # Display test results
    test_results = structured_data.get('test_results', [])
    if test_results:
        st.markdown("### 🔬 Detailed Test Results")
        df = pd.DataFrame(test_results)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No test results found in the report.")

def display_insurer_view(analysis: Dict[str, Any]):
    """Renders the investigator view with anomaly flags."""
    st.markdown("### 🕵️‍♂️ Professional Analysis View")
    
    anomalies = analysis.get('anomaly_report', [])
    
    if anomalies:
        st.error(f"🚨 **ALERT: {len(anomalies)} Anomalies Detected**")
        
        for i, alert in enumerate(anomalies, 1):
            with st.expander(f"🚩 Anomaly #{i}: {alert.get('test_name', 'Unknown')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Flag Type:** {alert.get('flag_type', 'Unknown')}")
                    st.markdown(f"**Test Name:** {alert.get('test_name', 'N/A')}")
                    st.markdown(f"**Result:** {alert.get('result', 'N/A')}")
                
                with col2:
                    st.markdown(f"**Reason:** {alert.get('reason', 'N/A')}")
                    st.markdown(f"**Details:** {alert.get('details', 'N/A')}")
    else:
        st.success("✅ **Report Status: CLEAN** - No anomalies detected")
    
    # Show full extracted data
    with st.expander("📄 Complete Extracted Data (JSON)"):
        structured_data = analysis.get('structured_data', {})
        st.json(structured_data)

# ==============================================================================
# 3. MAIN APPLICATION UI
# ==============================================================================

def main():
    """Main function to run the dashboard."""
    inject_custom_css()
    
    # Header
    st.markdown("# 🤖 Aarogya-AI: Intelligent Medical Report Analysis")
    st.markdown("Upload your medical report for AI-powered analysis and fraud detection.")
    
    # API Status in sidebar
    with st.sidebar:
        st.markdown("### 🔧 System Status")
        st.markdown(f"**API Endpoint:** {API_ENDPOINT}")
        
        try:
            test_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if test_response.status_code == 200:
                st.success("✅ API Connected")
                health_data = test_response.json()
                st.markdown(f"**Service:** {health_data.get('service', 'Unknown')}")
                st.markdown(f"**Status:** {health_data.get('status', 'Unknown')}")
            else:
                st.warning(f"⚠️ API Issue ({test_response.status_code})")
        except:
            st.error("❌ API Disconnected")
    
    # File Upload Section
    st.markdown("### 📁 Upload Medical Report")
    uploaded_file = st.file_uploader(
        "Choose a medical report file",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        help="Supported formats: PDF, PNG, JPG, JPEG (Max size: 200MB)",
        key="file_uploader"
    )
    
    if uploaded_file:
        # Display file info
        file_size = len(uploaded_file.getvalue())
        st.success(f"📄 **File Selected:** {uploaded_file.name}")
        st.info(f"**Size:** {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        st.info(f"**Type:** {uploaded_file.type}")
        
        # Analysis section
        col1, col2 = st.columns([1, 3])
        
        with col1:
            analyze_button = st.button("🚀 Analyze Report", type="primary", use_container_width=True)
        
        with col2:
            if analyze_button:
                st.info("⏳ Processing... This may take 1-2 minutes for large files.")
        
        # Process file when button clicked
        if analyze_button:
            # Analyze the report
            api_data = analyze_report(uploaded_file)
            
            # Handle results
            if "error" in api_data:
                st.error("❌ **Analysis Failed**")
                
                error_type = api_data.get("error", "Unknown")
                error_detail = api_data.get("detail", "No details available")
                
                st.markdown(f"**Error Type:** {error_type}")
                st.markdown(f"**Details:** {error_detail}")
                
                # Specific troubleshooting based on error type
                if error_type == "EmptyFile":
                    st.warning("**Solution:** Please ensure the file contains data and try uploading again.")
                elif error_type == "BadRequest":
                    st.warning("**Solution:** Check if the file format is supported (PDF, PNG, JPG, JPEG) and contains readable medical data.")
                elif error_type == "ServerError":
                    st.warning("**Solution:** Server issue detected. Please try again in a few minutes.")
                elif error_type == "ConnectionError":
                    st.warning("**Solution:** Network connectivity issue. Please check your internet connection.")
                
                with st.expander("🛠️ General Troubleshooting"):
                    st.markdown("""
                    **Common Solutions:**
                    1. **File Size:** Ensure file is under 200MB
                    2. **File Format:** Use PDF, PNG, JPG, or JPEG only
                    3. **File Content:** File should contain readable medical report data
                    4. **Network:** Check internet connection
                    5. **Server:** If server error, try again in 1-2 minutes
                    """)
            else:
                st.success("✅ **Analysis Complete!**")
                
                # Get analysis data
                analysis_payload = api_data.get('analysis', {})
                
                # Create tabs for different views
                patient_tab, professional_tab = st.tabs(["👤 Patient View", "🏥 Professional View"])
                
                with patient_tab:
                    display_patient_view(analysis_payload)
                
                with professional_tab:
                    display_insurer_view(analysis_payload)
                
                # Download option
                st.markdown("---")
                st.markdown("### 📥 Download Results")
                
                # Create download data
                download_data = json.dumps(api_data, indent=2)
                timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
                
                st.download_button(
                    label="📄 Download Analysis Report (JSON)",
                    data=download_data,
                    file_name=f"aarogya_analysis_{timestamp}.json",
                    mime="application/json",
                    use_container_width=True
                )
    else:
        # Instructions when no file uploaded
        st.markdown("### 📋 How to Use:")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Steps:**
            1. 📁 Upload a medical report file
            2. 🚀 Click "Analyze Report"
            3. 👀 View results in Patient/Professional tabs
            4. 📥 Download analysis if needed
            """)
        
        with col2:
            st.markdown("""
            **Supported Files:**
            - 📄 PDF reports
            - 🖼️ PNG/JPG images
            - 📏 Up to 200MB size
            - 🏥 Medical test reports
            """)
        
        st.info("🔒 **Privacy:** Files are processed securely and not stored permanently.")

if __name__ == "__main__":
    main()
    