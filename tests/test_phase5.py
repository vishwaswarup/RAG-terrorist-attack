"""
Test Phase 5 — Casualty Extraction: Number Words & Wider Patterns
==================================================================

Tests the upgraded casualty extractor's ability to handle:
1. Number words (seven, nineteen, etc.)
2. Compound numbers (forty five, twenty three)
3. Wider gaps between number and kill/injury keywords
4. Mixed patterns (number words + digits in same text)
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from extraction.casualty_extractor import extract_casualties


SAMPLES = [
    # --- Number words ---
    {
        "text": "Seven soldiers were killed in the ambush.",
        "killed": 7,
        "injured": 0,
    },
    {
        "text": "Two CRPF jawans were killed and four others were injured.",
        "killed": 2,
        "injured": 4,
    },
    {
        "text": "Nineteen people were injured in the blast.",
        "killed": 0,
        "injured": 19,
    },
    # --- Compound numbers ---
    {
        "text": "Forty five people were killed in the explosion.",
        "killed": 45,
        "injured": 0,
    },
    {
        "text": "Twenty three civilians were wounded in the attack.",
        "killed": 0,
        "injured": 23,
    },
    # --- Wider gap patterns ---
    {
        "text": "The blast resulted in the deaths of 40 Central Reserve Police Force personnel.",
        "killed": 40,
        "injured": 0,
    },
    {
        "text": "Seven Indian Air Force personnel were killed in the attack.",
        "killed": 7,
        "injured": 0,
    },
    {
        "text": "19 Indian Army soldiers were killed in the encounter.",
        "killed": 19,
        "injured": 0,
    },
    # --- Mixed: number words + digits ---
    {
        "text": "Seven people were killed and 150 were injured.",
        "killed": 7,
        "injured": 150,
    },
    # --- Boundary: don't cross kill/injury keywords ---
    {
        "text": "The attack left 30 dead and 150 wounded.",
        "killed": 30,
        "injured": 150,
    },
    {
        "text": "More than 100 people died and approximately 300 were wounded.",
        "killed": 100,
        "injured": 300,
    },
    # --- Zero case ---
    {
        "text": "There were no casualties reported.",
        "killed": 0,
        "injured": 0,
    },
]


def main():
    print("=" * 70)
    print("  Test Phase 5 — Casualty Extraction: Number Words & Wider Patterns")
    print("=" * 70)
    print()

    passed = 0
    total = len(SAMPLES)

    for i, sample in enumerate(SAMPLES, 1):
        result = extract_casualties(sample["text"])
        k_ok = result["killed"] == sample["killed"]
        i_ok = result["injured"] == sample["injured"]
        ok = k_ok and i_ok
        status = "✅" if ok else "❌"

        if ok:
            passed += 1

        print(f"  Sample {i}: {status}")
        print(f"    Text     : {sample['text'][:80]}...")
        print(f"    Killed   : {result['killed']} (expected {sample['killed']}) {'✓' if k_ok else '✗'}")
        print(f"    Injured  : {result['injured']} (expected {sample['injured']}) {'✓' if i_ok else '✗'}")
        print()

    print("=" * 70)
    print(f"  Results: {passed}/{total} passed")
    print("=" * 70)


if __name__ == "__main__":
    main()
