"""
Experiment 5 — Image OCR using EasyOCR
========================================

Interactive demo wrapper.
Production logic has been moved to ingestion/image_ingestor.py.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Re-export production function for backward compatibility
from ingestion.image_ingestor import extract_image_text  # noqa: F401


def main():
    print("=" * 60)
    print("  Experiment 5 — Image OCR (EasyOCR)")
    print("=" * 60)

    file_path = input("\nEnter image path: ").strip()

    try:
        print("\n  Initialising EasyOCR (first run downloads models)...")
        print("  Running OCR...\n")
        result = extract_image_text(file_path)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"[ERROR] {e}")
        return

    print("-" * 40)
    print(f"  Total Detections : {result['detections']}")
    print()
    print("  Combined Extracted Text:")
    print(f"  {result['text']}")
    print()


if __name__ == "__main__":
    main()
