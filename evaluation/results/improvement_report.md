# GTD Extraction Improvement Report

This report compares the baseline accuracy metrics against the new metrics after expanding keyword vocabularies, handling fuzzy numeric terms, and parsing complex linguistic casualty structures.

## Accuracy Metrics (Before vs After)

| Field | Old Accuracy | New Accuracy (Excl. Unknowns) | Delta |
|---|---|---|---|
| **Attack Type** | 71.3% | **72.8%** | **+1.5 pp** |
| **Weapon Type** | 63.2% | **63.3%** | **+0.1 pp** |
| **Target Type** | 59.6% | **60.7%** | **+1.1 pp** |
| **Killed** | 70.4% | **72.7%** | **+2.3 pp** |
| **Wounded** | 83.1% | **82.6%** | **-0.5 pp** |

*Note: Wounded accuracy dropped marginally (0.5 pp), likely due to the aggressive logic summing conjunctions catching false positives.*

## Extractor Modifications Made

### 1. Casualty Extractor
- Implemented a fuzzy number parser (`_FUZZY`) to convert "dozens" (24), "scores" (40), and "several" (3) into integer equivalents before applying regex.
- Widened regex gap distances from 6 words to **15 words** to bypass long, comma-separated subordinate clauses. Switched gap token from `\w+` to `\S+` to handle commas and punctuation.
- Added `_add_conjunctions` function to capture split multi-noun structures (e.g., "8 soldiers and 2 civilians were wounded").
- Implemented logic to capture "including the attacker" and "In addition to the attacker" to correctly increment or decrement the GTD `nkill` logic.

### 2. Attack Extractor
- Added `Unarmed Assault` category for "beaten", "punched", "mob violence".
- Expanded `Kidnapping` with "hostage", "seized", "captured".
- Expanded `Arson` with "vandalized", "sabotage", "destroyed", "damaged".

### 3. Weapon Extractor
- Added `Sabotage Equipment` category for "tools", "wrench", "bolt cutter".
- Expanded `Melee` to include "blunt object".
- Expanded `Vehicle` to include "ramming attack", "drove into".
- Expanded `Chemical` to include "poison", "acid".

### 4. Target Extractor
- Expanded `Civilian` heavily to capture GTD "Business" and "Educational Institution" categorizations ("shops", "stores", "bank", "factory", "schools", "universities").
- Expanded `Infrastructure` for utilities ("power stations", "telecom towers", "pylon").
- Expanded `Military` to explicitly capture "military convoys" and "patrol".

## Remaining High-Frequency Failure Categories
Despite aggressive keyword additions, rule-based extraction struggles with deep semantic ambiguity in GTD. The highest frequency remaining failures are:
1. **Target - Private Citizens vs Government vs Business:** Distinguishing off-duty police, private individuals employed by the government, or politicians is highly ambiguous without NLP part-of-speech tagging.
2. **Attack - Armed Assault vs Assassination:** GTD frequently labels "Armed Assault" for events where individuals are shot, while our logic may prioritize "Assassination" if it's a targeted killing, or vice versa depending on the journalist's phrasing.
3. **Weapon - Unknowns & Implied:** GTD labels "Firearms" when the text only says "shot dead", but our extractor looks for the actual noun (gun, rifle, etc.). We rely on "shot" triggering the *Attack* type, not the *Weapon* type.
