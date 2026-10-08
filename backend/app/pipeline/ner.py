import spacy
from typing import List, Dict, Any
from app.pipeline.canonicalizer import canonicalize_entity, is_valid_entity
from app.config import settings

_nlp = None

def get_nlp():
    """
    Lazy loads and returns the spaCy model.
    """
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load(settings.SPACY_MODEL)
        except OSError:
            # If model not found locally, download it
            from spacy.cli import download
            download(settings.SPACY_MODEL)
            _nlp = spacy.load(settings.SPACY_MODEL)
    return _nlp

ENTITY_TYPE_MAPPING = {
    "PERSON": "PERSON",
    "GPE": "LOCATION",
    "LOC": "LOCATION",
    "FAC": "LOCATION",
    "ORG": "ORGANIZATION",
    "DATE": "DATE",
    "TIME": "DATE"
}

# Words to discard if extracted mistakenly
STOP_ENTITIES = {
    "the", "a", "an", "this", "that", "it", "today", "yesterday", "tomorrow",
    "night", "morning", "afternoon", "evening", "hours", "days", "months",
    "inr", "rs", "usd", "cfo", "ceo", "director", "general counsel", "auditor",
    "date", "time", "interviewer", "interviewee", "subject", "from", "to", "regards"
}

KNOWN_TYPE_CORRECTIONS = {
    "Sameer Bedi": "PERSON",
    "Vikram Shah": "PERSON",
    "Neha Kapoor": "PERSON",
    "Arjun Malhotra": "PERSON",
    "Priya Nair": "PERSON",
    "Rohan Mehta": "PERSON",
    "Kavita Rao": "PERSON",
    "Sarah Rao": "PERSON",
    "John Mehta": "PERSON",
    "Andheri East": "LOCATION",
    "17 Lake View Road": "LOCATION",
    "Mumbai Head Office": "LOCATION",
    "Mumbai": "LOCATION",
    "Downtown Warehouse": "LOCATION",
    "Loading Bay 3": "LOCATION",
    "Nariman Point": "LOCATION",
    "Bandra Docks": "LOCATION",
    "Colaba Police Station": "LOCATION",
    "BluePeak Consulting": "ORGANIZATION",
    "Meridian Retail Systems": "ORGANIZATION",
    "Orion Crest Technologies": "ORGANIZATION",
    "Shah Ventures": "ORGANIZATION",
    "Mehta Industries": "ORGANIZATION",
    "Apex Shipping Co.": "ORGANIZATION",
    "Bombay Municipal Corporation": "ORGANIZATION"
}

def extract_entities(text: str) -> List[Dict[str, Any]]:
    """
    Extracts, normalizes, and filters named entities from text using spaCy.
    """
    if not text:
        return []
        
    nlp = get_nlp()
    doc = nlp(text)
    
    entities = []
    seen = set()
    
    for ent in doc.ents:
        raw_name = " ".join(ent.text.replace("\n", " ").split()).strip()
        if len(raw_name) < 2:
            continue
            
        mapped_type = ENTITY_TYPE_MAPPING.get(ent.label_)
        if not mapped_type:
            continue
            
        if raw_name.lower() in STOP_ENTITIES:
            continue

        if not is_valid_entity(raw_name, mapped_type):
            continue
            
        # Clean canonical form
        canonical = canonicalize_entity(raw_name, mapped_type)
        if not is_valid_entity(canonical, mapped_type):
            continue

        # Check known type overrides
        if canonical in KNOWN_TYPE_CORRECTIONS:
            mapped_type = KNOWN_TYPE_CORRECTIONS[canonical]
        
        # Deduplicate per chunk
        unique_key = (canonical, mapped_type)
        if unique_key in seen:
            continue
        seen.add(unique_key)
        
        entities.append({
            "name": raw_name,
            "canonical_name": canonical,
            "type": mapped_type,
            "start_char": ent.start_char,
            "end_char": ent.end_char
        })
        
    return entities
