# --- [Imports] ---
import os
import yaml
import logging
import tempfile
import time
from typing import Dict, Any, List
import uvicorn
import pandas as pd
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
app = FastAPI(title="Aarogya-AI API", version="3.5.0", description="Intelligent Medical Report Analysis")
PARAMS, REGEX_PARSER, GEMINI_PARSER, SUMMARY_MODEL = {}, None, None, None

@app.on_event("startup")
def startup_event():
    """Initialize config, DB, and AI models for Cloud Run."""
    global PARAMS, REGEX_PARSER, GEMINI_PARSER, SUMMARY_MODEL
    try:
        logging.info("🚀 Starting Aarogya-AI API initialization...")
        
        # Load config
        config_path = "/app/params.yaml"
        logging.info(f"Loading config from: {config_path}")
        
        if not os.path.exists(config_path):
            logging.warning(f"Config file not found: {config_path}, using defaults")
            PARAMS = {"regex_patterns": {}, "llm_parser_config": {}}
        else:
            with open(config_path, 'r') as f:
                PARAMS = yaml.safe_load(f)
            logging.info("✅ Config loaded successfully")
        
        # Database setup with error handling
        try:
            db_ops.DB_PATH = "/app/aarogya_ai_data.db"
            db_ops.initialize_database()
            logging.info("✅ Database initialized successfully")
        except Exception as e:
            logging.error(f"❌ Database initialization failed: {e}")
            # Continue without database for basic functionality
        
        # Google AI setup with error handling
        try:
            credentials_path = "/app/crack-decorator-468911-s1-5ab46e3aea4b.json"
            if os.path.exists(credentials_path):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
                logging.info("✅ Service account credentials loaded")
            elif os.getenv("GOOGLE_API_KEY"):
                genai.configure(api_key=os.getenv("GOOGLE_API_KEY"), transport="rest")
                logging.info("✅ Using API key for Google AI")
            else:
                logging.warning("⚠️ No Google AI credentials found")
            
            genai.configure(transport="rest")
            logging.info("✅ Google AI configured")
        except Exception as e:
            logging.error(f"❌ Google AI setup failed: {e}")
            # Continue without AI for basic functionality
        
        # Initialize parsers with error handling
        try:
            REGEX_PARSER = RegexParser(PARAMS.get('regex_patterns', {}))
            GEMINI_PARSER = GeminiParser(PARAMS.get('llm_parser_config', {}))
            SUMMARY_MODEL = genai.GenerativeModel('gemini-1.5-flash')
            logging.info("✅ Parsers initialized successfully")
        except Exception as e:
            logging.error(f"❌ Parser initialization failed: {e}")
            # Set None values for graceful degradation
            REGEX_PARSER = None
            GEMINI_PARSER = None
            SUMMARY_MODEL = None
        
        logging.info("🎉 API initialization completed")
        
    except Exception as e:
        logging.error(f"❌ CRITICAL: Startup failed: {e}", exc_info=True)
        # Don't raise exception - let app start in degraded mode

# --- [Helper Functions] ---
def adapt_parser_output_to_schema(d: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize parser output to schema."""
    d.setdefault('patient_details', {})
    d.setdefault('test_results', [])
    
    # Move top-level patient fields to patient_details
    for k in ['name', 'age', 'sex']:
        if k in d:
            d['patient_details'][k] = d.pop(k)
    
    # Normalize test results
    normalized_results = []
    for t in d.get('test_results', []):
        if isinstance(t, dict):
            normalized_results.append({
                "test_name": t.get("test_name", t.get("test", "Unknown Test")),
                "result": t.get("result", "N/A"),
                "unit": t.get("unit", ""),
                "reference_range": t.get("reference_range", "N/A")
            })
    
    d['test_results'] = normalized_results
    return d

def generate_final_summary(structured_data: Dict[str, Any]) -> str:
    """Generate patient-friendly summary with fallback."""
    try:
        if not SUMMARY_MODEL:
            return generate_simple_summary(structured_data)
        
        patient_details = structured_data.get('patient_details', {})
        patient_name = patient_details.get('name', 'Patient')
        test_results = structured_data.get('test_results', [])
        
        if not test_results:
            return "No test results were available to generate a summary."
        
        # Try AI summary
        context_str = f"Patient: {patient_name}\n\nTest Results:\n"
        for test in test_results[:10]:  # Limit to first 10 tests
            test_name = test.get('test_name', 'Unknown')
            result = test.get('result', 'N/A')
            unit = test.get('unit', '')
            ref_range = test.get('reference_range', 'N/A')
            context_str += f"- {test_name}: {result} {unit} (Normal: {ref_range})\n"
        
        system_prompt = "Generate a patient-friendly medical report summary. Be reassuring and informative."
        response = SUMMARY_MODEL.generate_content([system_prompt, context_str])
        
        if response and hasattr(response, 'text') and response.text:
            return response.text
        else:
            return generate_simple_summary(structured_data)
            
    except Exception as e:
        logging.error(f"AI summary generation failed: {e}")
        return generate_simple_summary(structured_data)

def generate_simple_summary(structured_data: Dict[str, Any]) -> str:
    """Generate basic summary without AI."""
    patient_details = structured_data.get('patient_details', {})
    test_results = structured_data.get('test_results', [])
    
    patient_name = patient_details.get('name', 'Patient')
    num_tests = len(test_results)
    
    if num_tests == 0:
        return f"Report processed for {patient_name}. No test results were found in the document."
    
    summary = f"Medical Report Summary for {patient_name}\n\n"
    summary += f"Total tests analyzed: {num_tests}\n\n"
    
    summary += "Key Test Results:\n"
    for test in test_results[:5]:  # Show first 5 tests
        test_name = test.get('test_name', 'Unknown Test')
        result = test.get('result', 'N/A')
        unit = test.get('unit', '')
        summary += f"• {test_name}: {result} {unit}\n"
    
    if num_tests > 5:
        summary += f"• ... and {num_tests - 5} more tests\n"
    
    summary += "\n**Disclaimer:** This is an AI-generated summary and not a substitute for professional medical advice. Please consult with your doctor to discuss your results in detail."
    
    return summary

# --- [API Endpoints] ---
@app.get("/", tags=["Status"])
def read_root() -> Dict[str, str]:
    """Root endpoint with basic API information."""
    return {
        "status": "Aarogya-AI API is running!",
        "version": "3.5.0",
        "timestamp": time.time(),
        "description": "Intelligent Medical Report Analysis API"
    }

@app.get("/health", tags=["Status"])  
def health_check():
    """Detailed health check for Cloud Run."""
    return {
        "status": "healthy",
        "service": "aarogya-ai-api",
        "timestamp": time.time(),
        "version": "3.5.0",
        "components": {
            "params_loaded": PARAMS is not None and len(PARAMS) > 0,
            "regex_parser": REGEX_PARSER is not None,
            "gemini_parser": GEMINI_PARSER is not None,
            "summary_model": SUMMARY_MODEL is not None,
            "database": hasattr(db_ops, 'DB_PATH')
        }
    }

@app.get("/healthz", tags=["Status"])
def health_check_simple():
    """Simple health check for Cloud Run."""
    return {"status": "ok"}

@app.post("/process_report/", response_model=AnalysisResponse, tags=["Analysis"])
async def process_report(report_file: UploadFile = File(...)):
    """
    Analyze uploaded medical report and return structured data + AI summary.
    
    FIXED VERSION: Proper file handling to prevent empty file errors.
    """
    
    # Validate file upload
    if not report_file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file extension
    allowed_extensions = ['.pdf', '.png', '.jpg', '.jpeg']
    file_ext = os.path.splitext(report_file.filename.lower())[1]
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Read and validate file content
    try:
        file_content = await report_file.read()
        file_size = len(file_content)
        
        logging.info(f"📁 Received file: {report_file.filename}, size: {file_size:,} bytes")
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        if file_size > 200 * 1024 * 1024:  # 200MB limit
            raise HTTPException(status_code=400, detail="File too large (max 200MB)")
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error reading uploaded file: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {str(e)}")
    
    # Create temporary file with proper content writing
    tmp_path = None
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            # Write content and flush to ensure it's written to disk
            tmp.write(file_content)
            tmp.flush()
            os.fsync(tmp.fileno())  # Force write to disk
            tmp_path = tmp.name
        
        # Verify file was written correctly
        if not os.path.exists(tmp_path):
            raise HTTPException(status_code=500, detail="Failed to create temporary file")
        
        temp_file_size = os.path.getsize(tmp_path)
        if temp_file_size == 0:
            raise HTTPException(status_code=500, detail="Temporary file is empty")
        
        logging.info(f"✅ Temporary file created: {tmp_path}, size: {temp_file_size:,} bytes")
        
        # Extract text from file
        try:
            raw_text = extract_text_from_file(tmp_path)
            
            if not raw_text or len(raw_text.strip()) == 0:
                raise HTTPException(
                    status_code=422, 
                    detail="Could not extract meaningful text from the file. Please ensure the file contains readable medical data."
                )
            
            logging.info(f"✅ Text extracted successfully: {len(raw_text)} characters")
            
        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"Text extraction failed: {e}")
            raise HTTPException(
                status_code=422, 
                detail=f"Failed to extract text from file: {str(e)}"
            )
        
        # Parse extracted text
        structured_data_dict = {"patient_details": {}, "test_results": []}
        
        try:
            # Try regex parsing first
            if REGEX_PARSER:
                structured_data_dict = REGEX_PARSER.parse(raw_text)
                logging.info(f"Regex parser found {len(structured_data_dict.get('test_results', []))} test results")
            
            # Fallback to Gemini if insufficient results
            fallback_threshold = PARAMS.get('parser_config', {}).get('gemini_fallback_threshold', 5)
            if len(structured_data_dict.get('test_results', [])) < fallback_threshold and GEMINI_PARSER:
                try:
                    logging.info("Trying Gemini parser for better results...")
                    raw_gemini_output = GEMINI_PARSER.parse(raw_text)
                    structured_data_dict = adapt_parser_output_to_schema(raw_gemini_output)
                    logging.info(f"Gemini parser found {len(structured_data_dict.get('test_results', []))} test results")
                except Exception as e:
                    logging.warning(f"Gemini parsing failed, using regex results: {e}")
            
            # If still no results, create basic structure
            if not structured_data_dict.get('test_results'):
                logging.info("No test results found, creating basic structure")
                structured_data_dict = {
                    "patient_details": {"name": "Unknown Patient"},
                    "test_results": [
                        {
                            "test_name": "Document Analysis",
                            "result": "Processed",
                            "unit": "",
                            "reference_range": "N/A"
                        }
                    ]
                }
                
        except Exception as e:
            logging.error(f"Parsing failed: {e}")
            # Create minimal valid structure
            structured_data_dict = {
                "patient_details": {"name": "Unknown Patient"},
                "test_results": [
                    {
                        "test_name": "Processing Error",
                        "result": "Failed to parse",
                        "unit": "",
                        "reference_range": "N/A"
                    }
                ]
            }
        
        # Create structured data object
        try:
            structured_data_obj = StructuredData(**structured_data_dict)
        except ValidationError as e:
            logging.error(f"Data validation failed: {e}")
            raise HTTPException(status_code=422, detail=f"Data validation failed: {str(e)}")
        
        # Initialize anomaly report (basic version for now)
        anomaly_report: List[AnomalyReport] = []
        
        # Try anomaly detection with error handling
        try:
            results_df = pd.DataFrame([r.dict() for r in structured_data_obj.test_results])
            if not results_df.empty:
                results_df['result_numeric'] = pd.to_numeric(results_df['result'], errors='coerce')
                clean_results_df = results_df.dropna(subset=['result_numeric'])
                
                if not clean_results_df.empty and PARAMS.get('plausibility_rules'):
                    plausibility_flags = find_plausibility_anomalies(
                        clean_results_df, 
                        PARAMS.get('plausibility_rules', {})
                    )
                    for _, row in plausibility_flags.iterrows():
                        anomaly_report.append(AnomalyReport(
                            flag_type="Plausibility",
                            test_name=row["Test Name"],
                            result=str(row["Anomalous Result"]),
                            reason=row["Reason"],
                            details=row["Plausible Range"]
                        ))
                    
                    logging.info(f"Found {len(plausibility_flags)} plausibility anomalies")
                    
        except Exception as e:
            logging.warning(f"Anomaly detection failed: {e}")
        
        # Generate summary
        try:
            summary = generate_final_summary(structured_data_obj.dict())
            logging.info("✅ Summary generated successfully")
        except Exception as e:
            logging.error(f"Summary generation failed: {e}")
            summary = "Summary generation failed. Please consult your healthcare provider for result interpretation."
        
        # Save to database (if available)
        try:
            if hasattr(db_ops, 'save_analysis_to_db'):
                db_ops.save_analysis_to_db(structured_data_obj.dict(), report_file.filename)
                logging.info("✅ Analysis saved to database")
        except Exception as e:
            logging.warning(f"Database save failed: {e}")
        
        logging.info(f"🎉 Successfully processed report: {report_file.filename}")
        
        # Return successful response
        return AnalysisResponse(
            filename=report_file.filename,
            analysis=AnalysisPayload(
                structured_data=structured_data_obj,
                summary=summary,
                anomaly_report=anomaly_report
            )
        )
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logging.error(f"Unexpected error in process_report: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
                logging.info(f"🗑️ Cleaned up temporary file: {tmp_path}")
            except Exception as e:
                logging.warning(f"Failed to clean up temp file: {e}")

# Test endpoint for file upload debugging
@app.post("/test_upload/", tags=["Testing"])
async def test_upload(report_file: UploadFile = File(...)):
    """Test endpoint to verify file upload functionality."""
    try:
        content = await report_file.read()
        return {
            "filename": report_file.filename,
            "content_type": report_file.content_type,
            "size": len(content),
            "status": "upload_successful",
            "first_bytes": content[:100].hex() if content else "empty"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Upload test failed: {str(e)}")

if __name__ == "__main__":
    # For local testing only
    port = int(os.environ.get("PORT", 8000))
    logging.info(f"Starting server on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
    