

# --- [1] Standard Library Imports ---
import os
import yaml
import logging
import tempfile
from typing import Dict, Any

# --- [2] Third-Party Imports ---
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import google.generativeai as genai

# --- [3] Local Application Imports ---
# Correctly importing from sibling and parent packages
from ..data_processing.pipeline import extract_text_from_file
from ..parser import RegexParser, GeminiParser
from .schemas import AnalysisResponse, AnalysisPayload, StructuredData, PatientDetails, TestResult

# --- [4] Application Setup & Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="Aarogya-AI API",
    description="An intelligent API to process, analyze, and summarize medical lab reports.",
    version="1.0.0"
)

# --- [5] Global Objects & Configuration Loading ---
# We define a function to load parameters to avoid global scope issues
def load_app_config():
    try:
        # Assuming params.yaml is in the root directory, two levels up from this file
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'params.yaml')
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.error("❌ CRITICAL: params.yaml not found in the root directory!")
        return {}

params = load_app_config()

# Initialize models and parsers within a startup event for clean separation
@app.on_event("startup")
def startup_event():
    global REGEX_PARSER, GEMINI_PARSER, SUMMARY_MODEL
    try:
        # Assuming the key file is in the root directory
        credentials_path = os.path.join(os.path.dirname(__file__), '..', '..', 'crack-decorator-468911-s1-5ab46e3aea4b.json')
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        genai.configure(transport='rest')
        
        REGEX_PARSER = RegexParser(params.get('regex_patterns', {}))
        GEMINI_PARSER = GeminiParser(params.get('llm_parser_config', {}))
        SUMMARY_MODEL = genai.GenerativeModel(params.get('llm_parser_config', {}).get('model_name', 'gemini-1.5-flash'))
        
        logging.info("✅ Parsers and AI Models initialized successfully.")
    except Exception as e:
        logging.error(f"❌ CRITICAL: Failed to initialize AI models: {e}")
        REGEX_PARSER, GEMINI_PARSER, SUMMARY_MODEL = None, None, None

# --- [6] Helper Functions ---
def format_data_for_summary(structured_data: Dict[str, Any]) -> str:
    """
    Formats structured data into a simple, clean string optimized for the summarization AI.
    """
    patient_details = structured_data.get('patient_details', {})
    patient_name = patient_details.get('name', 'Valued Patient')
    
    # Start with a simple header
    report_text = f"Patient Name: {patient_name}\n\nKey Test Results:\n"
    
    # Filter for a few key tests to keep the summary focused
    key_tests = [
        "Hemoglobin", "RBC Count", "Platelet Count", "WBC Count",
        "Cholesterol", "Triglycerides", "HDL", "LDL",
        "AST", "ALT", "Creatinine", "Urea", "Glucose"
    ]
    
    tests_to_summarize = []
    for test in structured_data.get('test_results', []):
        test_name = test.get('test_name', '')
        if any(key_test.lower() in test_name.lower() for key_test in key_tests):
            tests_to_summarize.append(test)
    
    # If we found key tests, format them. Otherwise, take the first 5.
    if not tests_to_summarize:
        tests_to_summarize = structured_data.get('test_results', [])[:5]

    for test in tests_to_summarize:
        name = test.get('test_name', 'N/A')
        result = test.get('result', 'N/A')
        unit = test.get('unit', '')
        ref_range = test.get('reference_range', 'N/A')
        # This format is cleaner and easier for the AI to understand
        report_text += f"- {name}: {result} {unit} (Normal: {ref_range})\n"
        
    return report_text


# --- [7] API Endpoints ---
@app.get("/")
def read_root() -> Dict[str, str]:
    return {"status": "Aarogya-AI API is running!"}

@app.post("/process_report/", response_model=AnalysisResponse, tags=["Analysis"])
async def process_report(report_file: UploadFile = File(...)) -> AnalysisResponse:
    if not all([REGEX_PARSER, GEMINI_PARSER, SUMMARY_MODEL]):
        raise HTTPException(status_code=503, detail="Service Unavailable: AI models are not initialized.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(report_file.filename)[1]) as tmp:
        tmp.write(await report_file.read())
        tmp_path = tmp.name

    try:
        raw_text = extract_text_from_file(tmp_path)
        if not raw_text or len(raw_text) < 20:
            raise HTTPException(status_code=400, detail="Could not extract sufficient text from the file.")

        structured_data_dict = REGEX_PARSER.parse(raw_text)
        if len(structured_data_dict.get('test_results', [])) < params.get('parser_config', {}).get('gemini_fallback_threshold', 5):
            structured_data_dict = GEMINI_PARSER.parse(raw_text)
        
        summary_prompt_data = format_data_for_summary(structured_data_dict)
        summary = SUMMARY_MODEL.generate_content([
            params.get('llm_parser_config', {}).get('system_prompt', ''),
            summary_prompt_data
        ]).text

        # Assemble the response using Pydantic models
        patient_details_obj = PatientDetails(**structured_data_dict.get('patient_details', {}))
        test_results_list = [TestResult(**test) for test in structured_data_dict.get('test_results', [])]
        
        response_payload = AnalysisResponse(
            filename=report_file.filename,
            analysis=AnalysisPayload(
                structured_data=StructuredData(
                    patient_details=patient_details_obj,
                    test_results=test_results_list
                ),
                summary=summary
            )
        )
        return response_payload

    except Exception as e:
        logging.error(f"An error occurred during processing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")
    finally:
        os.unlink(tmp_path)