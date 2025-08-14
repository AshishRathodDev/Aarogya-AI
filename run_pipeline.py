# run_pipeline.py

from src.data_processing.pipeline import IntelligentParser
import os
import pandas as pd

def main():
    print("--- Starting Aarogya-AI Data Processing Pipeline (v13 - FORENSIC MODE) ---")
    
    RAW_DATA_DIR = os.path.join('data', 'raw_reports')
    PROCESSED_DATA_DIR = os.path.join('data', 'processed')

    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    
    parser = IntelligentParser()
    
    output_csv_file = os.path.join(PROCESSED_DATA_DIR, 'master_health_data.csv')
    
    master_df = parser.process_directory(RAW_DATA_DIR)
    
    if master_df is not None and not master_df.empty:
        master_df.to_csv(output_csv_file, index=False)
        print(f"\n--- Pipeline Complete! ---")
        print(f"Successfully processed and saved {len(master_df)} records to '{output_csv_file}'")
        
        print("\n--- FINAL DATAFRAME HEAD ---")
        print(master_df.head())

        # --- AS PER YOUR BRILLIANT IDEA: THE FORENSIC REPORT ---
        print("\n\n--- FORENSIC REPORT: IDENTIFYING PROBLEMATIC DATA ---")
        
        # Rule 1: Find rows with garbage flags (e.g., flag length > 1)
        # We also check for NaN values in the flag column before applying string operations
        garbage_flags_df = master_df[master_df['flag'].notna() & (master_df['flag'].str.len() > 1)]
        
        if not garbage_flags_df.empty:
            print("\n[ALERT] Found rows with potentially garbage 'flag' values:")
            print("These files might have messy formats:")
            print(garbage_flags_df[['source_file', 'test_name', 'flag']].to_string())
        else:
            print("\n[INFO] No significant garbage found in 'flag' column. Good job!")

    else:
        print("\n--- PIPELINE COMPLETED ---")
        print("Could not extract any structured test data from the reports.")

if __name__ == '__main__':
    main()