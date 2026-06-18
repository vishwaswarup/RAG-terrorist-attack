"""
PDF Ingestor
============

Extracts text and metadata from PDF files using PyMuPDF (fitz).
"""

import os
import fitz  # PyMuPDF


def extract_pdf(file_path: str) -> dict:
    """
    Open a PDF and extract text from all pages.

    Returns
    -------
    dict with keys:
        text       – full extracted text
        page_count – number of pages
        metadata   – PDF metadata dict
        extractor  – name of the extractor used
    """

    # --- 1. Validate path ----------------------------------------------------
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        doc = fitz.open(file_path)
    except Exception as e:
        raise RuntimeError(f"Could not open PDF: {e}")

    # --- 2. Extract text page-by-page ---------------------------------------
    all_text_parts = []
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        all_text_parts.append(page.get_text())

    full_text = "\n".join(all_text_parts)

    result = {
        "text": full_text,
        "page_count": doc.page_count,
        "metadata": dict(doc.metadata),
        "extractor": "PyMuPDF",
    }

    doc.close()
    return result
