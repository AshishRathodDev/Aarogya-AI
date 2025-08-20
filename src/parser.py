import re
import json
import logging
from abc import ABC, abstractmethod
import google.generativeai as genai

# Ek blueprint jo batata hai ki har parser kaisa dikhega
class BaseParser(ABC):
    @abstractmethod
    def parse(self, text: str) -> dict:
        pass

# Hathiyaar #1: Regex Guard
class RegexParser(BaseParser):
    def __init__(self, patterns: dict):
        self.patterns = patterns
        logging.info("RegexParser initialized.")

    def parse(self, text: str) -> dict:
        extracted_data = {"test_results": []}
        for test_name, pattern in self.patterns.items():
            # I am using a simpler regex here, can be improved.
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    result_obj = {
                        "test_name": test_name,
                        "result": float(match.group(2)),
                        "unit": match.group(3).strip() if len(match.groups()) > 2 and match.group(3) else None
                    }
                    extracted_data["test_results"].append(result_obj)
                except (ValueError, IndexError):
                    logging.warning(f"Could not parse result for {test_name} with Regex.")
                    continue
        logging.info(f"RegexParser found {len(extracted_data['test_results'])} test results.")
        return extracted_data

# Hathiyaar #2: AI Commando
class GeminiParser(BaseParser):
    def __init__(self, config: dict):
        self.model_name = config['model_name']
        self.system_prompt = config['system_prompt']
        self.model = genai.GenerativeModel(
            self.model_name,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        logging.info(f"GeminiParser initialized with model: {self.model_name}")

    def parse(self, text: str) -> dict:
        try:
            logging.info("Sending request to Gemini AI...")
            response = self.model.generate_content([self.system_prompt, text])
            parsed_json = json.loads(response.text)
            logging.info("Successfully parsed response from Gemini AI.")
            return parsed_json
        except Exception as e:
            logging.error(f"Error while parsing with Gemini: {e}")
            return {"patient_details": {}, "test_results": []}