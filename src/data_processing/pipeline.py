import os
import io
import fitz  # PyMuPDF
from google.cloud import vision
import logging

def extract_text_from_file(file_path: str) -> str:
    """
    Takes a file path (PDF or Image), and extracts all text using Google Vision API.
    This is our high-accuracy "Station 1: The Mouth".
    """
    logging.info(f"Starting text extraction for: {os.path.basename(file_path)}")
    
    # Vision API client ko function ke andar banayenge
    try:
        client = vision.ImageAnnotatorClient()
    except Exception as e:
        logging.error(f"Failed to create Vision API client. Check credentials. Error: {e}")
        return ""

    file_extension = os.path.splitext(file_path)[1].lower()
    
    # CASE 1: FILE IS A PDF
    if file_extension == '.pdf':
        try:
            doc = fitz.open(file_path)
            all_text = []
            
            # Agar PDF mein zyada pages hon, to un sabko process karega
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # High DPI for better quality OCR
                pix = page.get_pixmap(dpi=300)
                img_byte_arr = pix.tobytes("png")
                
                image = vision.Image(content=img_byte_arr)
                response = client.document_text_detection(image=image)
                
                if response.error.message:
                    raise Exception(response.error.message)
                    
                all_text.append(response.full_text_annotation.text)
            
            doc.close()
            logging.info(f"Successfully extracted text from {len(all_text)} pages of PDF.")
            return "\n\n--- PAGE BREAK ---\n\n".join(all_text)
            
        except Exception as e:
            logging.error(f"Error processing PDF {file_path}: {e}")
            return ""

    # CASE 2: FILE IS AN IMAGE
    elif file_extension in ['.jpg', '.jpeg', '.png']:
        try:
            with io.open(file_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            response = client.document_text_detection(image=image)

            if response.error.message:
                raise Exception(response.error.message)
            
            logging.info("Successfully extracted text from image.")
            return response.full_text_annotation.text
            
        except Exception as e:
            logging.error(f"Error processing Image {file_path}: {e}")
            return ""
            
    # CASE 3: UNSUPPORTED FILE
    else:
        logging.warning(f"Unsupported file type: {file_extension}. Skipping.")
        return ""