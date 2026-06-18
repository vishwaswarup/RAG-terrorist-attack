"""
Experiment 1 — File Classification using python-magic
======================================================

Interactive demo wrapper.
Production logic has been moved to ingestion/file_classifier.py.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Re-export production function for backward compatibility
from ingestion.file_classifier import classify_file  # noqa: F401


def main():
    print("=" * 60)
    print("  Experiment 1 — File Classifier (python-magic)")
    print("=" * 60)
    print()

    file_path = input("Enter file path: ").strip()

    result = classify_file(file_path)

    print()
    print(f"  File Path   : {result['file_path']}")
    print(f"  MIME Type   : {result['mime_type']}")
    print(f"  Description : {result['description']}")
    print()
    print(f"  ➜  Classification: {result['category']}")
    print()


if __name__ == "__main__":
    main()
