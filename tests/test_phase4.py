"""
Test Phase 4 — Attack, Weapon, and Target Classification
==========================================================

Tests the attack_extractor module with realistic incident texts.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from extraction.attack_extractor import (
    extract_attack_types,
    extract_weapon_types,
    extract_target_types,
)


SAMPLES = [
    (
        "A suicide bomb exploded near a church in the city centre, "
        "killing 45 civilians. Gunmen then opened fire on the crowd."
    ),
    (
        "Militants armed with AK-47 rifles stormed a military base "
        "in the eastern province."
    ),
    (
        "A car bomb detonated near the embassy, damaging the building "
        "and injuring several police officers."
    ),
    (
        "Two journalists were assassinated outside their office "
        "by unidentified gunmen."
    ),
    (
        "Rebels kidnapped 12 students from a school in the northern region."
    ),
    (
        "The group hijacked a passenger aircraft en route to the capital."
    ),
    (
        "Protesters set fire to the government building using Molotov cocktails."
    ),
    (
        "A knife attack on a busy train left 5 passengers wounded."
    ),
]


def run_tests():
    print("=" * 70)
    print("  Test Phase 4 — Attack, Weapon & Target Classification")
    print("=" * 70)
    print()

    for i, text in enumerate(SAMPLES, start=1):
        attacks = extract_attack_types(text)
        weapons = extract_weapon_types(text)
        targets = extract_target_types(text)

        print(f"  Sample {i}:")
        print(f"    Text    : {text[:80]}...")
        print(f"    Attacks : {attacks}")
        print(f"    Weapons : {weapons}")
        print(f"    Targets : {targets}")
        print()

    print("=" * 70)
    print("  Phase 4 tests complete. Verify results manually above.")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
