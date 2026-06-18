"""
Experiment 6 — Scanned PDF OCR (pdf2image + EasyOCR)
=====================================================

Interactive demo wrapper.
Production logic has been moved to ingestion/scanned_pdf_ingestor.py.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Re-export production function for backward compatibility
from ingestion.scanned_pdf_ingestor import extract_scanned_pdf  # noqa: F401


TEMP_DIR = "temp_pages"


def main():
    print("=" * 60)
    print("  Experiment 6 — Scanned PDF OCR (pdf2image + EasyOCR)")
    print("=" * 60)

    file_path = input("\nEnter scanned PDF path: ").strip()

    try:
        print("\n  Converting PDF pages to images...")
        print("  Initialising EasyOCR...")
        result = extract_scanned_pdf(file_path)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"[ERROR] {e}")
        return

    print(f"  Pages Processed: {result['page_count']}")
    print()

    for page_num, page_text in enumerate(result["text"].split("\n"), start=1):
        print(f"===== PAGE {page_num} OCR =====")
        print(page_text if page_text.strip() else "  (no text detected)")
        print()

    print("-" * 40)
    print(f"  Total extracted characters: {len(result['text'])}")
    print(f"  Temp images saved in    : {os.path.abspath(TEMP_DIR)}/")
    print()


if __name__ == "__main__":
    main()
