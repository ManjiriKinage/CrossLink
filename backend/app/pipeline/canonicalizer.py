"""
canonicalizer.py — Universal Entity Canonicalization & Alias Resolution
========================================================================
Generalized, case-agnostic entity normalizer.
Avoids hardcoding names or case-specific identities, preserving evidentiary fidelity across arbitrary dossiers.
"""

import re
from typing import Dict, List, Optional, Set

# Universal legal and business corporate abbreviations
COMMON_ABBREVIATIONS: Dict[str, str] = {
    "cctv": "CCTV",
    "ltd": "Ltd.",
    "ltd.": "Ltd.",
    "inc": "Inc.",
    "inc.": "Inc.",
    "corp": "Corp.",
    "corp.": "Corp.",
    "co": "Co.",
    "co.": "Co."
}

# Standard professional and honorific prefixes to strip or normalize
TITLE_PREFIX_PATTERN = re.compile(
    r"^(?:mr\.|ms\.|mrs\.|dr\.|dr\b|inspector|investigator|officer|director|curator|auditor|ceo|cfo|guard|supervisor|manager|chief|contractor|technician|the)\s+",
    re.IGNORECASE
)

# Document header/metadata phrases that are NOT entities
INVALID_HEADER_PATTERNS = [
    r"-\s*(?:collection inventory|exhibition movement|security incident|visitor and access|internal email|investigation timeline|incident report|interview summary|closing memo|police report|forensic analysis|preliminary audit|vendor agreement|meeting notes|board meeting|finance report)",
    r"^(?:permanent collection|normal storage|estimated insurance|category:|artifact record:|card id:|case reference:|date range:|scheduled shift|recorded exit|authorized by|security verification|lot \d+ description)",
    r"^(?:inr|rs\.?|₹|\$)\s*\d+",
    r"^\d+\s*(?:crore|lakh|million|billion|inr|rs|usd)",
    r"^(?:confidential|findings:|note:|q:|a:|attendees:|subject:|from:|to:|regards|interviewer:|interviewee:)",
    r"^(?:date|time|hours|minutes|seconds|room|vault|corridor|door|window)$"
]

TRAILING_ANNOTATION_PATTERN = re.compile(
    r"\s*-\s*(?:curator|senior security officer|security guard|logistics manager|director|cfo|ceo|contractor|technician|inr|first|second|third|fourth|fifth|description|authorization|entry|exit).*$",
    re.IGNORECASE
)

TRAILING_PREPOSITION_PATTERN = re.compile(
    r"\s+(?:of|in|at|the|for|and|by|from|to|with)\s*$",
    re.IGNORECASE
)


def is_valid_entity(name: str, entity_type: str) -> bool:
    """Checks if an extracted entity text is a genuine real-world entity rather than document noise."""
    if not name or len(name.strip()) < 2:
        return False

    cleaned = " ".join(name.replace("\n", " ").split()).strip()
    lower = cleaned.lower()

    # Reject days of week / months if misclassified as PERSON/ORG
    if entity_type in ["PERSON", "ORGANIZATION"] and lower in {
        "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
        "january", "february", "march", "april", "june", "july", "august", "september",
        "october", "november", "december", "monday", "tuesday", "wednesday", "thursday",
        "friday", "saturday", "sunday", "first", "second", "third", "quarter", "annual"
    }:
        return False

    for pat in INVALID_HEADER_PATTERNS:
        if re.search(pat, lower):
            return False

    if entity_type == "DATE":
        if any(w in lower for w in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec", "19", "20"]):
            return True
        return len(lower) > 3 and any(char.isdigit() for char in lower)

    # Must contain at least two alphabetic letters
    alpha_chars = sum(1 for c in cleaned if c.isalpha())
    if alpha_chars < 2:
        return False

    return True


def canonicalize_entity(name: str, entity_type: str = "UNKNOWN") -> str:
    """
    Normalizes an entity name into its canonical identifier without case-specific hardcoding.
    Handles formatting, trailing headers/annotations, and title normalization uniformly.
    """
    if not name:
        return ""

    # Clean whitespace, quotes, and punctuation
    cleaned = " ".join(name.replace("\n", " ").split()).strip().strip(",.'\"-")

    # Strip possessives (e.g. "Rohan Mehta's" -> "Rohan Mehta")
    cleaned = re.sub(r"['’]s$", "", cleaned, flags=re.IGNORECASE).strip()

    # Strip professional titles, honorifics, and leading articles (e.g. "The Downtown Warehouse" -> "Downtown Warehouse")
    cleaned = TITLE_PREFIX_PATTERN.sub("", cleaned).strip()

    # Strip trailing role/action annotations (e.g. "Ananya Rao - Curator" -> "Ananya Rao")
    cleaned = TRAILING_ANNOTATION_PATTERN.sub("", cleaned).strip()

    # Strip dangling trailing prepositions (e.g. "Blue Sapphire Of" -> "Blue Sapphire")
    cleaned = TRAILING_PREPOSITION_PATTERN.sub("", cleaned).strip()

    # Normalize universal acronyms if exact match
    lower_key = cleaned.lower()
    if lower_key in COMMON_ABBREVIATIONS:
        return COMMON_ABBREVIATIONS[lower_key]

    # Normalize title case for names/places/organizations
    if entity_type in ["PERSON", "LOCATION", "ORGANIZATION"]:
        # Preserve existing camelCase or uppercase if intentional like CCTV
        words = cleaned.split()
        rebuilt = []
        for w in words:
            w_lower = w.lower()
            if w_lower in COMMON_ABBREVIATIONS:
                rebuilt.append(COMMON_ABBREVIATIONS[w_lower])
            elif w.isupper() and len(w) <= 4:
                rebuilt.append(w)
            elif w_lower in {"of", "the", "in", "and", "de", "van", "von"} and rebuilt:
                rebuilt.append(w_lower)
            else:
                rebuilt.append(w.capitalize())
        return " ".join(rebuilt)

    return cleaned


def resolve_alias_in_case(alias: str, case_entities: List[str]) -> str:
    """
    Dynamically resolves a partial name or alias against entities present in the active case.
    E.g. If alias is 'Rohan' and case entities contain 'Rohan Mehta', resolves to 'Rohan Mehta'.
    Completely dynamic, scoped to the current case, with no global hardcoding.
    """
    if not alias or not case_entities:
        return alias

    alias_clean = canonicalize_entity(alias)
    alias_lower = alias_clean.lower()

    # Exact match check first
    for ent in case_entities:
        if ent.lower() == alias_lower:
            return ent

    # Full name token match (e.g. first name or last name match)
    candidates = []
    for ent in case_entities:
        ent_tokens = [t.lower() for t in ent.split() if len(t) >= 3]
        if alias_lower in ent_tokens:
            candidates.append(ent)
        elif any(t in alias_lower for t in ent_tokens):
            candidates.append(ent)

    # Return unambiguous match
    if len(candidates) == 1:
        return candidates[0]

    return alias_clean
