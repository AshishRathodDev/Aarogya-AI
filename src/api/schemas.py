
"""
Pydantic Models for Aarogya-AI API

This module defines the data structures (schemas) for API request and response bodies.
Using these models ensures that our API is self-documenting, strongly-typed,
and provides clear validation errors.
"""

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

class AnalysisPayload(BaseModel):
    """The main analysis payload containing all processed information."""
    structured_data: StructuredData
    summary: str = Field(..., description="AI-generated patient-friendly summary.")
    # Future enhancement: anomaly_report: Optional[dict] = None

class AnalysisResponse(BaseModel):
    """The final, top-level response model for the /process_report endpoint."""
    filename: str = Field(..., description="Name of the processed file.", example="report.pdf")
    analysis: AnalysisPayload
    
    