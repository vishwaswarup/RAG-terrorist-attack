"""
Scanned PDF Ingestor
====================

Handles PDFs that contain scanned images instead of selectable text.

Strategy:  PDF → convert pages to images → OCR each image.

Requires poppler to be installed on the system:
    macOS  : brew install poppler
    Ubuntu : sudo apt-get install poppler-utils
"""

import os
import shutil
import easyocr
from pdf2image import convert_from_path


TEMP_DIR = "temp_pages"


def extract_scanned_pdf(file_path: str) -> dict:
    """
    Convert a scanned PDF to images, then OCR each page.

    Returns
    -------
    dict with keys:
        text       – full extracted text (all pages combined)
        page_count – number of pages processed
        extractor  – name of the extractor used
    """

    import time
    t0 = time.perf_counter()
    # --- 1. Validate path ---------------------------------------------------
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # --- 2. Create (or recreate) temp folder --------------------------------
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)

    # --- 3. Convert PDF pages to images -------------------------------------
    try:
        images = convert_from_path(file_path)
    except Exception as e:
        raise RuntimeError(
            f"pdf2image conversion failed: {e}\n"
            "  Hint: Make sure 'poppler' is installed.\n"
            "    macOS  : brew install poppler\n"
            "    Ubuntu : sudo apt-get install poppler-utils"
        )

    # Save each page image
    image_paths = []
    for idx, img in enumerate(images):
        img_path = os.path.join(TEMP_DIR, f"page_{idx + 1}.png")
        img.save(img_path, "PNG")
        image_paths.append(img_path)

    # --- 4. Initialise EasyOCR ----------------------------------------------
    try:
        reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    except Exception as e:
        raise RuntimeError(f"Could not initialise EasyOCR: {e}")

    # --- 5. OCR each page ---------------------------------------------------
    all_page_texts = []

    for img_path in image_paths:
        try:
            results = reader.readtext(img_path)
        except Exception:
            all_page_texts.append("")
            continue

        page_text = " ".join(text for (_, text, _) in results)
        all_page_texts.append(page_text)

    full_text = "\n".join(all_page_texts)

    elapsed = time.perf_counter() - t0
    print(f"[Timing] Scanned PDF OCR Ingestion completed in {elapsed:.4f}s")

    return {
        "text": full_text,
        "page_count": len(image_paths),
        "extractor": "pdf2image + EasyOCR",
    }
