"""
Experiment 3 — DOCX Text Extraction using python-docx
======================================================

Interactive demo wrapper.
Production logic has been moved to ingestion/docx_ingestor.py.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Re-export production function for backward compatibility
from ingestion.docx_ingestor import extract_docx  # noqa: F401


def main():
    print("=" * 60)
    print("  Experiment 3 — DOCX Extraction (python-docx)")
    print("=" * 60)

    file_path = input("\nEnter DOCX path: ").strip()

    try:
        result = extract_docx(file_path)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"[ERROR] {e}")
        return

    print("\n--- Paragraphs ---\n")
    for i, line in enumerate(result["text"].splitlines(), start=1):
        print(f"  [{i}] {line}")

    print()
    print("-" * 40)
    print(f"  Paragraph Count : {result['paragraph_count']}")
    print(f"  Character Count : {len(result['text'])}")
    print()


if __name__ == "__main__":
    main()
