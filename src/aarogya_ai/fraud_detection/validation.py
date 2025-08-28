from typing import Dict, Any, List
import pandas as pd
from aarogya_ai.api.schemas import PatientDetails

def perform_cross_report_validation(current_patient: PatientDetails, historical_data: pd.DataFrame) -> List[Dict[str, Any]]:
    anomalies = []
    if historical_data.empty or not current_patient or current_patient.age is None:
        return anomalies

    # [DEFINITIVE FIX] Check if the required column exists before accessing it
    if 'patient_age' in historical_data.columns:
        previous_ages = historical_data['patient_age'].dropna()
        if not previous_ages.empty:
            last_known_age = previous_ages.iloc[0]
            if current_patient.age < last_known_age:
                anomalies.append({
                    "flag_type": "Cross-Validation",
                    "test_name": "Patient Age",
                    "result": current_patient.age,
                    "reason": "Patient age decreased over time.",
                    "details": f"Current age: {current_patient.age}, Last known age: {last_known_age}"
                })
    return anomalies


