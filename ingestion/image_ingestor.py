"""
Image Ingestor
==============

Extracts text from images using EasyOCR.
"""

import os
import easyocr


def extract_image_text(file_path: str) -> dict:
    """
    Run OCR on an image and return extracted text.

    Returns
    -------
    dict with keys:
        text       – combined extracted text
        detections – number of text detections
        extractor  – name of the extractor used
    """

    # --- 1. Validate path ---------------------------------------------------
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # --- 2. Initialise EasyOCR reader ---------------------------------------
    try:
        reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    except Exception as e:
        raise RuntimeError(f"Could not initialise EasyOCR: {e}")

    # --- 3. Run OCR ---------------------------------------------------------
    try:
        results = reader.readtext(file_path)
    except Exception as e:
        raise RuntimeError(f"OCR failed: {e}")

    # --- 4. Combine detected text -------------------------------------------
    combined_text = " ".join(text for (_, text, _) in results)

    return {
        "text": combined_text,
        "detections": len(results),
        "extractor": "EasyOCR",
    }
