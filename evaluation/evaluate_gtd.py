"""
GTD Evaluation Framework
========================

Benchmarks the extraction pipeline against GTD summaries.
Generates accuracy metrics and failure logs.
"""

import os
import sys
import csv
from collections import defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from extraction.attack_extractor import extract_attack_types, extract_weapon_types, extract_target_types
from extraction.casualty_extractor import extract_casualties

# ---------------------------------------------------------------------------
# Label Mappings (GTD -> Extractor Expected)
# ---------------------------------------------------------------------------

ATTACK_MAP = {
    "Bombing/Explosion": ["Bombing"],
    "Armed Assault": ["Armed Assault"],
    "Assassination": ["Assassination"],
    "Facility/Infrastructure Attack": ["Arson", "Bombing"],
    "Hostage Taking (Kidnapping)": ["Kidnapping"],
    "Hijacking": ["Hijacking"],
    "Unarmed Assault": ["Unarmed Assault"]
}

WEAPON_MAP = {
    "Explosives": ["Explosives"],
    "Firearms": ["Firearms"],
    "Incendiary": ["Incendiary"],
    "Melee": ["Melee"],
    "Chemical": ["Chemical"],
    "Vehicle (not to include vehicle-borne explosives, i.e., car or truck bombs)": ["Vehicle"],
    "Sabotage Equipment": ["Sabotage Equipment"]
}

TARGET_MAP = {
    "Military": ["Military"],
    "Police": ["Government"],
    "Government (General)": ["Government"],
    "Government (Diplomatic)": ["Government"],
    "Private Citizens & Property": ["Civilian"],
    "Business": ["Civilian"],
    "Educational Institution": ["Civilian"],
    "NGO": ["Civilian"],
    "Tourists": ["Civilian"],
    "Religious Figures/Institutions": ["Religious"],
    "Utilities": ["Infrastructure"],
    "Telecommunication": ["Infrastructure"],
    "Journalists & Media": ["Media"],
    "Transportation": ["Transportation"],
    "Airports & Aircraft": ["Transportation"],
    "Maritime": ["Transportation"]
}

def is_match(gtd_label, predicted_list, mapping):
    """
    Returns True if the mapped GTD label is found in the predicted list.
    Returns False otherwise.
    """
    if gtd_label not in mapping:
        return False
    
    expected_labels = mapping[gtd_label]
    for expected in expected_labels:
        if expected in predicted_list:
            return True
    return False

def parse_casualty(val):
    if not val:
        return None
    try:
        return int(float(val))
    except ValueError:
        return None

class FieldMetrics:
    def __init__(self):
        self.total = 0
        self.correct = 0
        self.unknown = 0
        self.correct_unknown = 0  # how many 'Unknown' GTD rows we got correct (usually 0 if we predict anything)
        
    def add_result(self, is_correct, is_unknown):
        self.total += 1
        if is_unknown:
            self.unknown += 1
            if is_correct:
                self.correct_unknown += 1
        else:
            if is_correct:
                self.correct += 1

    @property
    def total_known(self):
        return self.total - self.unknown

    @property
    def accuracy_including_unknown(self):
        if self.total == 0: return 0.0
        # For 'Unknown' rows, if we predict something, it's considered wrong (unless it's an empty list match)
        return ((self.correct + self.correct_unknown) / self.total) * 100

    @property
    def accuracy_excluding_unknown(self):
        if self.total_known == 0: return 0.0
        return (self.correct / self.total_known) * 100

def main():
    dataset_path = os.path.join(PROJECT_ROOT, "evaluation", "gtd_eval_1000.csv")
    results_dir = os.path.join(PROJECT_ROOT, "evaluation", "results")
    os.makedirs(results_dir, exist_ok=True)
    
    attack_failures = []
    weapon_failures = []
    target_failures = []
    casualty_failures = []
    
    metrics = {
        "attack_type": FieldMetrics(),
        "weapon_type": FieldMetrics(),
        "target_type": FieldMetrics(),
        "killed": FieldMetrics(),
        "wounded": FieldMetrics()
    }
    
    with open(dataset_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            summary = row["summary"]
            
            # Ground Truth
            gt_attack = row["attacktype1_txt"]
            gt_weapon = row["weaptype1_txt"]
            gt_target = row["targtype1_txt"]
            gt_nkill = parse_casualty(row.get("nkill"))
            gt_nwound = parse_casualty(row.get("nwound"))
            
            # Predictions
            pred_attacks = extract_attack_types(summary)
            pred_weapons = extract_weapon_types(summary)
            pred_targets = extract_target_types(summary)
            pred_casualties = extract_casualties(summary)
            
            # --- Evaluate Attack ---
            is_unk = (gt_attack == "Unknown")
            # If GTD is Unknown, we only 'match' if we also predicted nothing.
            if is_unk:
                match = (len(pred_attacks) == 0)
            else:
                match = is_match(gt_attack, pred_attacks, ATTACK_MAP)
            
            metrics["attack_type"].add_result(match, is_unk)
            if not match and not is_unk:  # Log failure only for knowns
                attack_failures.append({"summary": summary, "ground_truth": gt_attack, "prediction": str(pred_attacks)})

            # --- Evaluate Weapon ---
            is_unk = (gt_weapon == "Unknown")
            if is_unk:
                match = (len(pred_weapons) == 0)
            else:
                match = is_match(gt_weapon, pred_weapons, WEAPON_MAP)
            
            metrics["weapon_type"].add_result(match, is_unk)
            if not match and not is_unk:
                weapon_failures.append({"summary": summary, "ground_truth": gt_weapon, "prediction": str(pred_weapons)})

            # --- Evaluate Target ---
            is_unk = (gt_target == "Unknown")
            if is_unk:
                match = (len(pred_targets) == 0)
            else:
                match = is_match(gt_target, pred_targets, TARGET_MAP)
            
            metrics["target_type"].add_result(match, is_unk)
            if not match and not is_unk:
                target_failures.append({"summary": summary, "ground_truth": gt_target, "prediction": str(pred_targets)})

            # --- Evaluate Killed ---
            is_unk_k = (gt_nkill is None)
            pred_k = pred_casualties.get("killed")
            # If GT is None, we consider it a match if we predicted 0
            if is_unk_k:
                match = (pred_k == 0)
            else:
                match = (pred_k == gt_nkill)
            
            metrics["killed"].add_result(match, is_unk_k)
            if not match and not is_unk_k:
                casualty_failures.append({"summary": summary, "ground_truth": f"K:{gt_nkill}", "prediction": f"K:{pred_k}"})

            # --- Evaluate Wounded ---
            is_unk_w = (gt_nwound is None)
            pred_w = pred_casualties.get("injured")
            if is_unk_w:
                match = (pred_w == 0)
            else:
                match = (pred_w == gt_nwound)
                
            metrics["wounded"].add_result(match, is_unk_w)
            if not match and not is_unk_w:
                casualty_failures.append({"summary": summary, "ground_truth": f"W:{gt_nwound}", "prediction": f"W:{pred_w}"})

    # --- Write Failure CSVs ---
    def write_failures(filename, data):
        path = os.path.join(results_dir, filename)
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["summary", "ground_truth", "prediction"])
            writer.writeheader()
            writer.writerows(data)
            
    write_failures("attack_failures.csv", attack_failures)
    write_failures("weapon_failures.csv", weapon_failures)
    write_failures("target_failures.csv", target_failures)
    write_failures("casualty_failures.csv", casualty_failures)

    # --- Generate Markdown Report ---
    report_path = os.path.join(results_dir, "evaluation_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# GTD Benchmark Evaluation Report\n\n")
        f.write(f"Total summaries evaluated: {metrics['attack_type'].total}\n\n")
        
        f.write("## Field-wise Accuracy\n\n")
        f.write("| Field | Accuracy (Excl. Unknowns) | Accuracy (Incl. Unknowns) | Known Rows | Unknown Rows |\n")
        f.write("|---|---|---|---|---|\n")
        for field, m in metrics.items():
            excl = f"{m.accuracy_excluding_unknown:.1f}%"
            incl = f"{m.accuracy_including_unknown:.1f}%"
            f.write(f"| {field} | {excl} | {incl} | {m.total_known} | {m.unknown} |\n")
            
        f.write("\n## Failure Analysis & Recommendations\n\n")
        
        f.write("### Attack Types\n")
        f.write(f"- Failed to match {len(attack_failures)} known GTD labels.\n")
        f.write("- **Recommendation:** Review `attack_failures.csv`. Common GTD labels like 'Unarmed Assault' currently have no mapping in our ontology. Decide if the ontology should be expanded, or if keyword lists for existing categories need widening.\n\n")
        
        f.write("### Weapon Types\n")
        f.write(f"- Failed to match {len(weapon_failures)} known GTD labels.\n")
        f.write("- **Recommendation:** Review `weapon_failures.csv`. GTD labels like 'Sabotage Equipment' might need a new category or mapping.\n\n")
        
        f.write("### Target Types\n")
        f.write(f"- Failed to match {len(target_failures)} known GTD labels.\n")
        f.write("- **Recommendation:** Review `target_failures.csv`. There is significant semantic drift between GTD 'Private Citizens' and our 'Civilian' definitions depending on context.\n\n")
        
        f.write("### Casualties\n")
        f.write(f"- Failed exact-match on {len(casualty_failures)} known GTD labels (Killed/Wounded combined).\n")
        f.write("- **Recommendation:** Review `casualty_failures.csv`. The extractor may be missing complex numerical phrases or 'dozens', 'hundreds', etc.\n\n")

    print(f"Evaluation complete. Report generated at: {report_path}")

if __name__ == "__main__":
    main()
