import re
from typing import Dict, Optional

# Known entity aliases for cold case investigation
KNOWN_CANONICAL_MAP: Dict[str, str] = {
    # Persons
    "john mehta": "John Mehta",
    "john": "John Mehta",
    "mehta": "John Mehta",
    "mr. mehta": "John Mehta",
    "mr. john mehta": "John Mehta",
    
    "sarah rao": "Sarah Rao",
    "sarah": "Sarah Rao",
    "ms. rao": "Sarah Rao",
    "ms. sarah rao": "Sarah Rao",
    
    "inspector kulkarni": "Inspector Kulkarni",
    "kulkarni": "Inspector Kulkarni",
    "investigator kulkarni": "Inspector Kulkarni",
    
    "vikram joshi": "Vikram Joshi",
    "joshi": "Vikram Joshi",
    
    "ramesh verma": "Ramesh Verma",
    "verma": "Ramesh Verma",
    
    "dr. h. s. bakshi": "Dr. H. S. Bakshi",
    "dr. bakshi": "Dr. H. S. Bakshi",
    "bakshi": "Dr. H. S. Bakshi",
    
    # Locations
    "downtown warehouse": "Downtown Warehouse",
    "the downtown warehouse": "Downtown Warehouse",
    "warehouse": "Downtown Warehouse",
    "loading bay 3": "Loading Bay 3",
    "bay 3": "Loading Bay 3",
    "nariman point": "Nariman Point",
    "bandra docks": "Bandra Docks",
    "bandra": "Bandra Docks",
    "mumbai": "Mumbai",
    "colaba police station": "Colaba Police Station",
    "colaba": "Colaba Police Station",
    
    # Organizations
    "mehta industries": "Mehta Industries",
    "mehta industries ltd.": "Mehta Industries",
    "mehta industries ltd": "Mehta Industries",
    "apex shipping": "Apex Shipping Co.",
    "apex shipping co.": "Apex Shipping Co.",
    "apex shipping co": "Apex Shipping Co.",
    "bombay municipal corporation": "Bombay Municipal Corporation",
    "fire brigade": "Bombay Municipal Corporation",
}

TITLE_PREFIXES = [
    r"^mr\.\s+", r"^ms\.\s+", r"^mrs\.\s+", r"^dr\.\s+",
    r"^inspector\s+", r"^officer\s+", r"^director\s+", r"^the\s+"
]

def canonicalize_entity(name: str, entity_type: str) -> str:
    """
    Returns the normalized, canonical form of an extracted entity name.
    """
    cleaned = name.strip().strip(",.'\"")
    lookup_key = cleaned.lower()
    
    # Check direct canonical dictionary
    if lookup_key in KNOWN_CANONICAL_MAP:
        return KNOWN_CANONICAL_MAP[lookup_key]
        
    # Strip common titles and re-check
    stripped = lookup_key
    for prefix in TITLE_PREFIXES:
        stripped = re.sub(prefix, "", stripped, flags=re.IGNORECASE).strip()
        
    if stripped in KNOWN_CANONICAL_MAP:
        return KNOWN_CANONICAL_MAP[stripped]
        
    # Standard Title Case for Person / Location / Org if not mapped
    if entity_type in ["PERSON", "LOCATION", "ORGANIZATION"]:
        # Capitalize words properly
        return " ".join(w.capitalize() for w in cleaned.split())
        
    return cleaned
