# src/fraud_detection/rules.py

"""
Rule-based anomaly detection for Aarogya-AI.
This module contains functions for the "Sentry" - our first level of fraud detection.
"""

import pandas as pd
from typing import Dict, List, Any

def find_plausibility_anomalies(df: pd.DataFrame, rules: Dict[str, Dict[str, float]]) -> pd.DataFrame:
    """
    Identifies records where test results fall outside plausible biological ranges.

    Args:
        df (pd.DataFrame): The cleaned input DataFrame containing a 'result_numeric' column.
        rules (Dict): A dictionary defining the min/max plausible range for each test.

    Returns:
        pd.DataFrame: A DataFrame containing only the anomalous records, formatted for reporting.
    """
    if df.empty or 'result_numeric' not in df.columns:
        return pd.DataFrame()

    # Filter the DataFrame to only include tests for which we have a rule
    df_filtered = df[df['test_name'].isin(rules.keys())].copy()
    if df_filtered.empty:
        return pd.DataFrame()

    # A lambda function to check if a value is outside its rule's range
    def is_anomalous(row):
        rule = rules.get(row['test_name'])
        # This check is safe because we already filtered the df
        return not (rule['min'] <= row['result_numeric'] <= rule['max'])

    # Apply the function to find anomalies
    anomalies_mask = df_filtered.apply(is_anomalous, axis=1)
    anomalies_df = df_filtered[anomalies_mask].copy()

    if not anomalies_df.empty:
        anomalies_df['Plausible Range'] = anomalies_df['test_name'].apply(lambda name: f"{rules[name]['min']} - {rules[name]['max']}")
        anomalies_df['Reason'] = 'Result is outside the plausible range.'
        
        # Select and rename columns for a clean report that matches our Pydantic alias
        report_columns = {
            'test_name': 'Test Name',
            'result_numeric': 'Anomalous Result',
            'Plausible Range': 'Plausible Range',
            'Reason': 'Reason'
        }
        return anomalies_df[list(report_columns.keys())].rename(columns=report_columns)
        
    return pd.DataFrame() # Return empty if no anomalies found


