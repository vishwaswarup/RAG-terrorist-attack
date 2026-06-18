"""
Casualty Extractor
==================

Extracts killed and injured counts from text using regex patterns.

Handles patterns like:
    "269 people were killed"
    "500 were injured"
    "at least 30 dead"
    "more than 100 wounded"
    "killing 45 and injuring 200"
    "left 10 dead and 50 hurt"
    "Seven soldiers were killed"
    "twenty three people died"
"""

import re


# ---------------------------------------------------------------------------
# Number-word conversion
# ---------------------------------------------------------------------------
_ONES = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19,
}
_TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}

_FUZZY = {"dozens": 24, "scores": 40, "several": 3}

# Build a single regex that matches number words (e.g. "forty five", "nineteen", "seven")
_ALL_WORDS = list(_ONES.keys()) + list(_TENS.keys()) + list(_FUZZY.keys())
_ALL_WORDS.sort(key=len, reverse=True)  # match longest first
_WORD_NUM_PATTERN = re.compile(
    r"\b(" + "|".join(_ALL_WORDS) + r")(?:\s*[-\s]\s*(" + "|".join(_ONES.keys()) + r"))?\b",
    re.IGNORECASE
)


def _word_to_number(text: str) -> int | None:
    """
    Convert a number-word string to an integer.
    
    Examples:
        "seven" -> 7
        "forty five" -> 45
        "nineteen" -> 19
    
    Returns None if not a valid number word.
    """
    text = text.strip().lower()
    text = re.sub(r"[-\s]+", " ", text)
    parts = text.split()
    
    if len(parts) == 1:
        if parts[0] in _ONES:
            return _ONES[parts[0]]
        if parts[0] in _TENS:
            return _TENS[parts[0]]
        if parts[0] in _FUZZY:
            return _FUZZY[parts[0]]
        return None
    elif len(parts) == 2:
        tens = _TENS.get(parts[0])
        ones = _ONES.get(parts[1])
        if tens is not None and ones is not None and ones < 10:
            return tens + ones
        return None
    return None


def _replace_word_numbers(text: str) -> str:
    """
    Replace all number-words in text with their digit equivalents.
    This allows the digit-based regex patterns to work on them.
    
    "Seven soldiers were killed" -> "7 soldiers were killed"
    "forty five people dead" -> "45 people dead"
    """
    def replacer(match):
        full = match.group(0)
        val = _word_to_number(full)
        if val is not None:
            return str(val)
        return full
    
    return _WORD_NUM_PATTERN.sub(replacer, text)


# ---------------------------------------------------------------------------
# Regex patterns for KILLED
# Each pattern captures the number as group 1.
# Patterns now use wider gaps (up to 15 words) to bypass long subordinate clauses
# and we use \S+ instead of \w+ to match commas and punctuation.
KILLED_PATTERNS = [
    # "N [up to 15 words, not crossing injury keywords] killed"
    r"(\d+)\s+(?:(?!injured|wounded|hurt|hospitali)\S+\s+){0,15}(?:were\s+)?killed",
    # "killed N people" / "killed N"
    r"killed\s+(\d+)(?:\s+people)?",
    # "killing N people" / "killing N"
    r"killing\s+(\d+)(?:\s+people)?",
    # "N dead" / "N people dead"
    r"(\d+)\s+(?:people\s+)?dead",
    # "N fatalities"
    r"(\d+)\s+fatalities",
    # "N deaths"
    r"(\d+)\s+deaths",
    # "left N dead"
    r"left\s+(\d+)\s+dead",
    # "claimed N lives" / "claimed the lives of N"
    r"claimed\s+(?:the\s+lives\s+of\s+)?(\d+)\s+lives?",
    r"claimed\s+(\d+)\s+lives",
    # "death toll of N" / "death toll rose to N"
    r"death\s+toll\s+(?:of|rose\s+to|reached|stands\s+at)\s+(\d+)",
    # "N [up to 15 words] died"
    r"(\d+)\s+(?:(?!killed|dead|fatalities)\S+\s+){0,15}died",
    # "deaths of N"
    r"deaths\s+of\s+(\d+)",
    # "resulted in the deaths of N"
    r"resulted\s+in\s+the\s+deaths?\s+of\s+(\d+)",
]

# ---------------------------------------------------------------------------
# Regex patterns for INJURED
# ---------------------------------------------------------------------------
INJURED_PATTERNS = [
    # "N [up to 15 words] injured"
    r"(\d+)\s+(?:(?!killed|dead|died|fatalities)\S+\s+){0,15}(?:were\s+)?injured",
    # "injuring N" / "injured N"
    r"injuring\s+(\d+)(?:\s+\w+)?",
    r"injured\s+(\d+)(?:\s+\w+)?",
    # "injured more than N" / "injured at least N others"
    r"injured\s+(?:more\s+than|at\s+least|over|approximately|around|nearly|about)\s+(\d+)",
    # "N [up to 15 words] wounded"
    r"(\d+)\s+(?:(?!killed|dead|died|fatalities)\S+\s+){0,15}(?:were\s+)?wounded",
    # "wounding N"
    r"wounding\s+(\d+)(?:\s+people)?",
    # "N hurt"
    r"(\d+)\s+(?:people\s+)?(?:were\s+)?hurt",
    # "left N injured/wounded/hurt"
    r"left\s+(\d+)\s+(?:injured|wounded|hurt)",
    # "N hospitalized" / "N people were hospitalized"
    r"(\d+)\s+(?:\w+\s+)?(?:were\s+)?hospitali[sz]ed",
]

# ---------------------------------------------------------------------------
# Prefix pattern — handles "at least", "more than", "approximately", etc.
# These appear before the number and should be stripped.
# ---------------------------------------------------------------------------
PREFIX = r"(?:at\s+least|more\s+than|over|approximately|around|nearly|about|up\s+to)?\s*"


def _find_sum_or_max_number(text: str, patterns: list[str]) -> int:
    """
    Search text for all matching patterns.
    If multiple numbers are found, check if they are part of a conjunction
    (e.g., "2 police and 3 civilians were killed"). We can sum them safely if 
    we extract them from the same sentence/context. 
    To be safe and handle "multiple casualty mentions in the same sentence", 
    we will try to sum all unique matches found by the patterns if they are 
    additive. However, a simpler, highly robust approach for this GTD fix:
    Since multiple patterns might capture the same number, we collect all
    (start_idx, end_idx, number) spans. We sum non-overlapping spans.
    """
    spans = []
    for pattern in patterns:
        full_pattern = PREFIX + pattern
        for match in re.finditer(full_pattern, text, re.IGNORECASE):
            try:
                val = int(match.group(1))
                # Only consider non-overlapping matches
                overlap = False
                for s, e, v in spans:
                    if not (match.end() <= s or match.start() >= e):
                        overlap = True
                        break
                if not overlap:
                    spans.append((match.start(), match.end(), val))
            except (IndexError, ValueError):
                continue
    
    total = sum(v for s, e, v in spans)
    return total if total > 0 else 0


def extract_casualties(text: str) -> dict:
    """
    Extract killed and injured counts from text.

    Parameters
    ----------
    text : str
        The raw text to search.

    Returns
    -------
    dict with keys:
        killed  – number of people killed (int, 0 if unknown)
        injured – number of people injured (int, 0 if unknown)
    """
    # First, replace number words with digits so our regex can match them
    normalized_text = _replace_word_numbers(text)
    
    # Handle "hostage fate unknown"
    if re.search(r"hostage fate unknown", text, re.IGNORECASE):
        # GTD treats unknown fate as 0 killed unless specified elsewhere.
        pass

    killed = _find_sum_or_max_number(normalized_text, KILLED_PATTERNS)
    injured = _find_sum_or_max_number(normalized_text, INJURED_PATTERNS)

    # In "X soldiers and Y civilians were wounded", standard regex misses the first noun.
    # Check for "N1 <noun> and N2 <noun> were <verb>"
    def _add_conjunctions(text, verb_pattern):
        # e.g., "8 soldiers and 2 civilians were wounded"
        # Since _find_sum_or_max_number caught 2, we should just add 8.
        # But to prevent double counting, let's just do a specific sum for this sentence structure.
        extra = 0
        pattern = r"(\d+)\s+\S+\s+(?:and|&|,)\s+(\d+)\s+\S+\s+(?:were\s+)?" + verb_pattern
        for m in re.finditer(pattern, text, re.IGNORECASE):
            try:
                # the second number is usually caught by the main patterns, so we just add the first one
                extra += int(m.group(1))
            except ValueError:
                pass
        return extra

    killed += _add_conjunctions(normalized_text, r"(?:killed|dead|died|fatalities)")
    injured += _add_conjunctions(normalized_text, r"(?:injured|wounded|hurt)")

    # The prompt requested "including the attacker". GTD nkill actually INCLUDES the attacker.
    # Therefore, if the text says "5 people killed, including the attacker", the true number is 5.
    # If the text says "In addition to the attacker, 5 people were killed", the true number is 6.
    if re.search(r"in\s+addition\s+to\s+(?:the\s+)?(?:assailant|attacker|bomber|suicide bomber)", normalized_text, re.IGNORECASE):
        killed += 1
    elif re.search(r"besides\s+(?:the\s+)?(?:assailant|attacker|bomber)", normalized_text, re.IGNORECASE):
        killed += 1

    # Also handle "N lone gunman died" etc if killed is 0
    if killed == 0 and re.search(r"(?:assailant|gunman|attacker|bomber).{0,30}died", text, re.IGNORECASE):
        killed += 1

    return {
        "killed": killed,
        "injured": injured,
    }


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    samples = [
        "A bomb exploded killing 45 people and injuring 200.",
        "The attack left 30 dead and 150 wounded.",
        "At least 269 people were killed and more than 500 were injured.",
        "The death toll rose to 12. Over 50 people were hospitalized.",
        "No casualties were reported in the incident.",
        "Seven soldiers were killed and nineteen were injured.",
        "The blast resulted in the deaths of 40 Central Reserve Police Force personnel.",
        "Two CRPF jawans were killed and four others were injured.",
        "At least sixty one cadets were killed and more than one hundred seventeen were injured.",
    ]

    for s in samples:
        result = extract_casualties(s)
        print(f"Text: {s}")
        print(f"  Killed : {result['killed']}")
        print(f"  Injured: {result['injured']}")
        print()
