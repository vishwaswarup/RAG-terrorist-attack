"""
Experiment 2 — PDF Text Extraction using PyMuPDF
=================================================

Interactive demo wrapper.
Production logic has been moved to ingestion/pdf_ingestor.py.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Re-export production function for backward compatibility
from ingestion.pdf_ingestor import extract_pdf  # noqa: F401


def main():
    print("=" * 60)
    print("  Experiment 2 — PDF Extraction (PyMuPDF)")
    print("=" * 60)

    file_path = input("\nEnter PDF path: ").strip()

    try:
        result = extract_pdf(file_path)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"[ERROR] {e}")
        return

    print(f"\n  Page Count : {result['page_count']}")
    print(f"  Metadata   :")
    for key, value in result["metadata"].items():
        if value:
            print(f"    {key:12s} : {value}")

    print(f"\n  Extracted Text:\n")
    print(result["text"] if result["text"].strip() else "  (no extractable text)")

    print("-" * 40)
    print(f"  Total extracted characters: {len(result['text'])}")
    print()


if __name__ == "__main__":
    main()
