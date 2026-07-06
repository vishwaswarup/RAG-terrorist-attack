"""
TXT Ingestor
============

Reads plain-text files with encoding fallback (UTF-8 → Latin-1).
"""

import os


def extract_txt(file_path: str) -> dict:
    """
    Read a plain-text file and return its contents.

    Returns
    -------
    dict with keys:
        text       – full file contents
        line_count – number of lines
        extractor  – name of the extractor used
    """

    import time
    t0 = time.perf_counter()
    # --- 1. Validate path ---------------------------------------------------
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            contents = f.read()
    except UnicodeDecodeError:
        # Fall back to latin-1 which never raises decode errors
        with open(file_path, "r", encoding="latin-1") as f:
            contents = f.read()
    except Exception as e:
        raise RuntimeError(f"Could not read file: {e}")

    elapsed = time.perf_counter() - t0
    print(f"[Timing] TXT Ingestion completed in {elapsed:.4f}s")

    return {
        "text": contents,
        "line_count": len(contents.splitlines()),
        "extractor": "Built-in (open)",
    }
