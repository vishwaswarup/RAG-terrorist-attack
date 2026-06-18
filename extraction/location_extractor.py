"""
Location Extractor
==================

Extracts country, state, and city from text using a hybrid approach:
    1. Text scanning for known multi-word regions (e.g. "Jammu and Kashmir").
    2. spaCy NER for candidate GPE (geopolitical entity) entities.
    3. Region configuration lookup for validation.
    4. Country-city mapping for disambiguation.
    5. CITY_TO_STATE for state resolution.

Returns a confidence score based on extraction quality.
"""

import os
import sys
import re
import spacy

# Ensure project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.regions import (
    ACTIVE_COUNTRIES, CITY_TO_COUNTRY_MAP, COUNTRY_SET_LOWER, CITY_TO_STATE
)

# ---------------------------------------------------------------------------
# Load spaCy model
# ---------------------------------------------------------------------------
nlp = spacy.load("en_core_web_sm")

# ---------------------------------------------------------------------------
# Known multi-word regions/states that should NOT be treated as cities
# ---------------------------------------------------------------------------
KNOWN_STATE_NAMES = [
    "Jammu and Kashmir",
    "Khyber Pakhtunkhwa",
    "Balochistan",
    "North West Frontier Province",
    "Azad Kashmir",
    "Gilgit-Baltistan",
    "Federally Administered Tribal Areas",
    "Nangarhar",
    "Helmand",
    "Kandahar",
    "Balkh",
    "Sindh",
    "Punjab",
    "Bihar",
    "Maharashtra",
    "Tamil Nadu",
    "West Bengal",
    "Assam",
    "Karnataka",
    "Telangana",
    "Uttar Pradesh",
    "Rajasthan",
    "Gujarat",
    "Madhya Pradesh",
    "Manipur",
    "Nagaland",
]


def extract_location(text: str) -> dict:
    """
    Extract country, state, city, and a confidence score from text.

    Parameters
    ----------
    text : str
        The raw text to analyse.

    Returns
    -------
    dict with keys:
        country    – the country name (str, "" if not found)
        state      – the state/province name (str, "" if not found)
        city       – the city name (str, "" if not found)
        confidence – extraction confidence score (float, 0.0 to 1.0)
    """

    doc = nlp(text)

    country = ""
    state = ""
    city = ""
    confidence = 0.0

    # --- 0. Pre-scan: detect known multi-word state names in raw text ------
    # This catches "Jammu and Kashmir", "Khyber Pakhtunkhwa" etc.
    # before spaCy splits them into separate GPEs.
    detected_state = ""
    state_component_words = set()  # words to exclude from city matching
    for state_name in KNOWN_STATE_NAMES:
        if state_name.lower() in text.lower():
            detected_state = state_name
            # Mark component words that shouldn't be treated as cities
            for word in state_name.split():
                state_component_words.add(word.lower())
            break

    # --- 1. Collect GPE entities from spaCy --------------------------------
    gpes = []
    seen = set()
    for ent in doc.ents:
        if ent.label_ == "GPE" and ent.text not in seen:
            gpes.append(ent.text)
            seen.add(ent.text)

    non_country_gpes = []

    # --- 2. Check for explicit countries -----------------------------------
    for gpe in gpes:
        if gpe.lower() in COUNTRY_SET_LOWER:
            if not country:
                for active_country in ACTIVE_COUNTRIES:
                    if active_country.lower() == gpe.lower():
                        country = active_country
                        break
        else:
            non_country_gpes.append(gpe)

    # --- 3. Check for cities in our region config --------------------------
    # Filter out GPEs that are just components of a state name
    # (e.g., "Jammu" from "Jammu and Kashmir")
    found_known_city = False
    for gpe in non_country_gpes:
        gpe_lower = gpe.lower()

        # Skip if this GPE is just a component of a detected state name
        if gpe_lower in state_component_words:
            continue

        if gpe_lower in CITY_TO_COUNTRY_MAP:
            city = gpe
            mapped_country = CITY_TO_COUNTRY_MAP[gpe_lower]
            # City-inferred country is more reliable than a country
            # just mentioned in text (e.g., "militants from Pakistan"
            # doesn't mean the incident happened in Pakistan)
            country = mapped_country
            found_known_city = True
            break

    # --- 4. Fallback: text scanning for known cities -----------------------
    # If spaCy didn't find the city as a GPE, scan the text directly.
    if not city:
        text_lower = text.lower()
        # Sort by longest first to avoid partial matches
        for known_city in sorted(CITY_TO_COUNTRY_MAP.keys(), key=len, reverse=True):
            if known_city in state_component_words:
                continue
            # Use word boundary matching to avoid partial matches
            if re.search(r"\b" + re.escape(known_city) + r"\b", text_lower):
                # Find the proper-cased version
                for c_country, c_cities in __import__('config.regions', fromlist=['COUNTRY_TO_CITIES']).COUNTRY_TO_CITIES.items():
                    for c_city in c_cities:
                        if c_city.lower() == known_city:
                            city = c_city
                            if not country:
                                country = c_country
                            found_known_city = True
                            break
                    if city:
                        break
                if city:
                    break

    # --- 5. Heuristic: if no known city found, use first non-state GPE -----
    if not city and non_country_gpes:
        for gpe in non_country_gpes:
            if gpe.lower() not in state_component_words:
                city = gpe
                break

    # --- 6. State resolution -----------------------------------------------
    # Priority: CITY_TO_STATE lookup > detected multi-word state > GPE guess
    if city and city.lower() in CITY_TO_STATE:
        state = CITY_TO_STATE[city.lower()]
    elif detected_state:
        state = detected_state
    else:
        # Fallback: use remaining non-country, non-city GPEs as state guess
        # BUT only if they match a known state name
        state_candidates = [
            g for g in non_country_gpes
            if g != city and g.lower() not in state_component_words
        ]
        for candidate in state_candidates:
            # Only accept if it's a known state name
            if candidate in KNOWN_STATE_NAMES or candidate.lower() in CITY_TO_STATE.values():
                state = candidate
                break
            # Also check if it looks like a real state (appears in our mappings)
            for st in KNOWN_STATE_NAMES:
                if candidate.lower() == st.lower():
                    state = st
                    break
            if state:
                break

    # --- 7. Calculate confidence -------------------------------------------
    if country and found_known_city:
        confidence = 1.0
    elif country and city:
        confidence = 0.8
    elif country:
        confidence = 0.7
    elif city:
        confidence = 0.5
    else:
        confidence = 0.0

    return {
        "country": country,
        "state": state,
        "city": city,
        "confidence": confidence
    }


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    samples = [
        "A bombing attack occurred in Colombo on April 21, 2019.",
        "The attack took place in Mumbai, Maharashtra.",
        "An explosion was reported near Kabul, Afghanistan.",
        "The incident occurred in Paris, France.",
        "A terrorist attack in Pulwama, Jammu and Kashmir.",
        "No location information available.",
        "Militants attacked an Indian Army camp at Nagrota near Jammu city in Jammu and Kashmir.",
        "Militants fired upon a bus on the Anantnag-Srinagar highway in Jammu and Kashmir.",
        "A militant attack on an Indian Air Force base at Pathankot in Punjab, India.",
        "A blast near the town of Uri in Jammu and Kashmir, India.",
        "A suicide bombing outside Hamid Karzai International Airport in Kabul, Afghanistan.",
        "A suicide bomber at Mazar-i-Sharif in Balkh province, Afghanistan.",
    ]

    for s in samples:
        result = extract_location(s)
        print(f"Text: {s}")
        print(f"  Country   : {result['country']!r}")
        print(f"  State     : {result['state']!r}")
        print(f"  City      : {result['city']!r}")
        print(f"  Confidence: {result['confidence']}")
        print()
