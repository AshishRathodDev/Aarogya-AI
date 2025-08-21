# src/data_processing/pipeline.py

import os
import io
import fitz  # PyMuPDF
from google.cloud import vision
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

# --- Global variable to hold our client ---
# We start with None, so it's "lazy".
_VISION_CLIENT: Optional[vision.ImageAnnotatorClient] = None

def get_vision_client() -> vision.ImageAnnotatorClient:
    """
    Initializes and returns a single, shared instance of the Vision API client.
    This is a professional pattern called the "Singleton" pattern.
    """
    global _VISION_CLIENT
    if _VISION_CLIENT is None:
        logging.info("Initializing Google Vision Client for the first time...")
        try:
            _VISION_CLIENT = vision.ImageAnnotatorClient()
            logging.info("✅ Google Vision Client initialized successfully.")
        except Exception as e:
            logging.error(f"❌ CRITICAL: Failed to initialize Google Vision Client. Check credentials. Error: {e}")
            raise ConnectionError("Could not initialize Google Vision client.") from e
    return _VISION_CLIENT

def _process_single_image_bytes(image_bytes: bytes, page_num: int = 0) -> str:
    """Helper function to process a single image's bytes."""
    client = get_vision_client()
    image = vision.Image(content=image_bytes)
    response = client.document_text_detection(image=image)
    
    if response.error.message:
        raise Exception(f"Google Vision API error on page/image {page_num + 1}: {response.error.message}")
    
    return response.full_text_annotation.text

def extract_text_from_file(file_path: str, max_workers: int = 10, dpi: int = 200) -> str:
    """
    High-performance, parallelized text extraction from a PDF or Image file.
    """
    logging.info(f"Starting text extraction for: {os.path.basename(file_path)}")
    file_extension = os.path.splitext(file_path)[1].lower()

    try:
        # --- PDF PROCESSING (Parallelized) ---
        if file_extension == '.pdf':
            doc = fitz.open(file_path)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(_process_single_image_bytes, page.get_pixmap(dpi=dpi).tobytes("png"), page_num): page_num
                    for page_num, page in enumerate(doc)
                }
                results = [""] * doc.page_count
                for future in as_completed(futures):
                    page_num = futures[future]
                    try:
                        results[page_num] = future.result()
                        logging.info(f"Successfully processed page {page_num + 1}/{doc.page_count}.")
                    except Exception as e:
                        logging.error(f"Failed to process page {page_num + 1}: {e}")
            doc.close()
            return "\n\n--- PAGE BREAK ---\n\n".join(results)

        # --- IMAGE PROCESSING (Single Task) ---
        elif file_extension in ['.jpg', '.jpeg', '.png']:
            with io.open(file_path, 'rb') as image_file:
                content = image_file.read()
            return _process_single_image_bytes(content)
        
        else:
            logging.warning(f"Unsupported file type: {file_extension}. Skipping.")
            return ""

    except Exception as e:
        logging.error(f"An error occurred during text extraction for {file_path}: {e}", exc_info=True)
        return ""
    
    
    
    