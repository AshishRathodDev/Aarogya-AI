import os
import yaml
import logging
import pandas as pd
from tqdm import tqdm
import google.generativeai as genai

# Apne project ke modules ko import karo
from src.data_processing.pipeline import extract_text_from_file # Aapke structure ke hisaab se
from src.parser import RegexParser, GeminiParser

# Setup logging (yeh professional tarika hai)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger('google.generativeai').setLevel(logging.WARNING) # Google ke faltu logs ko chup karao

def setup_credentials_and_ai():
    """Google credentials aur AI ko set karta hai."""
    try:
        # NOTE: Apni key ka path yahan daalna hai
        CREDENTIALS_FILE = 'crack-decorator-468911-s1-5ab46e3aea4b.json'
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDENTIALS_FILE
        genai.configure(transport='rest')
        logging.info("Google credentials and Gemini configured successfully.")
        return True
    except Exception as e:
        logging.error(f"Failed to configure credentials: {e}")
        return False

def main():
    """Main pipeline jahan saara magic hoga."""
    logging.info("--- Starting Aarogya-AI Intelligent Parsing Pipeline ---")

    # Step 1: Control Panel (params.yaml) load karo
    try:
        with open('params.yaml', 'r') as f:
            params = yaml.safe_load(f)
        logging.info("Parameters from params.yaml loaded.")
    except FileNotFoundError:
        logging.error("params.yaml not found! Please create it.")
        return

    # Step 2: AI aur Credentials setup karo
    if not setup_credentials_and_ai():
        return

    # Step 3: Dono hathiyaar (parsers) taiyar karo
    regex_parser = RegexParser(params['regex_patterns'])
    gemini_parser = GeminiParser(params['llm_parser_config'])
    fallback_threshold = params['parser_config']['gemini_fallback_threshold']
    
    # Step 4: Files ko process karna shuru karo
    raw_reports_dir = 'data/raw_reports'
    all_files = [os.path.join(raw_reports_dir, f) for f in os.listdir(raw_reports_dir) if f.endswith(('.pdf', '.jpg', '.png'))]
    
    final_results = []

    logging.info(f"Found {len(all_files)} files to process.")
    
    # tqdm ek sundar progress bar dikhata hai
    for file_path in tqdm(all_files, desc="Processing Reports"):
        logging.info(f"--- Processing: {os.path.basename(file_path)} ---")
        
        # Station 1: Text Extract karo
        raw_text = extract_text_from_file(file_path) # Yeh function aapke pipeline.py se aa raha hai
        
        if not raw_text or len(raw_text) < 50: # Agar text bahut kam hai to skip karo
            logging.warning(f"Not enough text extracted from {file_path}. Skipping.")
            continue
            
        # Station 2: HYBRID PARSING LOGIC
        logging.info("Attempting to parse with RegexParser (The Guard)...")
        parsed_data = regex_parser.parse(raw_text)
        
        num_tests_found = len(parsed_data.get('test_results', []))
        
        # Faisla lene ka waqt (The General's Decision)
        if num_tests_found < fallback_threshold:
            logging.warning(f"Guard found only {num_tests_found} tests (threshold is {fallback_threshold}). Escalating to Commando (Gemini)...")
            parsed_data = gemini_parser.parse(raw_text)
        else:
            logging.info(f"Guard successful. Found {num_tests_found} tests.")
            
        # Result ko final list mein daalo
        patient_name = parsed_data.get('patient_details', {}).get('name')
        for test in parsed_data.get('test_results', []):
            test['patient_name'] = patient_name
            test['source_file'] = os.path.basename(file_path)
            final_results.append(test)

    # Step 5: Final data ko ek single CSV file mein save karo
    if final_results:
        output_path = 'data/processed/master_health_data_v2.csv'
        df = pd.DataFrame(final_results)
        df.to_csv(output_path, index=False)
        logging.info(f"--- Pipeline Finished ---")
        logging.info(f"Successfully processed {len(all_files)} files. Results saved to {output_path}")
        print("\n--- FINAL DATAFRAME HEAD ---")
        print(df.head())
    else:
        logging.warning("No data was extracted from any file.")

if __name__ == '__main__':
    main()