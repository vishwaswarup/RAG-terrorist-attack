"""
Test Phase 3 — Organization Extraction
========================================

Tests the organization_extractor module with sample texts.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from extraction.organization_extractor import extract_organizations


SAMPLES = [
    # Case 1
    (
        "Jaish-e-Mohammed claimed responsibility for the attack. 40 CRPF personnel were killed.",
        {"responsible": ["Jaish-e-Mohammed"], "targets": ["CRPF"]}
    ),
    # Case 2
    (
        "ISIS claimed responsibility. Local police confirmed the casualties.",
        {"responsible": ["ISIS"], "targets": []}
    ),
    # Case 3
    (
        "The convoy of the Indian Army was targeted by Lashkar-e-Taiba militants.",
        {"responsible": ["Lashkar-e-Taiba"], "targets": ["Indian Army"]}
    ),
    # General Tests
    (
        "The bombing was attributed to the Taliban.",
        {"responsible": ["Taliban"], "targets": []}
    ),
    (
        "The attack was carried out by Lashkar-e-Taiba operatives.",
        {"responsible": ["Lashkar-e-Taiba"], "targets": []}
    ),
    (
        "BSF troops engaged the insurgents.",
        {"responsible": [], "targets": ["BSF"]}
    )
]


def run_tests():
    print("=" * 70)
    print("  Test Phase 3 — Organization Extraction (Perpetrator vs Target)")
    print("=" * 70)
    print()

    passed = 0
    for i, (text, expected) in enumerate(SAMPLES, start=1):
        result = extract_organizations(text)
        
        # Lowercase for robust comparison
        res_resp = {x.lower() for x in result["responsible_groups"]}
        res_targ = {x.lower() for x in result["target_organizations"]}
        exp_resp = {x.lower() for x in expected["responsible"]}
        exp_targ = {x.lower() for x in expected["targets"]}

        match_resp = (res_resp == exp_resp)
        match_targ = (res_targ == exp_targ)

        print(f"  Sample {i}: {text[:60]}...")
        if match_resp and match_targ:
            print("    ✅ PASS")
            passed += 1
        else:
            print("    ❌ FAIL")
            if not match_resp:
                print(f"      Expected Resp : {expected['responsible']}")
                print(f"      Got Resp      : {result['responsible_groups']}")
            if not match_targ:
                print(f"      Expected Targ : {expected['targets']}")
                print(f"      Got Targ      : {result['target_organizations']}")
        print()

    print("=" * 70)
    print(f"  Passed {passed} / {len(SAMPLES)} tests.")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
