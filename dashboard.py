import streamlit as st
import requests
import pandas as pd
import os
import logging

# ==============================================================================
# Application Configuration
# ==============================================================================
st.set_page_config(
    page_title="Aarogya-AI: Intelligent Report Analyzer",
    page_icon="🤖",
    layout="wide"
)

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- API Endpoint Configuration ---
# This is the address of our FastAPI server.
# It checks for an environment variable first, which is best practice for deployment.
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", 8000))
API_ENDPOINT = f"http://{API_HOST}:{API_PORT}/process_report/"

# ==============================================================================
# Main Application UI
# ==============================================================================

# --- Header Section ---
st.title("🤖 Aarogya-AI: Intelligent Medical Report Analyzer")
st.markdown("""
Welcome! This tool uses advanced AI to help you understand your medical reports.
Just upload your report (PDF or Image), and our system will extract the key information
and provide a simple, easy-to-understand summary.
""")
st.info(f"**API Status:** Attempting to connect to the backend server at `{API_ENDPOINT}`")

# --- File Uploader ---
st.header("1. Upload Your Medical Report")
uploaded_file = st.file_uploader(
    "Choose a file (PDF, JPG, PNG)",
    type=['pdf', 'jpg', 'png', 'jpeg']
)

# --- Processing and Result Display ---
if uploaded_file is not None:
    logging.info(f"File uploaded: {uploaded_file.name}")
    st.info("File uploaded successfully. Processing with Aarogya-AI...")

    with st.spinner('AI is reading and analyzing your report... This may take a moment.'):
        try:
            files = {'report_file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            response = requests.post(API_ENDPOINT, files=files, timeout=300)
            
            if response.status_code == 200:
                st.success("Analysis Complete!")
                api_data = response.json()
                analysis = api_data.get('analysis', {})
                
                # --- NEW: Display Results in a clean, two-column layout ---
                st.header("2. Your Report Analysis")
                
                # Create two columns
                col1, col2 = st.columns(2)

                # Column 1: AI-Generated Summary
                with col1:
                    st.subheader("📋 Patient-Friendly Summary")
                    summary = analysis.get('summary', 'Summary could not be generated.')
                    st.markdown(summary)

                # Column 2: Key Extracted Data
                with col2:
                    st.subheader("🔬 Key Extracted Data")
                    structured_data = analysis.get('structured_data', {})
                    
                    patient_details = structured_data.get('patient_details', {})
                    if patient_details.get('name'):
                        st.write(f"**Patient Name:** {patient_details['name']}")
                    if patient_details.get('age'):
                        st.write(f"**Age:** {patient_details['age']}")
                    if patient_details.get('sex'):
                        st.write(f"**Sex:** {patient_details['sex']}")
                    
                    st.markdown("---") # A separator line
                    
                    test_results = structured_data.get('test_results', [])
                    if test_results:
                        df_results = pd.DataFrame(test_results)
                        # Displaying only the most important columns in a cleaner way
                        st.dataframe(df_results[['test_name', 'result', 'unit', 'reference_range']])
                    else:
                        st.write("No structured test results were extracted.")
            else:
                st.error(f"Analysis Failed. (Status Code: {response.status_code})")
                st.json(response.json())

        except requests.exceptions.RequestException as e:
            st.error(f"**Connection Error:** Could not connect to the API server. Error: {e}")
            
            
            