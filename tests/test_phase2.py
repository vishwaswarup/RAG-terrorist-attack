"""
Test Phase 2 — Casualty Extraction
====================================

Tests the casualty_extractor module with varied patterns.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from extraction.casualty_extractor import extract_casualties


SAMPLES = [
    ("A bomb exploded killing 45 people and injuring 200.", 45, 200),
    ("The attack left 30 dead and 150 wounded.", 30, 150),
    ("At least 269 people were killed and more than 500 were injured.", 269, 500),
    ("The death toll rose to 12. Over 50 people were hospitalized.", 12, 50),
    ("No casualties were reported in the incident.", 0, 0),
    ("3 soldiers were killed in the ambush.", 3, 0),
    ("The blast injured 75 civilians.", 0, 75),
    ("More than 100 people died and approximately 300 were wounded.", 100, 300),
    ("The bombing claimed 22 lives.", 22, 0),
    ("10 killed, 25 injured in the explosion.", 10, 25),
]


def run_tests():
    print("=" * 70)
    print("  Test Phase 2 — Casualty Extraction")
    print("=" * 70)
    print()

    passed = 0
    total = len(SAMPLES)

    for i, (text, expected_killed, expected_injured) in enumerate(SAMPLES, start=1):
        result = extract_casualties(text)
        k_ok = result["killed"] == expected_killed
        i_ok = result["injured"] == expected_injured
        status = "✅" if (k_ok and i_ok) else "❌"

        if k_ok and i_ok:
            passed += 1

        print(f"  Sample {i}: {status}")
        print(f"    Text     : {text}")
        print(f"    Killed   : {result['killed']} (expected {expected_killed}) {'✓' if k_ok else '✗'}")
        print(f"    Injured  : {result['injured']} (expected {expected_injured}) {'✓' if i_ok else '✗'}")
        print()

    print("=" * 70)
    print(f"  Results: {passed}/{total} passed")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
