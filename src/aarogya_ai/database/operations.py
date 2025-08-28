import sqlite3
import pandas as pd
import logging
from typing import Dict, Any

DB_PATH = "aarogya_ai_data.db"

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def initialize_database():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # [DEFINITIVE FIX] Added patient_age and patient_sex to the table schema
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source_file TEXT,
            patient_name TEXT,
            patient_age INTEGER,
            patient_sex TEXT,
            test_name TEXT,
            result REAL,
            unit TEXT,
            reference_range TEXT
        );
        """)
        conn.commit()
        conn.close()
        logging.info("✅ Database initialized successfully.")
    except Exception as e:
        logging.error(f"❌ Failed to initialize database: {e}", exc_info=True)

def save_analysis_to_db(structured_data: Dict[str, Any], source_file: str):
    try:
        patient_details = structured_data.get('patient_details', {})
        test_results = structured_data.get('test_results', [])
        if not test_results: return

        df = pd.DataFrame(test_results)
        # [DEFINITIVE FIX] Add all patient details to the DataFrame before saving
        df['patient_name'] = patient_details.get('name')
        df['patient_age'] = patient_details.get('age')
        df['patient_sex'] = patient_details.get('sex')
        df['source_file'] = source_file
        
        df['result'] = pd.to_numeric(df['result'], errors='coerce')
        df.dropna(subset=['result'], inplace=True)
        
        # Ensure column order matches the new table schema perfectly
        df_to_insert = df[['source_file', 'patient_name', 'patient_age', 'patient_sex', 'test_name', 'result', 'unit', 'reference_range']]

        conn = get_db_connection()
        df_to_insert.to_sql('reports', conn, if_exists='append', index=False)
        conn.close()
        logging.info(f"✅ Successfully saved {len(df_to_insert)} records to DB for file: {source_file}")
    except Exception as e:
        logging.error(f"❌ Failed to save analysis to DB for file {source_file}: {e}", exc_info=True)

def get_patient_history(patient_name: str) -> pd.DataFrame:
    if not patient_name: return pd.DataFrame()
    try:
        conn = get_db_connection()
        query = "SELECT * FROM reports WHERE patient_name = ? ORDER BY processed_at DESC"
        df_history = pd.read_sql_query(query, conn, params=(patient_name,))
        conn.close()
        logging.info(f"Found {len(df_history)} historical records for patient: {patient_name}")
        return df_history
    except Exception as e:
        logging.error(f"Error fetching patient history for {patient_name}: {e}", exc_info=True)
        return pd.DataFrame()
    
    