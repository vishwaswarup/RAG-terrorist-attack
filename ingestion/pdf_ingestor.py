"""
PDF Ingestor
============

Extracts text and metadata from PDF files using PyMuPDF (fitz).
Now also extracts embedded images, runs OCR and captions on them,
and appends the results to the document text.
"""

import os
import fitz  # PyMuPDF
import tempfile
from ingestion.image_ingestor import extract_image_text


def extract_pdf(file_path: str) -> dict:
    """
    Open a PDF and extract text from all pages.
    Also extracts embedded images, generating captions and OCR text.

    Returns
    -------
    dict with keys:
        text       – full extracted text (including image captions/ocr)
        page_count – number of pages
        metadata   – PDF metadata dict
        extractor  – name of the extractor used
    """

    import time
    t0 = time.perf_counter()
    
    # --- 1. Validate path ----------------------------------------------------
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        doc = fitz.open(file_path)
    except Exception as e:
        raise RuntimeError(f"Could not open PDF: {e}")

    # --- 2. Extract text and images page-by-page ----------------------------
    all_text_parts = []
    
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        
        # 2a. Extract standard text
        page_text = page.get_text()
        if page_text.strip():
            all_text_parts.append(page_text)
            
        # 2b. Extract images
        image_list = page.get_images(full=True)
        for img_index, img_info in enumerate(image_list):
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Create a temporary file to run OCR/captioning
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{image_ext}") as tmp:
                    tmp.write(image_bytes)
                    tmp_path = tmp.name
                    
                try:
                    # Run the multimodal image ingestor
                    img_result = extract_image_text(tmp_path)
                    
                    img_output = f"\n--- Embedded Image {img_index + 1} on Page {page_num + 1} ---\n"
                    if img_result.get("caption"):
                        img_output += f"Caption: {img_result['caption']}\n"
                    if img_result.get("text"):
                        img_output += f"OCR Text: {img_result['text']}\n"
                        
                    all_text_parts.append(img_output)
                except Exception as inner_e:
                    print(f"  ⚠ Failed to process image {img_index+1} on page {page_num+1}: {inner_e}")
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                        
            except Exception as e:
                print(f"  ⚠ Failed to extract image {img_index+1} from PDF page {page_num+1}: {e}")

    full_text = "\n".join(all_text_parts)

    result = {
        "text": full_text,
        "page_count": doc.page_count,
        "metadata": dict(doc.metadata),
        "extractor": "PyMuPDF (with Image OCR)",
    }

    doc.close()
    
    elapsed = time.perf_counter() - t0
    print(f"[Timing] Standard PDF Ingestion (with Images) completed in {elapsed:.4f}s")
    
    return result
