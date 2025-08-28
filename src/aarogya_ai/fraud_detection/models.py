import pandas as pd
from sklearn.ensemble import IsolationForest
from typing import List, Dict, Any

def find_statistical_anomalies(df: pd.DataFrame, contamination: float = 0.05) -> pd.DataFrame:
    """
    Uses Isolation Forest to find statistical outliers in the data.
    It analyzes each test type independently and returns anomalies with a score.
    """
    if df.empty or 'result_numeric' not in df.columns:
        return pd.DataFrame()

    all_anomalies = []
    for test_name, group in df.groupby('test_name'):
        if len(group) < 10:  # Need enough data to find meaningful anomalies
            continue
        
        X = group[['result_numeric']].values
        model = IsolationForest(contamination=contamination, random_state=42)
        model.fit(X)
        
        scores = -1 * model.decision_function(X) # Lower scores are more anomalous; we invert them.
        group['anomaly_flag'] = model.predict(X)
        group['anomaly_score'] = scores
        
        anomalies = group[group['anomaly_flag'] == -1].copy()
        if not anomalies.empty:
            all_anomalies.append(anomalies)
            
    if not all_anomalies:
        return pd.DataFrame()
        
    final_anomalies_df = pd.concat(all_anomalies)
    
    # Format the final report for the API
    final_anomalies_df['Reason'] = 'Result is a statistical outlier'
    final_anomalies_df['Details'] = final_anomalies_df['anomaly_score'].apply(lambda x: f"Anomaly Score: {x:.2f}")
    
    report_columns = {
        'test_name': 'Test Name',
        'result_numeric': 'Anomalous Result',
        'Reason': 'Reason',
        'Details': 'Details'
    }
    return final_anomalies_df[list(report_columns.keys())].rename(columns=report_columns)



