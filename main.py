from fastapi import FastAPI, File, UploadFile, Form, HTTPException
import os
import shutil
import logging
import cv2
import pytesseract
import re

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI()

# Set the Tesseract OCR path if needed (for Windows users)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Directory to store temporary images
TEMP_DIR = "temp_images"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.post("/verify-pan")
async def verify_pan(
    pan_number: str = Form(...),
    pan_card_image: UploadFile = File(...)
):
    """Verify PAN number from the PAN card image using OCR."""

    # Define file path
    pan_card_path = os.path.join(TEMP_DIR, pan_card_image.filename)

    # Save uploaded image temporarily
    with open(pan_card_path, "wb") as buffer:
        shutil.copyfileobj(pan_card_image.file, buffer)

    logging.info("PAN card image saved successfully.")

    # Step 1: Extract PAN number from image using OCR
    extracted_pan = extract_pan_number(pan_card_path)
    if not extracted_pan:
        cleanup_files([pan_card_path])
        raise HTTPException(status_code=400, detail="Could not extract PAN number from the image.")

    logging.info(f"Extracted PAN Number: {extracted_pan}")

    # Step 2: Check if extracted PAN matches the provided PAN number
    if extracted_pan.strip().upper() != pan_number.strip().upper():
        cleanup_files([pan_card_path])
        return {"status": "Not Verified", "reason": "PAN number does not match."}

    # Cleanup temporary file
    cleanup_files([pan_card_path])

    return {"status": "Verified", "message": "PAN number matches successfully."}


def extract_pan_number(image_path: str) -> str:
    """Extract PAN number using OCR (Tesseract)."""
    try:
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # Convert to grayscale
        text = pytesseract.image_to_string(gray, config="--psm 6")  # OCR processing
        logging.debug(f"OCR Result: {text}")

        # Extract PAN number pattern (ABCDE1234F)
        match = re.search(r"[A-Z]{5}[0-9]{4}[A-Z]", text)
        if match:
            return match.group(0)
    except Exception as e:
        logging.error(f"Error extracting PAN number: {e}")
    return None


def cleanup_files(file_paths: list):
    """Remove temporary files after processing."""
    for file_path in file_paths:
        if os.path.exists(file_path):
            os.remove(file_path)
            logging.info(f"Deleted temporary file: {file_path}")
