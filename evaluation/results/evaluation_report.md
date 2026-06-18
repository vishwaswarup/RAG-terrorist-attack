# GTD Benchmark Evaluation Report

Total summaries evaluated: 1000

## Field-wise Accuracy

| Field | Accuracy (Excl. Unknowns) | Accuracy (Incl. Unknowns) | Known Rows | Unknown Rows |
|---|---|---|---|---|
| attack_type | 72.8% | 70.1% | 956 | 44 |
| weapon_type | 63.3% | 66.3% | 915 | 85 |
| target_type | 60.7% | 61.6% | 955 | 45 |
| killed | 72.7% | 73.3% | 964 | 36 |
| wounded | 82.6% | 83.3% | 923 | 77 |

## Failure Analysis & Recommendations

### Attack Types
- Failed to match 260 known GTD labels.
- **Recommendation:** Review `attack_failures.csv`. Common GTD labels like 'Unarmed Assault' currently have no mapping in our ontology. Decide if the ontology should be expanded, or if keyword lists for existing categories need widening.

### Weapon Types
- Failed to match 336 known GTD labels.
- **Recommendation:** Review `weapon_failures.csv`. GTD labels like 'Sabotage Equipment' might need a new category or mapping.

### Target Types
- Failed to match 375 known GTD labels.
- **Recommendation:** Review `target_failures.csv`. There is significant semantic drift between GTD 'Private Citizens' and our 'Civilian' definitions depending on context.

### Casualties
- Failed exact-match on 424 known GTD labels (Killed/Wounded combined).
- **Recommendation:** Review `casualty_failures.csv`. The extractor may be missing complex numerical phrases or 'dozens', 'hundreds', etc.

