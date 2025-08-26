# src/aarogya_ai/api/main.py

# ==============================================================================
# Aarogya-AI: Main API Endpoint (v3.2 - Definitive)
# ==============================================================================

# --- [Imports] ---
import os, yaml, logging, tempfile
from typing import Dict, Any, List
import uvicorn, pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import ValidationError
import google.generativeai as genai

# --- [Local Imports] ---
from aarogya_ai.data_processing.pipeline import extract_text_from_file
from aarogya_ai.parser import RegexParser, GeminiParser
from aarogya_ai.api.schemas import AnalysisResponse, AnalysisPayload, StructuredData, PatientDetails, TestResult, AnomalyReport
from aarogya_ai.database import operations as db_ops
from aarogya_ai.fraud_detection.rules import find_plausibility_anomalies
from aarogya_ai.fraud_detection.models import find_statistical_anomalies
from aarogya_ai.fraud_detection.validation import perform_cross_report_validation

# --- [Application Setup & Startup] ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app = FastAPI(title="Aarogya-AI API", version="3.2.0")
PARAMS, REGEX_PARSER, GEMINI_PARSER, SUMMARY_MODEL = {}, None, None, None
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
@app.on_event("startup")
def startup_event():
    global PARAMS, REGEX_PARSER, GEMINI_PARSER, SUMMARY_MODEL
    try:
        config_path = os.path.join(PROJECT_ROOT, 'params.yaml');
        with open(config_path, 'r') as f: PARAMS = yaml.safe_load(f)
        db_ops.DB_PATH = os.path.join(PROJECT_ROOT, 'aarogya_ai_data.db'); db_ops.initialize_database()
        credentials_path = os.path.join(PROJECT_ROOT, 'crack-decorator-468911-s1-5ab46e3aea4b.json')
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path; genai.configure(transport='rest')
        REGEX_PARSER = RegexParser(PARAMS.get('regex_patterns', {})); GEMINI_PARSER = GeminiParser(PARAMS.get('llm_parser_config', {}))
        SUMMARY_MODEL = genai.GenerativeModel(PARAMS.get('llm_parser_config', {}).get('model_name', 'gemini-1.5-flash'))
        logging.info("✅ All services initialized successfully.")
    except Exception as e:
        logging.error(f"❌ CRITICAL: Failed to initialize services: {e}", exc_info=True)

# --- [Helper Functions] ---
def adapt_parser_output_to_schema(d):
    d.setdefault('patient_details',{}); d.setdefault('test_results',[])
    for k in ['name','age','sex']:
        if k in d: d['patient_details'][k]=d.pop(k)
    r=[{"test_name":t.get("test_name",t.get("test")),"result":t.get("result"),"unit":t.get("unit"),"reference_range":t.get("reference_range")} for t in d.get('test_results',[]) if isinstance(t,dict)]
    d['test_results']=r; return d
def generate_final_summary(model, structured_data, system_prompt):
    pd=structured_data.get('patient_details',{}); pn=pd.get('name','Valued Patient');
    context_str=f"Patient Name: {pn}\n\nKey Test Results:\n";
    key_tests=["Hemoglobin","RBC","Platelet","WBC","Cholesterol","Triglycerides","HDL","LDL","AST","ALT","Creatinine","Urea","Glucose"]
    ts=[t for t in structured_data.get('test_results',[]) if any(k.lower() in t.get('test_name','').lower() for k in key_tests)];
    if not ts: ts=structured_data.get('test_results',[])[:5]
    for t in ts: context_str+=f"- {t.get('test_name','N/A')}: {t.get('result','N/A')} {t.get('unit','')} (Normal: {t.get('reference_range','N/A')})\n"
    try:
        response=model.generate_content([system_prompt,context_str]); return response.text
    except Exception as e: return f"An error occurred: {e}"

# --- [API Endpoints] ---
@app.get("/", tags=["Status"])
def read_root() -> Dict[str, str]: return {"status": "Aarogya-AI API is running!"}

@app.post("/process_report/", response_model=AnalysisResponse, tags=["Analysis"])
async def process_report(report_file: UploadFile = File(...)):
    if not all([PARAMS, REGEX_PARSER, GEMINI_PARSER, SUMMARY_MODEL]):
        raise HTTPException(status_code=503, detail="Service Unavailable.")
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(report_file.filename)[1]) as tmp:
        tmp.write(await report_file.read()); tmp_path = tmp.name
    try:
        raw_text = extract_text_from_file(tmp_path)
        if not raw_text: raise HTTPException(status_code=400, detail="Could not extract text.")
        structured_data_dict = REGEX_PARSER.parse(raw_text)
        if len(structured_data_dict.get('test_results', [])) < PARAMS['parser_config']['gemini_fallback_threshold']:
            raw_gemini_output = GEMINI_PARSER.parse(raw_text)
            structured_data_dict = adapt_parser_output_to_schema(raw_gemini_output)
        if not structured_data_dict.get('test_results'):
            raise HTTPException(status_code=422, detail="No valid test results could be parsed.")
        structured_data_obj = StructuredData(**structured_data_dict)

        anomaly_report: List[AnomalyReport] = []
        patient_name = structured_data_obj.patient_details.name
        historical_df = db_ops.get_patient_history(patient_name)
        cross_val_flags = perform_cross_report_validation(structured_data_obj.patient_details, historical_df)
        if cross_val_flags:
            anomaly_report.extend([AnomalyReport(**a) for a in cross_val_flags])

        results_df = pd.DataFrame([r.dict() for r in structured_data_obj.test_results])
        if not results_df.empty:
            results_df['result_numeric'] = pd.to_numeric(results_df['result'], errors='coerce')
            clean_results_df = results_df.dropna(subset=['result_numeric'])
            
            plausibility_flags = find_plausibility_anomalies(clean_results_df, PARAMS.get('plausibility_rules', {}))
            for _, row in plausibility_flags.iterrows():
                anomaly_report.append(AnomalyReport(flag_type="Plausibility", test_name=row["Test Name"], result=row["Anomalous Result"], reason=row["Reason"], details=row["Plausible Range"]))

            statistical_flags = find_statistical_anomalies(clean_results_df)
            for _, row in statistical_flags.iterrows():
                anomaly_report.append(AnomalyReport(flag_type="Statistical", test_name=row["Test Name"], result=row["Anomalous Result"], reason=row["Reason"], details=row["Details"]))
        
        summary = generate_final_summary(SUMMARY_MODEL, structured_data_obj.dict(), PARAMS['llm_parser_config']['system_prompt'])
        db_ops.save_analysis_to_db(structured_data_obj.dict(), report_file.filename)

        return AnalysisResponse(
            filename=report_file.filename,
            analysis=AnalysisPayload(
                structured_data=structured_data_obj,
                summary=summary,
                anomaly_report=anomaly_report
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)
        
        
        
        