from src.data_processing.pipeline import UniversalReportParser
import os

def main():
    print("--- Starting Aarogya-AI Data Processing Pipeline (V2 - INTELLIGENT PARSING) ---")
    
    RAW_DATA_DIR = os.path.join('data', 'raw_reports')
    PROCESSED_DATA_DIR = os.path.join('data', 'processed')

    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    
    parser = UniversalReportParser()
    
    master_df = parser.process_directory(RAW_DATA_DIR)
    
    if not master_df.empty:
        # Ab hum asli data save kar rahe hain
        output_csv_file = os.path.join(PROCESSED_DATA_DIR, 'master_health_data.csv')
        master_df.to_csv(output_csv_file, index=False)
        print(f"\n--- Pipeline Complete! ---")
        print(f"Successfully processed and saved {len(master_df)} records to '{output_csv_file}'")
        print("\nFinal DataFrame Head:")
        print(master_df.head())
    else:
        print("\n--- Pipeline Complete! ---")
        print("Could not extract any structured test data from the reports.")

if __name__ == '__main__':
    main()