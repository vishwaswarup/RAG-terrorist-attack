"""
File Classifier
===============

Classifies files by their actual binary content (magic bytes)
rather than relying on file extensions.

Uses python-magic to detect MIME types and maps them to
high-level categories: PDF, DOCX, TXT, IMAGE, UNKNOWN.
"""

import os
import sys
import magic  # from python-magic


def classify_file(file_path: str) -> dict:
    """
    Analyse a file and return its MIME type, description,
    and a high-level category.

    Returns
    -------
    dict with keys:
        file_path   – the input path
        mime_type   – detected MIME type
        description – human-readable description
        category    – one of PDF, DOCX, TXT, IMAGE, UNKNOWN
    """

    # --- 1. Check the file exists -------------------------------------------
    if not os.path.isfile(file_path):
        print(f"[ERROR] File not found: {file_path}")
        sys.exit(1)

    # --- 2. Detect MIME type -------------------------------------------------
    mime_type = magic.from_file(file_path, mime=True)

    # --- 3. Get a human-readable description --------------------------------
    description = magic.from_file(file_path)

    # --- 4. Map MIME type to a simple category ------------------------------
    if mime_type == "application/pdf":
        category = "PDF"
    elif mime_type in (
        "application/vnd.openxmlformats-officedocument"
        ".wordprocessingml.document",
        "application/msword",
    ):
        category = "DOCX"
    elif mime_type.startswith("text/"):
        category = "TXT"
    elif mime_type.startswith("image/"):
        category = "IMAGE"
    else:
        category = "UNKNOWN"

    return {
        "file_path": file_path,
        "mime_type": mime_type,
        "description": description,
        "category": category,
    }
