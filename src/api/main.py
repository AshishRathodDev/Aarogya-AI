# --- [1] Standard Library Imports ---
import os
import yaml
import json
import logging
import tempfile
from typing import Dict, Any

# --- [2] Third-Party Imports ---
import pandas as pd
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import google.generativeai as genai


# --- [3] Local Application Imports ---
# This is how we connect our logic from other files.
# We assume the script is run from the root 'Aarogya-AI' directory.
from src.data_processing.pipeline import extract_text_from_file
from src.parser import RegexParser, GeminiParser


# --- [4] Application Setup & Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="Aarogya-AI API",
    description="An intelligent API to process, analyze, and summarize medical lab reports.",
    version="1.0.0"
)


# --- [5] Global Objects & Configuration Loading ---
# Load all configurations from params.yaml at startup.
try:
    with open('params.yaml', 'r') as f:
        params = yaml.safe_load(f)
    logging.info("✅ Configuration from params.yaml loaded successfully.")
except FileNotFoundError:
    logging.error("❌ CRITICAL: params.yaml not found! The application cannot start.")
    params = {} # Set to empty dict to avoid crashing, but endpoints will fail.

# Initialize AI models and parsers at startup to avoid re-initializing on every request.
try:
    CREDENTIALS_FILE = 'crack-decorator-468911-s1-5ab46e3aea4b.json' # Hardcoded for now
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDENTIALS_FILE
    genai.configure(transport='rest')
    
    REGEX_PARSER = RegexParser(params.get('regex_patterns', {}))
    GEMINI_PARSER = GeminiParser(params.get('llm_parser_config', {}))
    
    # Initialize the Gemini Model for summarization
    SUMMARY_MODEL = genai.GenerativeModel(params.get('llm_parser_config', {}).get('model_name', 'gemini-1.5-flash'))
    
    logging.info("✅ Parsers and AI Models initialized successfully.")
except Exception as e:
    logging.error(f"❌ CRITICAL: Failed to initialize AI models: {e}")
    REGEX_PARSER, GEMINI_PARSER, SUMMARY_MODEL = None, None, None
    
    

# --- [6] Helper Functions ---
def format_data_for_summary(structured_data: Dict[str, Any]) -> str:
    """Formats structured data into a simple string for the summarization prompt."""
    patient_details = structured_data.get('patient_details', {})
    patient_name = patient_details.get('name', 'Valued Patient')
    
    report_text = f"Patient Name: {patient_name}\n\nTest Results:\n"
    
    for test in structured_data.get('test_results', []):
        name = test.get('test_name', 'N/A')
        result = test.get('result', 'N/A')
        unit = test.get('unit', '')
        ref_range = test.get('reference_range', 'N/A')
        report_text += f"- {name}: {result} {unit} (Normal Range: {ref_range})\n"
        
    return report_text


# --- [7] API Endpoints ---
@app.get("/")
def read_root():
    return {"status": "Aarogya-AI API is running!"}

@app.post("/process_report/", response_class=JSONResponse)
async def process_report(report_file: UploadFile = File(...)):
    """
    Processes a medical report and returns a full analysis including structured data and a summary.
    """
    if not all([REGEX_PARSER, GEMINI_PARSER, SUMMARY_MODEL]):
        raise HTTPException(status_code=500, detail="Internal Server Error: AI models are not initialized.")

    # Use a temporary file to save the upload, which is a robust way to handle files.
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(report_file.filename)[1]) as tmp:
        tmp.write(await report_file.read())
        tmp_path = tmp.name

    try:
        logging.info(f"--- [Station 1] Starting text extraction from {report_file.filename} ---")
        raw_text = extract_text_from_file(tmp_path)
        if not raw_text or len(raw_text) < 20:
            raise HTTPException(status_code=400, detail="Could not extract sufficient text from the file.")

        logging.info("--- [Station 2] Starting hybrid parsing... ---")
        structured_data = REGEX_PARSER.parse(raw_text)
        if len(structured_data.get('test_results', [])) < params.get('parser_config', {}).get('gemini_fallback_threshold', 5):
            logging.info("Regex parsing insufficient, escalating to Gemini parser.")
            structured_data = GEMINI_PARSER.parse(raw_text)
        
        logging.info("--- [Station 4] Starting summary generation... ---")
        summary_prompt_data = format_data_for_summary(structured_data)
        summary = SUMMARY_MODEL.generate_content([
            params.get('llm_parser_config', {}).get('system_prompt', ''),
            summary_prompt_data
        ]).text

        # Prepare the final response
        final_response = {
            "filename": report_file.filename,
            "analysis": {
                "structured_data": structured_data,
                "summary": summary
                # Station 3 (Anomaly Detection) can be added here as the next step
            }
        }
        return JSONResponse(content=final_response, status_code=200)

    except Exception as e:
        logging.error(f"An error occurred during processing: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")
    finally:
        # Clean up the temporary file
        os.unlink(tmp_path)



