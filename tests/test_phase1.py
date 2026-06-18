"""
Test Phase 1 — Date & Location Extraction
==========================================

Tests the date_extractor and location_extractor modules
with sample incident texts.
"""

import os
import sys

# Ensure project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from extraction.date_extractor import extract_date
from extraction.location_extractor import extract_location


SAMPLES = [
    # Explicit Country + City match (Confidence 1.0)
    "A bombing attack occurred in Colombo, Sri Lanka on April 21, 2019.",
    "The attack took place in Mumbai, Maharashtra, India on 26 November 2008.",
    # Infer Country from City (Confidence 0.8 / 0.9 depending on logic, here 1.0 because known city)
    "A major terrorist attack occurred in Pulwama, Jammu and Kashmir.",
    "An explosion was reported near Kabul on 15 March 2020.",
    "A blast shook Lahore yesterday.",
    "Gunmen attacked a hotel in Islamabad.",
    "Protests turned violent in Dhaka.",
    "An earthquake hit Kathmandu.",
    "A shooting took place in Delhi.",
    # Unknown City in Known Country (Confidence 0.7 or 0.8)
    "An incident in a small village in Pakistan.",
    # Unknown Country and Unknown City (Confidence 0.5)
    "The incident occurred in Paris, France on 13/11/2015.",
    # Nothing
    "No date or location information available in this sentence."
]


def run_tests():
    print("=" * 70)
    print("  Test Phase 1 — Date & Location Extraction (Configurable)")
    print("=" * 70)
    print()

    for i, text in enumerate(SAMPLES, start=1):
        date = extract_date(text)
        location = extract_location(text)

        print(f"  Sample {i}:")
        print(f"    Text       : {text}")
        print(f"    Date       : {date!r}")
        print(f"    Country    : {location['country']!r}")
        print(f"    State      : {location['state']!r}")
        print(f"    City       : {location['city']!r}")
        print(f"    Confidence : {location['confidence']}")
        print()

    print("=" * 70)
    print("  Phase 1 tests complete. Verify results manually above.")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
