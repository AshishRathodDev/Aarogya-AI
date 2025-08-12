import re
import pandas as pd
import os
from typing import List, Dict
import warnings
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

warnings.filterwarnings('ignore')

class UniversalReportParser:
    def __init__(self):
        self.patient_patterns = {
            'name': [r"Name\s*:\s*(Mr\.|Mrs\.)\s*([^\n]+)", r"Patient Name\s*:\s*([^\n]+)"],
            'age': [r"Age\s*:\s*(\d+)", r"Age / Gender\s*:\s*(\d+)"],
            'sex': [r"Sex\s*:\s*(Male|Female|M|F)\b", r"Age/Sex\s*-\s*\d+\s*Yers/(\w)"]
        }
        self.master_test_list = [
            "Total Cholesterol", "HDL Cholesterol", "Triglycerides", "LDL", "VLDL", 
            "LDL/ HDL Ratio", "Total Cholesterol/HDL Ratio", "Bilirubin Total", "Bilirubin Direct", 
            "Serum Bilirubin (Indirect)", "SGOT / AST", "SGPT / ALT", "AST / ALT Ratio", 
            "Alkaline Phosphatase (ALP)", "Total Protein", "Albumin", "Globulin", 
            "Albumin/Globulin (A/G) Ratio", "S.Cholesterol", "S.Triglycerides", "S. HDL", "S. LDL", "S. VLDL",
            "CHOLESTEROL", "TRIGLYCERIDES", "HDL-CHOLESTEROL", "LDL-CHOLESTEROL"
        ]

    def _extract_text_from_file(self, file_path: str) -> str:
        text = ""
        try:
            if file_path.lower().endswith('.pdf'):
                doc = fitz.open(file_path)
                for page in doc:
                    text += page.get_text()
                doc.close()
            elif file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                text = pytesseract.image_to_string(Image.open(file_path))
            print(f"[INFO] Text extracted from {os.path.basename(file_path)}")
        except Exception as e:
            print(f"[ERROR] Failed to extract text from {file_path}. Reason: {e}")
        return text

    def _parse_patient_info(self, text: str) -> Dict:
        patient_info = {}
        for key, patterns in self.patient_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    # Get the last matching group
                    info = match.groups()[-1].strip()
                    patient_info[key] = re.sub(r'Referral.*', '', info, flags=re.IGNORECASE).strip()
                    break
        return patient_info

    def _parse_test_results(self, text: str) -> pd.DataFrame:
        test_results = []
        lines = text.split('\n')
        
        for line in lines:
            for test_name in self.master_test_list:
                if line.strip().lower().startswith(test_name.lower()):
                    numbers = re.findall(r'[\d.]+', line)
                    if numbers:
                        result = numbers[0]
                        flag = "".join(re.findall(r'[HLΗ]', line, re.IGNORECASE))
                        ref_interval = " ".join(re.findall(r'\d+\s*-\s*\d+', line)) or "N/A"
                        unit_match = re.search(r'(mg/dl|Ratio|U/L|g/dL|%)', line, re.IGNORECASE)
                        unit = unit_match.group(0) if unit_match else "N/A"

                        test_results.append({
                            "test_name": test_name,
                            "result": result,
                            "flag": flag,
                            "biological_ref_interval": ref_interval,
                            "unit": unit
                        })
                    break
        return pd.DataFrame(test_results)

    def process_directory(self, directory_path: str) -> pd.DataFrame:
        all_results = []
        for filename in os.listdir(directory_path):
            # Ignore hidden files like .DS_Store
            if filename.startswith('.'):
                continue

            file_path = os.path.join(directory_path, filename)
            if not os.path.isfile(file_path):
                continue

            print(f"\n[PIPELINE] Processing: {filename}")
            raw_text = self._extract_text_from_file(file_path)
            
            if not raw_text:
                continue
                
            patient_info = self._parse_patient_info(raw_text)
            df_results = self._parse_test_results(raw_text)
            
            if not df_results.empty:
                for key, value in patient_info.items():
                    df_results[key] = value
                df_results['source_file'] = filename
                all_results.append(df_results)
        
        if all_results:
            return pd.concat(all_results, ignore_index=True)
        else:
            return pd.DataFrame()
