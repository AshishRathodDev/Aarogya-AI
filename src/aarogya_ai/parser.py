import re
import json
import logging
from abc import ABC, abstractmethod
import google.generativeai as genai
from typing import Dict, Any

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
    def __init__(self, config: Dict[str, Any], max_retries: int = 2):
        self.model_name = config['model_name']
        self.system_prompt = config['system_prompt']
        self.max_retries = max_retries
        self.model = genai.GenerativeModel(
            self.model_name,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        logging.info(f"GeminiParser initialized with model: {self.model_name}")

    def parse(self, text: str) -> Dict[str, Any]:
        """
        Parses text using the Gemini model with a self-correction retry loop.
        """
        attempt = 0
        last_exception = None
        
        # We will try up to 'max_retries' times to get a valid JSON
        while attempt < self.max_retries:
            attempt += 1
            logging.info(f"Sending request to Gemini AI (Attempt {attempt}/{self.max_retries})...")
            
            try:
                # If this is a retry, we include the error from the previous attempt
                if last_exception:
                    correction_prompt = f"""
                    The previous attempt failed with a JSON parsing error.
                    ERROR: {last_exception}
                    
                    Please analyze the original text again and provide a valid JSON output without any syntax errors.
                    ORIGINAL TEXT:
                    {text}
                    """
                    prompt = [self.system_prompt, correction_prompt]
                else:
                    prompt = [self.system_prompt, text]

                response = self.model.generate_content(prompt)
                
                # Attempt to parse the JSON. If it works, we're done.
                parsed_json = json.loads(response.text)
                logging.info("✅ Successfully parsed valid JSON response from Gemini AI.")
                return parsed_json
            
            except json.JSONDecodeError as e:
                logging.warning(f"Attempt {attempt} failed. Gemini returned invalid JSON. Error: {e}")
                last_exception = e
                # If this was the last attempt, we give up.
                if attempt >= self.max_retries:
                    logging.error("Max retries reached. Failed to get valid JSON from Gemini.")
                    break
            except Exception as e:
                # Handle other potential API errors
                logging.error(f"An unexpected error occurred with Gemini on attempt {attempt}: {e}")
                last_exception = e
                break # Don't retry on non-JSON errors

        # If the loop finishes without success, return an empty structure.
        return {"patient_details": {}, "test_results": []}
    
    
    