"""Fix ground truth state values to match CITY_TO_STATE mappings."""
import json, os

GT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ground_truth")

# Correct state values for each incident based on CITY_TO_STATE
CORRECTIONS = {
    "incident_001.json": "Jammu and Kashmir",   # Pulwama → J&K (was "Jammu")
    "incident_002.json": "Maharashtra",          # Mumbai → Maharashtra (correct)
    # incident_003: Colombo, Sri Lanka — no state/province system
    "incident_004.json": "Punjab",               # Pathankot → Punjab (correct)
    "incident_005.json": "Khyber Pakhtunkhwa",   # Peshawar → KP (was "")
    "incident_006.json": "Jammu and Kashmir",    # Uri → J&K (was "Jammu")
    "incident_007.json": "Kabul",                # Kabul → Kabul province (was "")
    "incident_008.json": "Balochistan",           # Quetta → Balochistan (correct)
    "incident_009.json": "",                      # Dhaka — no state (correct)
    "incident_010.json": "Delhi",                # New Delhi → Delhi (was "")
    "incident_011.json": "Punjab",               # Lahore → Punjab (was "")
    "incident_012.json": "Jammu and Kashmir",    # Srinagar → J&K (was "Jammu")
    "incident_013.json": "Punjab",               # Lahore → Punjab (was "")
    "incident_014.json": "Kandahar",             # Kandahar → Kandahar province (was "")
    "incident_015.json": "Bihar",                # Bodh Gaya → Bihar (correct)
    "incident_016.json": "Kunduz",               # Kunduz → Kunduz province (was "")
    "incident_017.json": "Jammu and Kashmir",    # Nagrota → J&K (was "Jammu")
    "incident_018.json": "Kabul",                # Kabul → Kabul province (was "")
    "incident_019.json": "Jammu and Kashmir",    # Anantnag → J&K (was "Jammu")
    "incident_020.json": "Nangarhar",            # Jalalabad → Nangarhar (correct)
    "incident_021.json": "Sindh",                # Karachi → Sindh (correct)
    "incident_022.json": "Punjab",               # Gurdaspur → Punjab (correct)
    "incident_023.json": "Balkh",                # Mazar-i-Sharif → Balkh (correct)
    "incident_024.json": "",                      # Dhaka — no state (correct)
    "incident_025.json": "Jammu and Kashmir",    # Handwara → J&K (was "Jammu")
}

updated = 0
for filename, correct_state in CORRECTIONS.items():
    path = os.path.join(GT_DIR, filename)
    if not os.path.isfile(path):
        continue
    with open(path) as f:
        data = json.load(f)
    if data.get("state") != correct_state:
        old = data.get("state", "")
        data["state"] = correct_state
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
        print(f"  ✅ {filename}: '{old}' → '{correct_state}'")
        updated += 1
    else:
        print(f"  ── {filename}: already correct ('{correct_state}')")

print(f"\n  Updated {updated} files.")
