"""
Extraction Evaluation Framework
================================

Measures extraction accuracy across all fields by comparing
pipeline output against ground-truth JSON files.

Usage:
    python3 evaluation/evaluate_extraction.py
"""

import os
import sys
import json
import glob

# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from models.document import Document
from incident_pipeline import build_incident


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize(s: str) -> str:
    """Lowercase and strip for comparison."""
    return s.strip().lower() if s else ""


def _set_score(expected: list, actual: list) -> dict:
    """
    Compare two lists and return precision, recall, F1.
    Uses case-insensitive, substring-aware matching.
    """
    if not expected and not actual:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "tp": 0, "fp": 0, "fn": 0}

    expected_norm = [_normalize(e) for e in expected]
    actual_norm = [_normalize(a) for a in actual]

    # For each expected item, check if ANY actual item contains it or vice versa
    tp = 0
    matched_actual = set()
    for e in expected_norm:
        for i, a in enumerate(actual_norm):
            if i not in matched_actual and (e in a or a in e):
                tp += 1
                matched_actual.add(i)
                break

    fp = len(actual_norm) - len(matched_actual)
    fn = len(expected_norm) - tp

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}


def _exact_match(expected, actual) -> bool:
    """Check if two scalar values match (case-insensitive for strings)."""
    if isinstance(expected, str) and isinstance(actual, str):
        return _normalize(expected) == _normalize(actual)
    return expected == actual


def _numeric_match(expected: int, actual: int) -> bool:
    """Check exact numeric match."""
    return expected == actual


# ---------------------------------------------------------------------------
# Main evaluation
# ---------------------------------------------------------------------------

def evaluate():
    eval_dir = os.path.dirname(os.path.abspath(__file__))
    inc_dir = os.path.join(eval_dir, "incidents")
    gt_dir = os.path.join(eval_dir, "ground_truth")

    # Discover all incident files
    incident_files = sorted(glob.glob(os.path.join(inc_dir, "incident_*.txt")))

    if not incident_files:
        print("  No incident files found in evaluation/incidents/")
        return

    print()
    print("=" * 70)
    print("  EXTRACTION EVALUATION FRAMEWORK")
    print("=" * 70)
    print(f"  Incidents found: {len(incident_files)}")
    print()

    # Accumulators
    field_correct = {
        "date": 0, "country": 0, "state": 0, "city": 0,
        "killed": 0, "injured": 0,
    }
    field_total = {k: 0 for k in field_correct}

    list_scores = {
        "responsible_groups": [],
        "target_organizations": [],
        "attack_types": [],
        "weapon_types": [],
        "target_types": [],
    }

    # Failure log
    failures = []

    for inc_path in incident_files:
        basename = os.path.splitext(os.path.basename(inc_path))[0]
        gt_path = os.path.join(gt_dir, basename + ".json")

        if not os.path.isfile(gt_path):
            print(f"  ⚠  No ground truth for {basename}, skipping.")
            continue

        # Load text
        with open(inc_path, "r") as f:
            text = f.read().strip()

        # Load ground truth
        with open(gt_path, "r") as f:
            gt = json.load(f)

        # Build a fake Document to feed the pipeline
        doc = Document(
            doc_id=basename,
            source_type="TXT",
            source_path=inc_path,
            raw_text=text,
            title=basename,
        )

        # Run extraction (suppress DB save by catching it)
        try:
            incident = build_incident(doc)
        except Exception as e:
            print(f"  ❌ {basename}: extraction failed — {e}")
            continue

        # --- Compare scalar fields ---
        for field in ["date", "country", "state", "city"]:
            expected = gt.get(field, "")
            actual = getattr(incident, field, "")
            field_total[field] += 1
            if _exact_match(expected, actual):
                field_correct[field] += 1
            else:
                failures.append({
                    "incident": basename,
                    "field": field,
                    "expected": expected,
                    "actual": actual,
                })

        for field in ["killed", "injured"]:
            expected = gt.get(field, 0)
            actual = getattr(incident, field, 0)
            field_total[field] += 1
            if _numeric_match(expected, actual):
                field_correct[field] += 1
            else:
                failures.append({
                    "incident": basename,
                    "field": field,
                    "expected": expected,
                    "actual": actual,
                })

        # --- Compare list fields ---
        for field in list_scores.keys():
            expected = gt.get(field, [])
            actual = getattr(incident, field, [])
            score = _set_score(expected, actual)
            list_scores[field].append({
                "incident": basename,
                "expected": expected,
                "actual": actual,
                **score,
            })

            # Log false positives and false negatives
            if score["fp"] > 0 or score["fn"] > 0:
                failures.append({
                    "incident": basename,
                    "field": field,
                    "expected": expected,
                    "actual": actual,
                    "fp": score["fp"],
                    "fn": score["fn"],
                })

    # --- Print Results ---
    print("-" * 70)
    print("  SCALAR FIELD ACCURACY")
    print("-" * 70)
    for field in ["date", "country", "state", "city", "killed", "injured"]:
        total = field_total[field]
        correct = field_correct[field]
        pct = (correct / total * 100) if total > 0 else 0
        status = "✅" if pct >= 90 else "⚠️" if pct >= 70 else "❌"
        print(f"  {status} {field:20s} : {correct}/{total}  ({pct:.0f}%)")

    print()
    print("-" * 70)
    print("  LIST FIELD ACCURACY (Avg Precision / Recall / F1)")
    print("-" * 70)
    for field, scores in list_scores.items():
        if not scores:
            continue
        avg_p = sum(s["precision"] for s in scores) / len(scores)
        avg_r = sum(s["recall"] for s in scores) / len(scores)
        avg_f = sum(s["f1"] for s in scores) / len(scores)
        total_fp = sum(s["fp"] for s in scores)
        total_fn = sum(s["fn"] for s in scores)
        status = "✅" if avg_f >= 0.90 else "⚠️" if avg_f >= 0.70 else "❌"
        print(f"  {status} {field:25s} : P={avg_p:.2f}  R={avg_r:.2f}  F1={avg_f:.2f}  (FP={total_fp}, FN={total_fn})")

    # --- Failure Analysis ---
    print()
    print("-" * 70)
    print("  TOP FAILURE CATEGORIES")
    print("-" * 70)

    # Group failures by field
    failure_by_field = {}
    for f in failures:
        fld = f["field"]
        if fld not in failure_by_field:
            failure_by_field[fld] = []
        failure_by_field[fld].append(f)

    for fld, flist in sorted(failure_by_field.items(), key=lambda x: -len(x[1])):
        print(f"\n  [{fld}] — {len(flist)} error(s):")
        for item in flist[:5]:  # Show top 5
            print(f"    {item['incident']}:")
            print(f"      Expected : {item['expected']}")
            print(f"      Got      : {item['actual']}")

        if len(flist) > 5:
            print(f"    ... and {len(flist) - 5} more.")

    # --- Overall Summary ---
    print()
    print("=" * 70)
    total_scalar = sum(field_total.values())
    correct_scalar = sum(field_correct.values())
    overall_scalar_pct = (correct_scalar / total_scalar * 100) if total_scalar > 0 else 0

    all_f1 = []
    for scores in list_scores.values():
        all_f1.extend(s["f1"] for s in scores)
    avg_overall_f1 = (sum(all_f1) / len(all_f1)) if all_f1 else 0

    print(f"  Overall Scalar Accuracy : {correct_scalar}/{total_scalar} ({overall_scalar_pct:.1f}%)")
    print(f"  Overall List F1         : {avg_overall_f1:.2f}")
    print(f"  Total Failures Logged   : {len(failures)}")
    print("=" * 70)
    print()

    # --- Save JSON report ---
    report = {
        "incidents_evaluated": len(incident_files),
        "scalar_accuracy": {},
        "list_accuracy": {},
        "overall_scalar_accuracy": round(overall_scalar_pct, 1),
        "overall_list_f1": round(avg_overall_f1, 2),
        "total_failures": len(failures),
        "failures": failures,
    }

    for field in ["date", "country", "state", "city", "killed", "injured"]:
        total = field_total[field]
        correct = field_correct[field]
        report["scalar_accuracy"][field] = {
            "correct": correct,
            "total": total,
            "pct": round((correct / total * 100) if total > 0 else 0, 1),
        }

    for field, scores in list_scores.items():
        if not scores:
            continue
        avg_p = sum(s["precision"] for s in scores) / len(scores)
        avg_r = sum(s["recall"] for s in scores) / len(scores)
        avg_f = sum(s["f1"] for s in scores) / len(scores)
        total_fp = sum(s["fp"] for s in scores)
        total_fn = sum(s["fn"] for s in scores)
        report["list_accuracy"][field] = {
            "precision": round(avg_p, 2),
            "recall": round(avg_r, 2),
            "f1": round(avg_f, 2),
            "total_fp": total_fp,
            "total_fn": total_fn,
        }

    # Determine report name from CLI args or default
    report_name = "evaluation_report"
    if len(sys.argv) > 1:
        report_name = sys.argv[1]

    reports_dir = os.path.join(PROJECT_ROOT, "evaluation_reports")
    os.makedirs(reports_dir, exist_ok=True)
    report_path = os.path.join(reports_dir, f"{report_name}.json")

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"  📊 Report saved to: {report_path}")
    print()


if __name__ == "__main__":
    evaluate()
