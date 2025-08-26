from pydantic import BaseModel, Field
from typing import List, Optional, Any

# ==============================================================================
# API Schemas (The Rulebook)
# ==============================================================================

class TestResult(BaseModel):
    """Defines the structure for a single medical test result."""
    test_name: str = Field(..., description="Name of the medical test.", example="Hemoglobin")
    result: Any = Field(..., description="The result value of the test.", example=15.2)
    unit: Optional[str] = Field(None, description="Unit of measurement.", example="g/dL")
    reference_range: Optional[str] = Field(None, description="The normal range for the test.", example="13.0-17.0")

class PatientDetails(BaseModel):
    """Defines the structure for patient demographic information."""
    name: Optional[str] = Field(None, description="Patient's name.", example="Yashvi M. Patel")
    age: Optional[int] = Field(None, description="Patient's age.", example=21)
    sex: Optional[str] = Field(None, description="Patient's sex.", example="Female")

class StructuredData(BaseModel):
    """Represents the fully structured data extracted from the report."""
    patient_details: PatientDetails
    test_results: List[TestResult]

# --- [FIX] Moved AnomalyReport definition BEFORE it is used ---
# In src/api/schemas.py (REPLACE AnomalyReport)

class AnomalyReport(BaseModel):
    """Defines the structure for a single flagged anomaly with explainability."""
    flag_type: str = Field(..., description="Type of flag (Plausibility or Statistical).", example="Statistical")
    test_name: str = Field(..., description="The name of the flagged test.")
    result: Any = Field(..., description="The anomalous result value.")
    reason: str = Field(..., description="The high-level reason the result was flagged.")
    details: Optional[str] = Field(None, description="Explainability details (e.g., Plausible Range or Anomaly Score).")

class AnalysisPayload(BaseModel):
    """The main analysis payload containing all processed information."""
    structured_data: StructuredData
    summary: str = Field(..., description="AI-generated patient-friendly summary.")
    anomaly_report: List[AnomalyReport] = Field([], description="A list of any detected anomalies or potential fraud flags.")

class AnalysisResponse(BaseModel):
    """The final, top-level response model for the /process_report endpoint."""
    filename: str = Field(..., description="Name of the processed file.", example="report.pdf")
    analysis: AnalysisPayload
    
    
    