import spacy
from typing import List, Dict, Any
from app.pipeline.canonicalizer import canonicalize_entity
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
    "night", "morning", "afternoon", "evening", "hours", "days", "months"
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
        raw_name = ent.text.strip()
        if len(raw_name) < 2:
            continue
            
        mapped_type = ENTITY_TYPE_MAPPING.get(ent.label_)
        if not mapped_type:
            continue
            
        if raw_name.lower() in STOP_ENTITIES:
            continue
            
        # Clean canonical form
        canonical = canonicalize_entity(raw_name, mapped_type)
        
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
