"""
DOCX Ingestor
=============

Extracts paragraph text from Microsoft Word (.docx) files
using python-docx.
"""

import os
from docx import Document


def extract_docx(file_path: str) -> dict:
    """
    Open a DOCX file and extract all paragraph text.

    Returns
    -------
    dict with keys:
        text            – full extracted text
        paragraph_count – number of paragraphs
        extractor       – name of the extractor used
    """

    # --- 1. Validate path ---------------------------------------------------
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        doc = Document(file_path)
    except Exception as e:
        raise RuntimeError(f"Could not open DOCX: {e}")

    # --- 2. Read paragraphs -------------------------------------------------
    paragraphs = doc.paragraphs
    full_text = "\n".join(para.text for para in paragraphs)

    return {
        "text": full_text,
        "paragraph_count": len(paragraphs),
        "extractor": "python-docx",
    }
