"""
Date Extractor
==============

Extracts the first recognisable date from text.

Strategy (in priority order):
    1. dateparser — handles natural language dates like
       "April 21, 2019" or "21st of March, 2020".
    2. Regex fallback — catches ISO dates (2019-04-21),
       and common numeric formats (21/04/2019, 04-21-2019).
"""

import re
import dateparser


# ---------------------------------------------------------------------------
# Regex patterns for common date formats (fallback)
# ---------------------------------------------------------------------------
DATE_PATTERNS = [
    # ISO: 2019-04-21
    r"\b(\d{4}-\d{1,2}-\d{1,2})\b",
    # US: 04/21/2019 or 04-21-2019
    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b",
    # UK/EU: 21/04/2019
    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b",
    # Written: "April 21, 2019" / "21 April 2019"
    r"\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|"
    r"August|September|October|November|December)(?:\s+\d{4})?)\b",
    r"\b((?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?)\b",
]


def extract_date(text: str) -> str:
    """
    Extract the first date found in the text.

    Parameters
    ----------
    text : str
        The raw text to search for dates.

    Returns
    -------
    str
        The date in ISO format (YYYY-MM-DD), or "" if none found.
    """

    # --- Strategy 1: dateparser (handles natural language) ------------------
    # We search for date-like substrings using regex first,
    # then parse them with dateparser for accurate interpretation.
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_date = match.group(1)
            parsed = dateparser.parse(raw_date)
            if parsed:
                return parsed.strftime("%Y-%m-%d")

    # --- Strategy 2: Let dateparser scan common phrases --------------------
    # Try to find month names in the text and parse surrounding context.
    month_pattern = (
        r"(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December|"
        r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    )
    # Look for "Month DD, YYYY" or "DD Month YYYY" in a wider window
    context_pattern = (
        r"(?:\d{1,2}\s+)?" + month_pattern +
        r"(?:\s+\d{1,2},?)?\s*\d{4}"
    )
    match = re.search(context_pattern, text, re.IGNORECASE)
    if match:
        parsed = dateparser.parse(match.group(0))
        if parsed:
            return parsed.strftime("%Y-%m-%d")

    # --- Strategy 3: dateparser on the whole text (slow, last resort) ------
    # Only try on shorter texts to avoid false positives.
    if len(text) < 500:
        parsed = dateparser.parse(text)
        if parsed:
            return parsed.strftime("%Y-%m-%d")

    return ""


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    samples = [
        "A bombing attack occurred in Colombo, Sri Lanka on April 21, 2019.",
        "The incident took place on 15 March 2020 in Kabul.",
        "On 2021-09-11, a memorial was held.",
        "The attack happened on 26/11/2008 in Mumbai.",
        "No specific date mentioned in this text.",
    ]

    for s in samples:
        result = extract_date(s)
        print(f"Text: {s}")
        print(f"  Date: {result!r}")
        print()
