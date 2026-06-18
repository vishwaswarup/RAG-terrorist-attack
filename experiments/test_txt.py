"""
Experiment 4 — Plain Text File Reading
========================================

Interactive demo wrapper.
Production logic has been moved to ingestion/txt_ingestor.py.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Re-export production function for backward compatibility
from ingestion.txt_ingestor import extract_txt  # noqa: F401


def main():
    print("=" * 60)
    print("  Experiment 4 — TXT Extraction")
    print("=" * 60)

    file_path = input("\nEnter TXT path: ").strip()

    try:
        result = extract_txt(file_path)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"[ERROR] {e}")
        return

    print()
    print(f"  Line Count      : {result['line_count']}")
    print(f"  Character Count : {len(result['text'])}")
    print()
    print("--- Contents ---\n")
    print(result["text"])
    print()


if __name__ == "__main__":
    main()
