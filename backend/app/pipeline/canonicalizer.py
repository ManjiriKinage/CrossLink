import re
from typing import Dict, Optional, Set

# Complete entity alias dictionary for canonical resolution
KNOWN_CANONICAL_MAP: Dict[str, str] = {
    # 1995 Downtown Warehouse Case
    "john mehta": "John Mehta",
    "john": "John Mehta",
    "mehta": "John Mehta",
    "mr. mehta": "John Mehta",
    "mr. john mehta": "John Mehta",
    "managing director john mehta": "John Mehta",
    
    "sarah rao": "Sarah Rao",
    "sarah": "Sarah Rao",
    "ms. rao": "Sarah Rao",
    "ms. sarah rao": "Sarah Rao",
    "logistics manager sarah rao": "Sarah Rao",
    
    "inspector kulkarni": "Inspector Kulkarni",
    "kulkarni": "Inspector Kulkarni",
    "investigator kulkarni": "Inspector Kulkarni",
    "officer kulkarni": "Inspector Kulkarni",
    "lead investigator kulkarni": "Inspector Kulkarni",
    
    "vikram joshi": "Vikram Joshi",
    "joshi": "Vikram Joshi",
    "night supervisor vikram joshi": "Vikram Joshi",
    
    "ramesh verma": "Ramesh Verma",
    "verma": "Ramesh Verma",
    "security guard ramesh verma": "Ramesh Verma",
    "guard ramesh verma": "Ramesh Verma",
    
    "dr. h. s. bakshi": "Dr. H. S. Bakshi",
    "dr. h.s. bakshi": "Dr. H. S. Bakshi",
    "dr. bakshi": "Dr. H. S. Bakshi",
    "dr bakshi": "Dr. H. S. Bakshi",
    "bakshi": "Dr. H. S. Bakshi",
    "h. s. bakshi": "Dr. H. S. Bakshi",
    "h.s. bakshi": "Dr. H. S. Bakshi",
    "chief forensic chemist dr. h. s. bakshi": "Dr. H. S. Bakshi",
    
    "downtown warehouse": "Downtown Warehouse",
    "the downtown warehouse": "Downtown Warehouse",
    "warehouse": "Downtown Warehouse",
    "loading bay 3": "Loading Bay 3",
    "bay 3": "Loading Bay 3",
    "loading bay": "Loading Bay 3",
    "nariman point": "Nariman Point",
    "bandra docks": "Bandra Docks",
    "bandra": "Bandra Docks",
    "mumbai": "Mumbai",
    "colaba police station": "Colaba Police Station",
    "colaba": "Colaba Police Station",
    
    "mehta industries": "Mehta Industries",
    "mehta industries ltd.": "Mehta Industries",
    "mehta industries ltd": "Mehta Industries",
    "apex shipping": "Apex Shipping Co.",
    "apex shipping co.": "Apex Shipping Co.",
    "apex shipping co": "Apex Shipping Co.",
    "bombay municipal corporation": "Bombay Municipal Corporation",
    "fire brigade": "Bombay Municipal Corporation",

    "14 june 1995": "14 June 1995",
    "june 14, 1995": "14 June 1995",
    "14th june 1995": "14 June 1995",
    "june 1995": "June 1995",

    # Corporate Fraud Case: BluePeak Consulting / Orion Crest
    "arjun malhotra": "Arjun Malhotra",
    "arjun": "Arjun Malhotra",
    "mr. arjun malhotra": "Arjun Malhotra",
    "mr. malhotra": "Arjun Malhotra",
    "ceo arjun malhotra": "Arjun Malhotra",

    "neha kapoor": "Neha Kapoor",
    "neha": "Neha Kapoor",
    "ms. neha kapoor": "Neha Kapoor",
    "ms. kapoor": "Neha Kapoor",
    "cfo neha kapoor": "Neha Kapoor",

    "vikram shah": "Vikram Shah",
    "mr. vikram shah": "Vikram Shah",
    "director vikram shah": "Vikram Shah",

    "priya nair": "Priya Nair",
    "priya": "Priya Nair",
    "ms. priya nair": "Priya Nair",
    "general counsel priya nair": "Priya Nair",

    "rohan mehta": "Rohan Mehta",
    "rohan": "Rohan Mehta",

    "sameer bedi": "Sameer Bedi",
    "sameer": "Sameer Bedi",
    "mr. sameer bedi": "Sameer Bedi",

    "kavita rao": "Kavita Rao",
    "kavita": "Kavita Rao",
    "auditor kavita rao": "Kavita Rao",

    "bluepeak consulting": "BluePeak Consulting",
    "bluepeak": "BluePeak Consulting",
    "blue peak": "BluePeak Consulting",
    "blue peak consulting": "BluePeak Consulting",
    "bluepeak consulting ltd.": "BluePeak Consulting",

    "meridian retail systems": "Meridian Retail Systems",
    "meridian retail": "Meridian Retail Systems",
    "meridian": "Meridian Retail Systems",

    "orion crest technologies": "Orion Crest Technologies",
    "orion crest": "Orion Crest Technologies",
    "orion crest technologies ltd.": "Orion Crest Technologies",

    "shah ventures": "Shah Ventures",
    "17 lake view road": "17 Lake View Road",
    "lake view road": "17 Lake View Road",
    "andheri east": "Andheri East",
    "mumbai head office": "Mumbai Head Office",
}

TITLE_PREFIXES = [
    r"^mr\.\s+", r"^ms\.\s+", r"^mrs\.\s+", r"^dr\.\s+", r"^dr\s+",
    r"^inspector\s+", r"^investigator\s+", r"^officer\s+", r"^director\s+",
    r"^auditor\s+", r"^ceo\s+", r"^cfo\s+", r"^the\s+", r"^guard\s+",
    r"^supervisor\s+", r"^manager\s+", r"^chief\s+"
]

INVALID_ENTITY_PATTERNS = [
    r"^inr\b", r"^rs\.?\b", r"^₹", r"^\$", r"^\d+([.,]\d+)*$",
    r"^\d+\s*(crore|lakh|million|billion|inr|rs|usd)",
    r"confidential", r"board meeting", r"internal finance", r"preliminary audit",
    r"vendor agreement", r"bank transaction", r"investigation interview",
    r"investigation timeline", r"meeting notes", r"closing memo", r"police report",
    r"witness statement", r"newspaper clipping", r"forensic analysis",
    r"^date\b", r"^time\b", r"^interviewer\b", r"^interviewee\b",
    r"^subject\b", r"^from\b", r"^to\b", r"^regards\b", r"^attendees\b",
    r"^findings\b", r"^note\b", r"^q:\b", r"^a:\b"
]

def is_valid_entity(name: str, entity_type: str) -> bool:
    """Checks if an extracted entity text is a valid real-world entity."""
    if not name or len(name.strip()) < 2:
        return False
    
    cleaned = " ".join(name.replace("\n", " ").split()).strip()
    lower = cleaned.lower()

    if entity_type in ["PERSON", "ORGANIZATION"] and lower in [
        "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
        "first", "second", "third", "fourth", "fifth", "quarter", "annual"
    ]:
        return False

    for pat in INVALID_ENTITY_PATTERNS:
        if re.search(pat, lower):
            return False

    if entity_type == "DATE":
        if any(w in lower for w in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec", "199", "202"]):
            return True
        return len(lower) > 3 and any(char.isdigit() for char in lower)

    alpha_chars = sum(1 for c in cleaned if c.isalpha())
    if alpha_chars < 2:
        return False

    return True

def canonicalize_entity(name: str, entity_type: str) -> str:
    """
    Returns the normalized, canonical form of an extracted entity name.
    Strictly merges aliases into unique canonical identifiers.
    """
    if not name:
        return ""

    # Clean newlines, multiple spaces, quotes, and punctuation
    cleaned = " ".join(name.replace("\n", " ").split()).strip().strip(",.'\"")
    
    # Strip possessives (e.g. "Sarah Rao's" -> "Sarah Rao")
    cleaned = re.sub(r"['’]s$", "", cleaned, flags=re.IGNORECASE).strip()

    # Strip trailing role/header annotations
    cleaned = re.sub(r"\s+(interviewer|interviewee|authorized|attendees|director|cfo|ceo|author|date)\b.*$", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"\s*-\s*(inr|first|second|third|fourth|fifth).*$", "", cleaned, flags=re.IGNORECASE).strip()

    lookup_key = cleaned.lower()
    
    # 1. Direct dictionary check
    if lookup_key in KNOWN_CANONICAL_MAP:
        return KNOWN_CANONICAL_MAP[lookup_key]
        
    # 2. Strip common titles/prefixes and re-check
    stripped = lookup_key
    for prefix in TITLE_PREFIXES:
        stripped = re.sub(prefix, "", stripped, flags=re.IGNORECASE).strip()
        
    if stripped in KNOWN_CANONICAL_MAP:
        return KNOWN_CANONICAL_MAP[stripped]

    # 3. Known domain stems
    if "bakshi" in stripped:
        return "Dr. H. S. Bakshi"
    if "kulkarni" in stripped:
        return "Inspector Kulkarni"
    if "ramesh verma" in stripped or (stripped == "verma" and entity_type == "PERSON"):
        return "Ramesh Verma"
    if "vikram joshi" in stripped or (stripped == "joshi" and entity_type == "PERSON"):
        return "Vikram Joshi"
    if "sarah rao" in stripped:
        return "Sarah Rao"
    if "john mehta" in stripped:
        return "John Mehta"
    if "mehta industries" in stripped:
        return "Mehta Industries"
    if "apex shipping" in stripped:
        return "Apex Shipping Co."
    if "loading bay" in stripped or stripped == "bay 3":
        return "Loading Bay 3"
    if "warehouse" in stripped:
        return "Downtown Warehouse"
    if "bluepeak" in stripped:
        return "BluePeak Consulting"
    if "meridian" in stripped:
        return "Meridian Retail Systems"
    if "orion crest" in stripped:
        return "Orion Crest Technologies"
    if "lake view road" in stripped:
        return "17 Lake View Road"
    if stripped == "andheri east":
        return "Andheri East"
    if stripped == "sameer bedi":
        return "Sameer Bedi"
        
    # 4. Standard Title Case
    if entity_type in ["PERSON", "LOCATION", "ORGANIZATION"]:
        return " ".join(w.capitalize() for w in stripped.split())
        
    return cleaned
