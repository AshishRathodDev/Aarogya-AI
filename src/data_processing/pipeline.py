import re
import pandas as pd
import os
from typing import List, Dict, Any
import warnings
import fitz
from PIL import Image
import pytesseract

warnings.filterwarnings('ignore')

class IntelligentParser:
    def __init__(self):
        # ... (patient_patterns same rahega) ...
        self.patient_patterns = {
            'name': re.compile(r"(?:Name|Patient Name)\s*:\s*(Mr\.|Mrs\.)\s*([^\n]+)", re.IGNORECASE),
            'age': re.compile(r"Age\s*:\s*(\d+)", re.IGNORECASE),
            'sex': re.compile(r"Sex\s*:\s*(Male|Female|M|F)\b", re.IGNORECASE)
        }
        
        # --- THE ARCHITECT'S UPGRADE ---
        # Hum pehle hi saare patterns ko compile karke rakh lenge.
        self.test_patterns = self._compile_test_patterns()
        
        self.table_start_keywords = ['BIOCHEMISTRY', 'Test Name', 'Test Performed', 'Investigations', 'LIPID PROFILE']
        self.table_end_keywords = ['Interpretation', 'Clinical Significance', '** End of Report', '---', 'Method:', 'Page:']

    def _compile_test_patterns(self) -> Dict[str, re.Pattern]:
        """
        Pre-compiles regex patterns for all test aliases for maximum performance.
        """
        master_test_map = {
            "Total Cholesterol": ["Total Cholesterol", "S.Cholesterol", "CHOLESTEROL"],
            "HDL Cholesterol": ["HDL Cholesterol", "S. HDL", "HDL-CHOLESTEROL", "HDL"],
            # ... (baaki saare tests yahan daalna) ...
            "Triglycerides": ["Triglycerides", "S.Triglycerides"]
        }
        
        compiled_patterns = {}
        for standard_name, aliases in master_test_map.items():
            # Create a regex pattern that matches any of the aliases
            # e.g., (Total Cholesterol|S\.Cholesterol|CHOLESTEROL)
            pattern_str = r'\b(' + '|'.join(re.escape(alias) for alias in aliases) + r')\b'
            compiled_patterns[standard_name] = re.compile(pattern_str, re.IGNORECASE)
            
        return compiled_patterns

    # ... (_extract_text_from_file aur _parse_patient_info same rahenge) ...
    def _extract_text_from_file(self, file_path: str) -> str:
        text, filename = "", os.path.basename(file_path)
        if not (filename.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg'))): return ""
        try:
            if filename.lower().endswith('.pdf'):
                with fitz.open(file_path) as doc:
                    for page in doc: text += page.get_text("text")
            else:
                text = pytesseract.image_to_string(Image.open(file_path))
            print(f"[INFO] Text extracted from {filename}")
            return text
        except Exception as e:
            print(f"[ERROR] Failed to process {filename}. Reason: {e}")
            return ""

    def _parse_patient_info(self, text: str) -> Dict[str, Any]:
        info = {}
        for key, pattern in self.patient_patterns.items():
            match = pattern.search(text)
            if match:
                info[key] = match.groups()[-1].strip()
        return info

    def _parse_test_results(self, text: str) -> pd.DataFrame:
        results = []
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        in_test_section = False
        for i, line in enumerate(lines):
            if not in_test_section and any(keyword.lower() in line.lower() for keyword in self.table_start_keywords):
                in_test_section = True
            if in_test_section and any(keyword.lower() in line.lower() for keyword in self.table_end_keywords):
                in_test_section = False

            if in_test_section:
                # Ab hum pehle se banaye hue patterns use karenge
                for standard_name, pattern in self.test_patterns.items():
                    if pattern.search(line):
                        lookahead_text = " ".join(lines[i : i+4])
                        result_match = re.search(r'(\d+\.\d+|\d+)', lookahead_text)
                        
                        if result_match:
                            result = result_match.group(1)
                            flag = "".join(re.findall(r'[HLΗ]', line, re.IGNORECASE))
                            ref_match = re.search(r'(\d+\s*-\s*\d+)', lookahead_text)
                            ref_interval = ref_match.group(0) if ref_match else "N/A"
                            unit_match = re.search(r'(mg/dl|Ratio|U/L|g/dL|%)', lookahead_text, re.IGNORECASE)
                            unit = unit_match.group(0) if unit_match else "N/A"
                            
                            results.append({
                                "test_name": standard_name, "result": result, "flag": flag,
                                "biological_ref_interval": ref_interval, "unit": unit
                            })
                            break # Found a match, go to the next line
        
        return pd.DataFrame(results)

    # ... (process_directory same rahega) ...
    def process_directory(self, directory_path: str) -> pd.DataFrame:
        all_results = []
        if not os.path.isdir(directory_path): return pd.DataFrame()
            
        for filename in sorted(os.listdir(directory_path)):
            if filename.startswith('.'): continue
            
            file_path = os.path.join(directory_path, filename)
            if not os.path.isfile(file_path): continue
            
            print(f"\n[PIPELINE] Processing: {filename}")
            raw_text = self._extract_text_from_file(file_path)
            if not raw_text: continue
            
            patient_info = self._parse_patient_info(raw_text)
            df_results = self._parse_test_results(raw_text)
            
            if not df_results.empty:
                df_results['patient_name'] = patient_info.get('name', 'Unknown')
                df_results['age'] = patient_info.get('age', None)
                df_results['sex'] = patient_info.get('sex', 'Unknown')
                df_results['source_file'] = filename
                all_results.append(df_results)
            else:
                print(f"[INFO] No valid test results found in {filename}")
        
        if all_results:
            master_df = pd.concat(all_results, ignore_index=True)
            master_df.drop_duplicates(inplace=True)
            master_df['result'] = pd.to_numeric(master_df['result'], errors='coerce')
            master_df.dropna(subset=['result'], inplace=True)
            master_df['patient_id'] = master_df.groupby('source_file').ngroup() + 1
            return master_df
        else:
            return pd.DataFrame()